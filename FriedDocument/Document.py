# -*- coding: iso-8859-1 -*
#############################################################################
#
# Copyright (c) 2004-2006 Fry-IT Ltd. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

# python
import re, sys, os, urllib, string
import copy
opj = os.path.join
from pprint import pprint
from cgi import escape
import time
from sets import Set
import logging
logger = logging.getLogger('FriedDocument')

# Zope
from Products.ZCatalog.CatalogAwareness import CatalogAware
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.Permission import Permission
from DocumentTemplate import sequence
from Globals import Persistent, InitializeClass, package_home, DTMLFile
from OFS import Folder, SimpleItem
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface
from Acquisition import aq_inner, aq_parent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.PageTemplate import PTRuntimeError
from OFS.OrderedFolder import OrderedFolder

try:
    from Products.ExternalEditor import ExternalEditor
    _has_ExternalEditor = 1
except ImportError:
    _has_ExternalEditor = 0

from Products import ZTinyMCE
try:
    version_txt_file = opj(INSTANCE_HOME, 'Products', 'ZTinyMCE','version.txt')
    __ztinymce_version__ = open(version_txt_file).read()
    __, major, minor = [int(x) for x in __ztinymce_version__.split('.')]
except:
    __ztinymce_version__ = "unknown"
    
if major < 2:
    LOG("FriedDocument", WARNING, "Upgrade to ZTinyMCE version 0.2.x")
    
from Products.FriedZopeBase.Bases import HomepageOrderedBaseCatalogAware as _Base
from Products.FriedZopeBase.Utils import niceboolean, internationalizeID, anyTrue
from Products.FriedZopeBase.Utils import debug as fried_debug

try:
    import lxml.html.diff as lxml_html_diff
except ImportError:
    lxml_html_diff = None

    
from Debugger import DebuggerBase    
import Utils
from Constants import *

# Use DEBUG from Constants to wrap fried_debug
def debug(*a, **k):
    if k.get('f') or DEBUG:
        fried_debug(*a, **k)

try:
    from beautifyhtml import beautifyhtml
except ImportError:
    LOG("FriedDocument", WARNING, "BeautifySoup not installed")
    beautifyhtml = None


#----------------------------------------------------------------------------
# Misc stuff

class DeprecatedError(Exception):
    pass

class RevisionError(Exception):
    pass

class NotFileError(Exception):
    pass


ss = lambda x: x.strip().lower()

try:
    v=open('version.txt').read().strip()
    __home__ = '.'
except:
    v=open(opj(package_home(globals()), 'version.txt')
                ).read().strip()
    __home__ = package_home(globals())
    
__version__=v

def format_timestamp(timestamp):
    today_fmt = 'Today %H:%M:%S'
    other_fmt = '%b %d %H:%M'
    now = time.time()
    cnow = time.gmtime(now)
    c = time.gmtime(timestamp)
    if c[0]==cnow[0] and c[1]==cnow[1] and c[2]==cnow[2]:
        # it's today
        return time.strftime(today_fmt, c)
    else:
        return time.strftime(other_fmt, c)

#----------------------------------------------------------------------------
# Error classes

class NoMetalmacroError(Exception):
    def __init__(self, args=None):
        self.args = args
        
class UnusableSlotError(Exception):
    def __init__(self, args=None):
        self.args = args
        
class NousableSlotsError(Exception):
    def __init__(self, args=None):
        self.args = args

class SlotKeyError(Exception):
    pass

class SubmitError(Exception):
    pass

class UtilityImportError(ImportError):
    pass

#----------------------------------------------------------------------------
# Functions


def _findOtherDocuments(root, meta_type=META_TYPE, search_sub=True):
    """ return a list of document objects """
    here = []
    for obj in root.objectValues():
        if obj.meta_type == meta_type:
            here.append(obj)
        elif search_sub and obj.isPrincipiaFolderish:
            here.extend(_findOtherDocuments(obj, meta_type=meta_type, 
                                            search_sub=search_sub))
    return here
            

def manage_findBeLikeDocuments(self, howmany=5):
    """ return a list of dict of documents that we could mimic.
    This is selected by most recently used. """

    try:
        parent = aq_parent(aq_inner(self))
    except:
        parent = self

    # first look closely
    documents = _findOtherDocuments(parent)
    
    if hasattr(self, 'getRoot'):
        # then, if possible look in the root and up
        parent = self.getRoot()
        for document in _findOtherDocuments(parent):
            if document not in documents:
                documents.append(document)

    all = []
    for object in documents:
        path = '/'.join(object.getPhysicalPath())
        d = {'path':path, 
             'mod_time':int(object.bobobase_modification_time()),
             'object':object,
             'title_or_id':object.title_or_id(),
             }
        all.append(d)

    all = sequence.sort(all, (('mod_time',),))
    all.reverse()
    all = all[:howmany]
    return all

def manage_findMetalPTs(self, *args, **kw):
    """ return a list of unique Page Template that might be used as 
    metal macro headers&footers. """
    self = self.Destination()
    
    suggestion_object_paths = []
    
    # 1. Adjacent fellow FriedDocuments
    docs_here = []
    for o in self.objectValues():
        if o.meta_type == META_TYPE:
            docs_here.append(o)
        elif o.isPrincipiaFolderish:
            docs_here.extend(o.objectValues(META_TYPE))
    docs_below = self.superValues(META_TYPE)
    docs_about = Utils.uniqify(docs_here + docs_below)
    
    for each in docs_about:
        objid = each.getMetalObjectId()
        if objid not in suggestion_object_paths:
            suggestion_object_paths.append(objid)
    
    # 2. Look for page templates
    pts_here = self.objectValues('Page Template')
    pts_below = self.superValues('Page Template')
    pts_about = Utils.uniqify(list(pts_here) + list(pts_below))
    
    for pts in pts_about:
        try:
            if pts.pt_macros().keys():
                suggestion_object_paths.append(pts.getId())
        except PTRuntimeError:
            LOG("FriedDocument", WARNING, 
                "METAL macros can't be extracted from %s" % pts)
            
    return Utils.uniqify(suggestion_object_paths)


def manage_findCSSUrlAlts(self, *args, **kw):
    """ return a list of urls that can be used for the WYSIWYG CSS.
    Look for a globally set variable called 'fried_css_url', 
    look in near by fellow FriedDocuments. """
    alts = []
    alts_simple_list = []
    
    # 1. Global variable called 'fried_css_url'
    if hasattr(self, 'fried_css_url'):
        if getattr(self, 'fried_css_url'):
            cssurl = getattr(self, 'fried_css_url')
            if cssurl:
                alts.append({'url':cssurl,
                             'reason':"'fried_css_url' property"})
                alts_simple_list.append(cssurl)
                         
    # 2. Fellow FriedDocument objects
    docs_here = []
    for o in self.objectValues():
        if o.meta_type == META_TYPE:
            docs_here.append(o)
        elif o.isPrincipiaFolderish:
            docs_here.extend(o.objectValues(META_TYPE))
    docs_below = self.superValues(META_TYPE)
    docs_about = Utils.uniqify(docs_here + docs_below)
    
    for each in docs_about:
        css_url = each.getCSSURL()
        if css_url not in alts_simple_list:
            _relurl = each.absolute_url().replace(self.absolute_url(),'')
            if css_url:
                alts.append({'url':css_url,
                             'reason':"Found in %s"%_relurl})
                alts_simple_list.append(css_url)
            
    # 3. Look for suspicious DTML Document and DTML Methods
    for dtmlish in self.superValues(['DTML Document','DTML Method']):
        id = dtmlish.getId()
        if id.lower().endswith('_css') or id.lower().endswith('.css'):
            css_url = dtmlish.absolute_url().replace(self.REQUEST.BASE0,'')
            if css_url not in alts_simple_list:
                alts.append({'url':css_url,
                             'reason':"%s at %s"%(dtmlish.meta_type, css_url)})
                alts_simple_list.append(css_url)
            
    del alts_simple_list
    return alts


    
def cookDocumentId(title):
    title = title.strip()
    id = internationalizeID(title)
    id = id.replace('  ',' ').replace(' ','-').replace('&','and')
    transtab = string.maketrans('/ ','_ ')
    id = string.translate(id, transtab, '?&!;<=>*#[]{}')
    return id
    
def manage_suggestIdFromTitle(dispatcher, title):
    """ transform the title to something that can be a Zope ID """
    return cookDocumentId(title)
    
manage_addFriedDocumentForm = DTMLFile('dtml/add_document', globals())

def manage_addFriedDocument(dispatcher, id, title, metalmacro=None, 
                            slots=[], css_url='', belike_path=None,
                            show_in_nav=False,
                            REQUEST=None):
    """ add a new Fried Document object """
        
    if not metalmacro and slots:
        raise NoMetalmacroError, "...but slots defined"
    
    dest = dispatcher.Destination()
    
    metalmacro_orig = metalmacro
    
    if isinstance(metalmacro, str):
        if metalmacro.startswith('here/'):
            metalmacro.replace('here/','')
            
        if metalmacro.count('/') > 0:
            metalmacro = dest.restrictedTraverse(metalmacro)
        else:
            try:
                metalmacro = getattr(dest, metalmacro)
            except AttributeError:
                raise AttributeError, \
                "metalmacro %r could not be found in Zope" % metalmacro
                
    if isinstance(slots, str):
        slots = [slots]
        
    
    if hasattr(metalmacro, 'meta_type') and metalmacro.meta_type == 'Page Template':
        pass
    elif metalmacro.__class__.__name__ in ('PageTemplateFile', 'CTPageTemplateFile'):
        pass
    elif callable(metalmacro):
        pass
    else:
        raise AssertionError, "metalmacro object must be Page Template"
            
    macroname, usable_slots = _findMetalslots(metalmacro)
    if hasattr(metalmacro, 'getId'):
        metalobjectid = metalmacro.getId()
    else:
        metalobjectid = metalmacro_orig
    
    for slot in slots:
        if slot not in usable_slots:
            raise UnusableSlotError, slot
    if not slots and usable_slots:
        slots = usable_slots
        
    id = id.strip()
    title = title.strip()
    if id == "":
        id = cookDocumentId(title)

    inst = FriedDocument(id, title, metalobjectid, macroname, slots, css_url, 
                         show_in_nav=bool(show_in_nav))
    dest._setObject(id, inst)
    self = dest._getOb(id)

    if belike_path:
        
        belike_object = dispatcher.restrictedTraverse(belike_path)
        assert belike_object.meta_type == META_TYPE, \
        "blike_object %s meta type is not a document (path=%r)" % (belike_object, belike_path)
        self._beLike(belike_object)
    
    if REQUEST is not None:
        redirect = REQUEST.RESPONSE.redirect
        if REQUEST.has_key('addandgoto'):
            url = self.absolute_url()
            url += '/manage_Basic'
        else:
            url = REQUEST.URL1+'/manage_main'
        redirect(url)
    else:
        return self
    
   
def _findMetalslots(metalmacro):
    
    if hasattr(metalmacro, 'macros'):
        _macros = metalmacro.macros

        if not _macros:
            raise NousableSlotsError, "No slots found that we can use"
        elif len(_macros.keys()) > 1:
            raise MultipleMacrosError, "Only one macro supported"
    
        # find the slots!
        key1 = _macros.keys()[0]
        value = _macros[key1]
        
    elif callable(metalmacro):
        value = metalmacro()
        key1 = ""
        
    slots = _find_metalslots(value)

    return key1, slots


def _find_metalslots(iterable):
    """ dig deep inside the list of nested tuples """
    all = []
    islist = lambda x: isinstance(x, (tuple, list))
    for item in iterable:
        if item and islist(item) and item[0]== 'defineSlot':
            all.append(item[1][0])
        elif item and islist(item) and 'metal:define-slot' in item:
            slotname = _find_metalslots_dig_deeper(item)
            if slotname:
                all.append(slotname)
        elif islist(item):
            all.extend(_find_metalslots(item))
            
    return all            

def _find_metalslots_dig_deeper(item):
    """ try to figure out what the slotname really is if anything """
    for c in range(len(item)):
        if item[c]=='metal:define-slot':
            try:
                return item[c+1]
            except IndexError:
                return None
    return None


def unicodify(i, encoding='utf-8'):
    if type(i) == unicode:
        return i
    else:
        return unicode(str(i), encoding)
    
def lazy_unicodify(s, encoding='utf-8'):
    """ combine various uses of unicodify() and ms_character_cleanup() """
    try:
        return unicodify(s, encoding)
    except UnicodeDecodeError:
        s = ms_character_cleanup(s)
        try:
            return unicodify(s, encoding)
        except UnicodeDecodeError:
            # perhaps it has unicode characters in an encoding
            # different from the original one
            if encoding.lower() in ('utf-8','utf8'):
                return unicodify(s, 'latin1')
            else:
                return unicodify(s, 'utf-8')
    
def ms_character_cleanup(s):
    MS_CHARS = { '\x80' : 'euro',
                 '\x82' : 'sbquo',
                 '\x83' : 'fnof', 
                 '\x84' : 'bdquo', 
                 '\x85' : 'hellip',
                 '\x86' : 'dagger',
                 '\x87' : 'Dagger',
                 '\x88' : 'circ', 
                 '\x89' : 'permil',
                 '\x8A' : 'Scaron',
                 '\x8B' : 'lsaquo',
                 '\x8C' : 'OElig',
                 '\x8E' : '#x17D',
                 '\x91' : 'lsquo',
                 '\x92' : 'rsquo',
                 '\x93' : 'ldquo',
                 '\x94' : 'rdquo',
                 '\x95' : 'bull', 
                 '\x96' : 'ndash', 
                 '\x97' : 'mdash', 
                 '\x98' : 'tilde', 
                 '\x99' : 'trade', 
                 '\x9a' : 'scaron',
                 '\x9b' : 'rsaquo',
                 '\x9c' : 'oelig',
                 '\x9e' : '#x17E',
                 '\x9f' : 'Yuml',
                 }
    for key, value in MS_CHARS.items():
        s = s.replace(key, '&%s;' % value)
    return s

def _dict_constructor(key, format='html', raw=u'', rendered=u'',
                     wysiwyg=True, editable=True):
    return {key: PersistentList([
                   {'format':format,
                    'raw':raw,
                    'rendered':rendered,
                    'editable':editable,
                    'wysiwyg':wysiwyg,
                    'revision_timestamp':time.time(),
                    }
                  ])
                }
                                                                             
def _equal_revisions(revision1, revision2):
    """ Compare the user-interesting stuff """

    try:
        if revision1['raw'] != revision2['raw']:
            return False
    except UnicodeDecodeError:
        # will be the case if you compare a unicode string to a 
        # u"sålt" != "sålt"
        # This can happen if either part is of type str and the 
        # other is a healthy unicode object 
        if unicodify(revision1['raw'],'iso-8859-1') != unicodify(revision2['raw'], 'iso-8859-1'):
            return False
        
    if revision1['format'] != revision2['format']:
        return False
    
    return True
        

def _exactly_equal_revisions(revision1, revision2):
    """ Compare everything """
    for k, v in revision1.items():
        if not revision2.has_key(k):
            return False
        if v != revision2[k]:
            return False
    for k, v in revision2.items():
        if not revision1.has_key(k):
            return False
        if v != revision1[k]:
            return False        
    
    return True
    
#----------------------------------------------------------------------------


class FriedDocument(_Base, DebuggerBase):
    """ Folderish object that contains text for rendering with a 
    METAL document. Support editing with ZTinyMCE. 
    """
    __implements__ = (WriteLockInterface,)
    
    __ztinymce_installed_version = __ztinymce_version__
    
    isPrincipiaFolderish=1
    
    has_ExternalEditor = _has_ExternalEditor
    
    meta_type = META_TYPE
    
    META_TYPE = META_TYPE # so that this variable is reachable from templates
    
    _default_slot_format = 'html'
    
    _properties=({'id':'title',         'type': 'ustring','mode':'w'},
                 {'id':'css_url',       'type': 'string', 'mode':'w'},
                 {'id':'metalobjectid', 'type': 'string', 'mode':'w'},
                 {'id':'macroname',     'type': 'string', 'mode':'r'},
                 {'id':'ztinymce_configuration', 'type':'string', 'mode':'w'},
                 {'id':'version',       'type': 'float',  'mode':'w'},
                 {'id':'creation_date', 'type': 'date',   'mode':'r'},
                 {'id':'in_versioning', 'type': 'boolean','mode':'r'},
                 )
    
    # legacy 
    ztinymce_configuration = ''
    
    security=ClassSecurityInfo()

    def __init__(self, id, title, metalobjectid=None, macroname=None,
                 slots=[], css_url='', show_in_nav=False, language='en'):
        """ FriedDocument init 
        
        == Slots ==
        
        Class attribute variable '_texts' is a dict...
        ...where each key is the name the slot.
        The value part of each such dict is another list[1]. Each item represents
        a revision. Each item in this list is a dict which contains these keys:
          * revision_timestamp (a time.time() timestamp)
          * raw (the editable raw content)
          * rendered (raw + format + misc tidying)
          * format (html, css, javascript, etc.)
          * editable (boolean; used for the /editable page)
          * wysiwyg (boolean; used for deciding on plain <textarea or javascript WYSIWYG.
          
        The variable can look something like this:
            
            _texts = {
                 'body':[
                 
                         {'revision_timestamp':12345678.0,
                          'raw':'hello\n',
                          'rendered':'hello<br />',
                          'format':'html',
                          'editable':True,
                          'wysiwyg':True},
                          
                        {'revision_timestamp':12345677.0,
                          'raw':'hell\n',
                          'rendered':'hell<br />',
                          'format':'html',
                          'editable':True,
                          'wysiwyg':True},
                        ],
                          
                 'extracss':[
                         {'revision_timestamp':12345678.0,
                          'raw':'body{font-family:Arial};\n',
                          'rendered':'body{font-family:Arial};\n',
                          'format':'css',
                          'editable':True,
                          'wysiwyg':False},

                         {'revision_timestamp':12345677.0,
                          'raw':'body{};\n',
                          'rendered':'body{};\n',
                          'format':'css',
                          'editable':True,
                          'wysiwyg':False},
                 ],
            }
                      
          
        The sort order is maintained by another class attribute variable called
        _slots_order. Unless you explicitely specify a order or if you for some reason
        have to repair the document, you can always reset the _slots_order by doing
        this: self._slots_order = self._texts.keys(). Get the idea?
        
        When you make a save on a slot (eg. 'body') we insert the latest change
        at the 1st place in the list and append a 'revision_timestamp' timestamp
        to it.
        
        [1] - It used to be different until the revision feature was implemented.
        Every time of the slots used to be a dict. In newer versions it's a sorted
        list of dicts.
        
        == METAL ==
        
        Every FriedDocument is assumed to be working with a Page Template of 
        some sort that defines a METAL macro. In the FriedDocument we need to 
        know the name of the object that contains the macro definition and 
        the macro that it defines. Fried Documents support that the metal object
        is a string that defines the name of a function eg. 'getHeader'.

        """
        self.id = id
        self.title = unicodify(title)
        self.metalobjectid = metalobjectid
        self.macroname = macroname
        self._slots_order = Utils.uniqify(slots)
        _texts = PersistentMapping()
        
        # where we keep the versioning data
        self._texts_versioning = PersistentMapping()

        map(_texts.update, map(_dict_constructor, slots))
        
        self._texts = _texts
        self.version = 0.1
        self.creation_date = DateTime()
        self.css_url = css_url
        self.show_in_nav = bool(show_in_nav)
        self.language = language
        self.in_versioning = False
        
        self._is_cooked = False
        
        self.expiry_hours = 0
        
        self.ztinymce_configuration = ''
    
    # legacy
    _is_cooked = True
    expiry_hours = 0
    in_versioning = False
    
    def inVersioning(self):
        """ return if in versioning """
        return self.in_versioning
    
    def hasUnpublishedChanges(self):
        """ return true if there are unpublished changes. The document has to be
        in versioning to begin with. """
        if self.inVersioning():
            # compare latest slot changes
            slot = self.manage_getSlots()[0]
            in_plain = self._getTexts(ignore_versioning=True)[slot][0]
            in_versioning = self._getTexts()[slot][0]
            if in_plain['raw'] != in_versioning['raw']:
                return True
        return False
    
    def countUnpublishedChanges(self):
        """ return how many changes have been made in the versioning channel """
        assert self.inVersioning(), "Document not in versioning mode"
        slot = self.manage_getSlots()[0]
        in_versioning = self._getTexts()[slot]
        # the reason for the "-1" is that setting up the versioning channel
        # becomes one item but that that's not a *change* which is what this
        # method name promises to deliver
        return len(in_versioning) - 1
            
    
    def isEditable(self):
        """ true if any of the slots is editable """
        for revisions in self._getTexts().values():
            if isinstance(revisions, dict):
                # old style
                textdict = revisions
            else:
                textdict = revisions[0]
            
            if textdict.get('editable'):
                return True
            
        return False
    
    def showInNav(self):
        """ return 'show_in_nav' """
        # because this feature was introduced much later,
        # objects that don't have the attribute have never been created
        # with the chance to set this to true, therefore if the attribute
        # doesn't exist, assume true.
        default = True
        return getattr(self, 'show_in_nav', default)
        
        
    def manage_options(self):
        interals = [{'label':'Basic',    'action':'manage_Basic'},
                    {'label':'Options', 'action':'manage_Options'},
                    #{'label':'Library',  'action':'manage_Library'},
                    ]
        externals = list(Folder.Folder.manage_options[1:6])
        all = []
        all.append({'label':'Contents', 'action':'manage_main'})
        all.extend(interals+externals)
        return tuple(all)
        
    def manage_afterAdd(self, item, container):
        """ zope calls this method after the object has been created.
        All we need to do here is to cook the document. """
        self._cook()
        
    def manage_Update(self, REQUEST=None):
        """ refresh and update this document """
        new_slots = self._findMetalSlots()
        self.reindex_object()
        self._cook()
        self._convert_oldstyle_slots()
        
        if REQUEST is not None:
            return self.manage_Options(self, REQUEST, 
                manage_tabs_message="Document updated")
            
        
    def hasAdditionalProperties(self):
        """ return true if this document has more than the default number of properties """
        return len(self.propertyIds()) > len(FriedDocument._properties)
    
    
    def hasTinyMCEConfiguration(self):
        """ return true if we have a TinyMCE Configuration nearby """
        return self.getTinyMCEConfiguration() is not None
    
    def getTinyMCEConfigurations(self):
        """ return all TinyMCE configuration objects we can find """
        all = self.objectValues('ZTinyMCE Configuration')
        if all:
            return all

        parent = aq_parent(aq_inner(self))
        all = []
        while parent != self:
            all.extend(parent.objectValues('ZTinyMCE Configuration'))
            parent = aq_parent(aq_inner(parent))
            if not hasattr(parent, 'meta_type'):
                break
        return all
        
    def getTinyMCEConfiguration(self):
        """ return true if we have a TinyMCE Configuration nearby """
        if hasattr(self, self.ztinymce_configuration):
            return getattr(self, self.ztinymce_configuration)
        
        all = self.objectValues('ZTinyMCE Configuration')
        if all:
            self._saveTinyMCEConfigurationChoice(all[0].getId())
            return all[0]
    
        parent = aq_parent(aq_inner(self))
        while parent != self:
            all.extend(parent.objectValues('ZTinyMCE Configuration'))
            if all:
                self._saveTinyMCEConfigurationChoice(all[0].getId())
                return all[0]
            parent = aq_parent(aq_inner(parent))
            if not hasattr(parent, 'meta_type'):
                break
            
        return None
    
    def _saveTinyMCEConfigurationChoice(self, objectid):
        """ save that this is the ZTinyMCE Configuration we want to use. """
        self.ztinymce_configuration = objectid
        
    def getCurrentTinyMCEConfiguration(self):
        """ return the current configuration if any """
        return getattr(self, 'ztinymce_configuration', None)
    
    def manage_setTinyMCEConfiguration(self, id, REQUEST=None):
        """ set that this is the id of the configuration they want to use """
        all_configs = self.getTinyMCEConfigurations()
        all_config_ids = [x.getId() for x in all_configs]
        assert id in all_config_ids, "Unrecognized id %r" % id
        
        self._saveTinyMCEConfigurationChoice(id)
        
        if REQUEST is not None:
            return self.manage_Options(self, REQUEST, 
                manage_tabs_message="Document updated")
        
    
    def isZTinyMCEInstalled(self):
        """ return true if ZTinyMCE is installed """
        return not not self.__ztinymce_installed_version
    
   
    security.declareProtected(MANAGE_DOCUMENT, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests 
        for ExternalEditor """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        
        if not REQUEST.get('BODY'):
            get_transaction.abort()
            RESPONSE.setStatus(405)
        else:
            body = REQUEST.get('BODY')
            slot = self.manage_getSlots()[0]
            
            try:
                body = self._strip_doctypehtml(body)
            except:
                LOG("FriedDocument.slotbodyrender", ERROR, "", error=sys.exc_info())
            try:
                self.manage_saveSlot(slot, raw=body)
            except:
                LOG("FriedDocument", ERROR, "", error=sys.exc_info())
            # NOTE: we can't call self._cook() here because the 
            # inherited objects within are also locked by the WebDAV
            # locking thing.
            self._is_cooked = False
            RESPONSE.setStatus(204)
            return RESPONSE
        
        

    def _strip_doctypehtml(self, html):
        """ strip everything above <body> and everything below </body> """
        pos = re.compile('<body.*?>', re.I|re.S).search(html)
        html = html[pos.end():]

        pos = re.compile('</body>', re.I).search(html)
        if pos is None:
            return html
        html = html[:pos.start()]
        return html
        
    
    security.declareProtected(MANAGE_DOCUMENT, 'EditableBody')
    def EditableBody(self):
        """Get source for download
        for ExternalEditor """
        
        allslots = self.manage_getSlots()

        if self.REQUEST.get('slot') and self.REQUEST.get('slot') in allslots:
            slot = self.REQUEST.get('slot')
            self.manage_changeFirstslot(slot)
        else:
            slot = allslots[0]
            
        slotinfo = self._getSlotInfo(slot)
        if slotinfo['format']=='html':
            return self._doctype_html_wrap(self.getText(slot))
        else:
            return self.getText(slot)

        
    def _doctype_html_wrap(self, html):
        """ wrap a chunk of HTML in a XHTML Transitional header and footer """
        head = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '''
        head += '''"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'''
        head += '<html xmlns="http://www.w3.org/1999/xhtml"\n      '\
                'xmlns:tal="http://xml.zope.org/namespaces/tal">\n'
        if self.getCSSURL():
            head += '<link rel="stylesheet" type="text/css" href="%s" />\n' % self.getCSSURL(absolute=True)
        head += '<body>\n'
        #head += "<!-- {slotbody} Everything above and including this line will be discard when saved  -->\n"
        
        #foot = "\n<!-- {/slotbody} Everything below and including this line will be discarded when saved -->\n"
        foot = "</body>\n</html>"
        
        return "%s\n%s\n%s" % (head, html, foot)
        
    
    def content_type(self):
        """ return the content-type so that ExternalEditor knows what it needs to use
        for the extension. """
        slot = self.manage_getSlots()[0]
        slotinfo = self._getSlotInfo(slot)
        format = slotinfo['format']
        if format == 'html':
            return "text/html"
        elif format == 'css':
            return "text/css"
        elif format == 'javascript':
            return "text/javascript"
        elif format == 'xml':
            return "text/xml"
        else:
            return "text/plain"
    
    def get_size(self):
        """ Used for FTP and ZMI (possibly) """
        return len(self.EditableBody())
        

    
    security.declareProtected('View', 'searchable_text')
    def searchable_text(self):
        """ instead of a class instance attribute for the ZCatalog
        to work on we use this. It's a class method that returns all the text 
        of all slots' raw text without any HTML tags. """
        encoding = self.getUnicodeEncoding()
        any_tag_regex = re.compile(r"<.*?>", re.M|re.DOTALL)
        texts = []
        for revisions in self._getTexts().values():
            if isinstance(revisions, dict):
                # old style
                textdict = revisions
            else:
                textdict = revisions[0]
                
            # check if this slot is explicitly set to disallow indexing
            if not textdict.get('no_indexing'):
                raw = textdict.get('raw',u'')
                if isinstance(raw, unicode):
                    texts.append(raw)
                else:
                    try:
                        texts.append(unicodify(raw, encoding))
                    except UnicodeDecodeError:
                        try:
                            # try the other encoding
                            if encoding == 'utf8':
                                texts.append(unicodify(raw, 'latin1'))
                            else:
                                texts.append(unicodify(raw, 'utf8'))
                        except UnicodeDecodeError:
                            texts.append(unicodify(raw, encoding, 'replace'))
                
        text = u'\n'.join(texts)
        text = any_tag_regex.sub(u"", text)
        return text

    security.declareProtected('View', 'searchable_text_ascii')
    def searchable_text_ascii(self):
        """ return the value of searchable_text() ASCII encoded """
        return internationalizeID(self.searchable_text())
    
    def index_object(self):
        """A common method to allow Findables to index themselves."""
        try:
            catalog = self.getCatalog()
        except AttributeError:
            try:
                catalog = self.Catalog
            except AttributeError:
                return
        
        path = '/'.join(self.getPhysicalPath())
        
        indexes = catalog._catalog.indexes
        idxs = []
        for idx in ['path','id','title','searchable_text']:
            if indexes.has_key(idx):
                idxs.append(idx)

        if idxs:
            catalog.catalog_object(self, path, idxs=idxs)
            
        
    def unindex_object(self):
        """A common method to allow Findables to unindex themselves."""
        try:
            catalog = self.getCatalog()
        except AttributeError:
            try:
                catalog = self.Catalog
            except AttributeError:
                return 
        
        catalog.uncatalog_object('/'.join(self.getPhysicalPath()))
        
    def getId(self):
        """ return id """
        return self.id

    def getTitle(self):
        """ return title """
        return self.title
    
    def getTitle_ascii(self):
        """ return title ascii encoded """
        return internationalizeID(self.getTitle())
    
    def title_or_id(self):
        """ return title or id """
        return self.getTitle() or self.getId()

    def _saveTitle(self, title):
        """ private save method """
        assert isinstance(title, unicode), "Title must be unicode type"
        self.title = title
    
    def getLongTitle(self):
        """ return the long title or the default short one """
        return self.longtitle or self.getTitle()
    
    def manage_getSlots(self):
        """ return the slots """
        return self._slots_order
    
    def manage_getNonEmptySlots(self):
        """ return the slots """
        slots = []
        for slot in self.manage_getSlots():
            if self.manage_getSlotInfo(slot)['raw']:
                slots.append(slot)            
        return slots
    
    security.declareProtected(MANAGE_DOCUMENT, 'manage_getSlotInfo')
    def manage_getSlotInfo(self, slot, ignore_versioning=False):
        """ wrapper for _getSlotInfo() but restricted """
        return self._getSlotInfo(slot, ignore_versioning=ignore_versioning)
    
    def has_slot(self, slotname):
        """ return true if the document has a slot by this name """
        return slotname in self.manage_getSlots()
    
    def manage_getEditableSlots(self):
        """ return a list of slots that can be edited manually """
        ok = []
        for slot in self.manage_getSlots():
            if self._getSlotInfo(slot).get('editable',True):
                ok.append(slot)
        return ok
    
    def getMetalObjectId(self):
        """ return metalobjectid """
        return self.metalobjectid
    
    def getVersion(self):
        """ return version """
        return self.version
    
    def getValidationError(self):
        """ return the validation error that the Page Template reports.
        ...if currently no validation error, return None
        """
        base = getattr(self, 'aq_base', self)
        if not hasattr(base, 'index_html_template'):
            return None
        template = self.index_html_template
        if template.pt_errors():
            # automatically create a simple page template and fetch it's 
            # error message and then delete it.
            if hasattr(self, 'error_template_temporary'):
                self.manage_delObjects(['error_template_temporary'])
            adder = self.manage_addProduct['PageTemplates'].manage_addPageTemplate
            adder('error_template_temporary')
            error_pt = self.error_template_temporary
            slot = self.manage_getSlots()[0]
            slotinfo = self._getSlotInfo(slot)
            error_pt.write(slotinfo['rendered'])
            try:
                reason, explaination = error_pt.pt_errors()
            except TypeError:
                if error_pt.pt_errors() is None:
                    reason = explaination = None
            self.manage_delObjects(['error_template_temporary'])
            if reason == "Compilation failed":
                return self._tidyValidationError(explaination)
        return None
    
    def _tidyValidationError(self, msg):
        """ return it a bit more user friendly. """
        if msg.startswith('TAL.HTMLTALParser.'):
            msg = msg[len('TAL.HTMLTALParser.'):]
        return msg
        
        
    
    def manage_fixBrokenSlotsOrder(self):
        """ return true if the _slots_order isn't the same as 
        the _texts.keys() and if we can fix it. """
        x = self._slots_order[:]
        y = self._texts.keys()
        x.sort(); y.sort()
        if x != y:
            if len(x) > len(y):
                # we can remove some stuff from x
                new_x = []
                for e in x:
                    if e in y:
                        new_x.append(e)
                x = new_x
            elif len(x) < len(y):
                for e in y:
                    if e not in x:
                        x.append(e)
                        
            # the two ifs above will fix x if it's missing or is in excess
            # of items. It might still not be right. 
            if x != y:
                # they are just too different
                x = y
            self._slots_order = x
            return True
        
        else:
            return False
    
    def _beLike(self, document):
        """ make sure this document has the same properties as the
        passed in one has. """
        #self._slots_order = document.manage_getSlots()
        texts = self._getTexts()
        for slot, revisions in document._getTexts().items():
            if not texts.has_key(slot):
                continue
            
            if isinstance(revisions, dict):
                # we're trying to be _beLike(an-old-style-document_
                document_slotinfo = revisions
            else:
                # grab the latest revision
                document_slotinfo = revisions[0]
            
            this_slotinfo = self._getSlotInfo(slot)
            
            this_slotinfo['wysiwyg'] = document_slotinfo['wysiwyg']
            if document_slotinfo.has_key('editable'):
                this_slotinfo['editable'] = document_slotinfo['editable']
            this_slotinfo['format'] = document_slotinfo['format']
            
            self._saveSlotInfoPlain(slot, this_slotinfo)
        
        # now, document._slots_order is a list that we want this
        # document to be sorted like. The only problem is that there
        # might be items in document._slots_order that doesn't appear
        # in self._slots_order hence this ad hoc loop
        
        old = self._slots_order[:] # make a copy
        new = []
        for item in document._slots_order:
            if item in old:
                new.append(item)
                old.remove(item)
        # this appends those new items there weren't in document._slots_order
        new.extend(old)
        self._slots_order = new
        
        # copy the ztinymce_configuration if possible
        if document.getCurrentTinyMCEConfiguration():
            ztinymce_configuration = document.getCurrentTinyMCEConfiguration()
            if hasattr(self, ztinymce_configuration):
                self._saveTinyMCEConfigurationChoice(ztinymce_configuration)
        
        
    def _incrementVersion(self, increment_major=0, to=None):
        """ increment the version number """
        if to:
            self.version = float(to)
        elif increment_major:
            major, minor = str(self.getVersion()).split('.')[0], 0
            major = int(major)+1
            self.version = float("%s.%s"%(major, minor))
        else:
            major, minor = str(self.getVersion()).split('.')
            minor = int(minor) + 1
            self.version = float("%s.%s"%(major, minor))
    
            
    def hasRevisions(self, slot):
        """ nice and tidy wrapper around _getSlotRevisionTimestamps()
        """
        timestamps = self._getSlotRevisionTimestamps(slot)
        return len(timestamps) > 1
    

    def getRevisionTimestamps(self, slot, skip_first=False):
        """ return the timestamps nicely and sorted """
        return self._getSlotRevisionTimestamps(slot, True, skip_first=skip_first)

    def countRevisionTimestamps(self, slot):
        """ return how many revisions there are of this slot """
        return len(self._getSlotRevisionTimestamps(slot))
    
    
    def _getSlotRevisionTimestamps(self, slot, formatted=False, skip_first=False):
        """ return a list of all revision timestamps of this slot """
        
        if self.inVersioning():
            _texts = self._texts_versioning
        else:
            _texts = self._texts
            
        try:
            timestamps = [x['revision_timestamp'] for x in _texts[slot]]
        except KeyError, reason:
            if reason.args[0] == 'revision_timestamp':
                # old style
                return []
            else:
                raise SlotKeyError, slot

        if skip_first:
            timestamps = timestamps[1:]

        if formatted:
            now = time.time()
            cnow = time.gmtime(now)
            dates = []
            today_fmt = 'Today %H:%M:%S'
            other_fmt = '%b %d %H:%M'
            for timestamp in timestamps:
                date = format_timestamp(timestamp)
                dates.append(dict(timestamp=timestamp, date=date))
            return dates
                
        else:
            return timestamps
            

    def _getSlotRevisions(self, slot):
        """ return a list of all revisions for a particular slot """
        
        if self.inVersioning():
            try:
                _texts = self._texts_versioning
                if _texts == {}:
                    self._initVersioningTexts(slot)
                    return self._getSlotRevisions(slot)
            except AttributeError:
                self._startVersioningTexts()
                return self._getSlotRevisions(slot)
        else:
            _texts = self._texts
            
        return _texts[slot]
        
    
    def _startVersioningTexts(self):
        """ create the variable _texts_versioning into this class """
        self._texts_versioning = {}
        self._initVersioningTexts()
        
    def _initVersioningTexts(self):
        """ the variable _texts_versioning is empty, copy the last 
        copy from the non-versioning. """
        if Set(self.manage_getSlots()) != Set(self._texts.keys()):
            self.manage_fixBrokenSlotsOrder()
            
        source = self._texts
        if not hasattr(self, '_texts_versioning'):
            self._texts_versioning = {}
        destination = self._texts_versioning
        
        for slot in self.manage_getSlots():
            destination[slot] = [copy.copy(source[slot][0])]
            
        self._texts_versioning = destination
        
        
    def _getSlotInfo(self, slot, ignore_versioning=False):
        """ return the slot info """

        _texts = self._getTexts(ignore_versioning=ignore_versioning)
            
        try:
            # always return the latest (1st) item inside the slot revisions
            return _texts[slot][0]
        except KeyError, reason:
            if reason.args[0] == 0:
                try:
                    return _texts[slot]
                except KeyError:
                    raise SlotKeyError, slot
            else:
                # search for it
                matcher = ss(slot)
                for slotkey, revisions in _texts.items():
                    if matcher == ss(slotkey):
                        self.__slow_slotInfokey(slot)
                        if isinstance(revisions, dict):
                            # old where the list of revisions is just a dict
                            return revisions
                        else:
                            return revisions[0]
                        
                # eh? still here?
                raise SlotKeyError, slot
            
    def _saveSlotInfoPlain(self, slot, newinfo, ignore_versioning=False):
        """ unlike _saveSlotInfo() this save is much simpler because it 
        DOES NOT create a new revision. 
        This is useful if the change is too unimportant to deserve a user-facing
        revision.
        If 'ignore_versioning', don't listen to inVersioning() and save directly
        into self._texts.
        """
        _texts = self._getTexts(ignore_versioning=ignore_versioning)
    
        revisions = _texts[slot]
        if isinstance(revisions, dict):
            # old old old! Upgrade this legacy slot info.
            # Variable 'revisions' is now a dict with keys: editable, raw, format, etc.
            
            # set the previous to the objects bobobase_modification_time minus 
            # 1 second so that we can be certain it's older.
            mod_time = self.bobobase_modification_time()
            revisions['revision_timestamp'] = float(mod_time)-1
            revisions = [newinfo]
        else:
            # overwrite the 0th item of the revisions
            revisions[0] = newinfo
            
        _texts[slot] = revisions
        
        if self.inVersioning() and not ignore_versioning:
            self._texts_versioning = _texts
        else:
            self._texts = _texts
            
    def _reinstateRevision(self, slot, revision_timestamp):
        """ move a slotinfo in on top """
        # accuracy down to the second. Should be enough.
        revision_timestamp = int(float(revision_timestamp)) 
        newinfo = None
        for revision in self._getSlotRevisions(slot):
            if int(revision['revision_timestamp']) == revision_timestamp:
                newinfo = copy.copy(revision)
                break
            
        if newinfo is None:
            fmt = "That revision timestamp key (%r) does not exist in slot %r"
            raise RevisionError, fmt % (revision_timestamp, slot)
        
        self._saveSlotInfo(slot, newinfo)
        self._is_cooked = False
            
        
    def _saveSlotInfo(self, slot, newinfo):
        """ save new values from outside. """
        newinfo['revision_timestamp'] = time.time()
        
        # _getTexts() is clever to return the correct class variable
        # depending on the state of versioning
        _texts = self._getTexts()
        
        revisions = _texts[slot]
        if isinstance(revisions, dict):
            # old old old! Upgrade this legacy slot info.
            # Variable 'revisions' is now a dict with keys: editable, raw, format, etc.
            
            # set the previous to the objects bobobase_modification_time minus 
            # 1 second so that we can be certain it's older.
            revisions['revision_timestamp'] = float(self.bobobase_modification_time())-1
            revisions = [newinfo, _texts[slot]]
        else:
            
            # only create a new revision if the new info is different to previous
            # one.
            if _equal_revisions(newinfo, revisions[0]):
                # That was the basic test. The user hasn't entered different
                # content into the slots. Perhaps something else has changed, and
                # if so, make a save but without creating a new revision. Just
                # update the latest revision_timestamp.
                if not _exactly_equal_revisions(newinfo, revisions[0]):
                    # they are different in some tiny detail
                    revisions[0] = newinfo
            else:
                # add a new revision
                revisions.insert(0, newinfo)
                if len(revisions) > REVISIONS_MAXLENGTH:
                    revisions = revisions[:REVISIONS_MAXLENGTH]
            
        
                    
        _texts[slot] = revisions
        
        if self.inVersioning():
            self._texts_versioning = _texts
        else:
            self._texts = _texts
            
        
    def _tidyRawSlot(self, slot):
        """ open up the slot and attempt to clean the raw content """
        slotinfo = self._getSlotInfo(slot)
        fmt = slotinfo['format']
        if fmt == 'html':
            raw = slotinfo['raw']
            slotinfo['raw'] = self._tidyText(raw)
            self._saveSlotInfoPlain(slot, slotinfo)
            
    def _beautifySlot(self, slot):
        slotinfo = self._getSlotInfo(slot)
        fmt = slotinfo['format']
        if fmt == 'html':
            raw = slotinfo['raw']
            slotinfo['raw'] = beautifyhtml(raw, self.getUnicodeEncoding())
            
            self._saveSlotInfoPlain(slot, slotinfo)
        else:
            raise NotImplementedError, "unable to beautify text of type %r" % fmt
                
    def __slow_slotInfokey(self, slotkey):
        """ make a note that someone managed to access a slot info
        but with incorrect case on the key which slowed down the
        time it took for find the item. """
        m = "Findable but incorrect case for slot key %r in "%slotkey
        _module = inspect.stack()[2][1]
        _method = inspect.stack()[2][3]
        _line = inspect.stack()[2][2]
        m += "%s.%s line %s"%(_module, _method, _line)
        LOG("FriedDocument._getSlotInfo()", WARNING, m)
        
    def getText(self, slot):
        """ return the raw text """
        return self._getSlotInfo(slot)['raw']
    
    def showText(self, slot):
        """ return the rendered text """
        return self._getSlotInfo(slot)['rendered']
    
    def getFormat(self, slot):
        """ return the format of this slot """
        return self._getSlotInfo(slot)['format']
    
    def canWYSIWYG(self, slot):
        """ return the wysiwyg bool of this slot """
        return self._getSlotInfo(slot)['wysiwyg']
    
    def canEdit(self, slot):
        """ return the editable bool of this slot """
        return self._getSlotInfo(slot).get('editable', True)

    def getLanguage(self):
        """ return language """
        return getattr(self, 'language', 'en')
    

    def getExpiryHours(self):
        """ return expiry_hours """
        return self.expiry_hours
    
    
    def getCSSURL(self, absolute=False):
        """ return the URL of the CSS file/object which is used on the site,
        this takes used in the WYSIWYG editor so that it looks like you're
        editing right there in context. """
        url = self.css_url
        if absolute and not url.startswith('http'):
            if url.startswith('/'):
                return self.REQUEST.BASE0 + url
            else:
                url1 = self.REQUEST.URL1
                url1_parts = url1.split('/')
                if 'externalEdit_' in url1_parts:
                    url1_parts.remove('externalEdit_')
                url1 = '/'.join(url1_parts)
                return url1 +'/' + url
        else:
            return url

    
    
        
    security.declareProtected('View', 'view')
    def view(self, REQUEST, **kw):
        """ return the composed page """
        
        # By being alert to this variable in REQUEST we make it possible
        # to view the page like an anonymous would see it even if you're
        # logged in normally.
        SUPPRESS_VERSIONING = REQUEST.get('SUPPRESS_VERSIONING', False)
        
        if self.metalobjectid is None:
            slot = self.manage_getSlots[0]
            return self.showText(slot)
        else:
            if self.getExpiryHours():
                # let's return the cached version
                if hasattr(getattr(self, 'aq_base', self), 'index_html_cached'):
                    template = self.index_html_cached
                    template_time = template.bobobase_modification_time()
                    if ((DateTime() - template_time) * 24) < self.getExpiryHours():
                        return template(self)
                
                if not self._is_cooked:
                    self._cook()
                    
                # Need to create the cached version
                res = self.index_html_template(self, REQUEST, **kw)
                _extra_stuff = '<tal:cache replace="python:here.doCache(%s)" />'
                _extra_stuff = _extra_stuff % self.getExpiryHours()
                res = _extra_stuff + res
                self._save_template(res, 'index_html_cached')
                return res
                    
            if not self._is_cooked:
                self._cook()

            # If the document is in versioning mode, we have to figure out
            # who it is who is trying to watch this document. If in versioning,
            # only a user with the access permission to edit Fried Documents 
            # should get the index_html_versioning. All others
            # get the plain index_html_template which is likely to be one 
            # or more revisions behind. The reason we're relying on the 
            # inVersioning() instead of doing the user permission test first is 
            # that doing a boolean check first is much faster.
            # That means that if a manager is keeping a Fried Document in versioning
            # the anonymous usage of the template is slightly slower duing that
            # time. In other words, try to not be in versioning mode too much.
            if self.inVersioning() and not SUPPRESS_VERSIONING:
                if self._isFriedDocumentManager():
                    # they can watch the latest revision if it exists
                    self.doCache(0)
                    return self.index_html_versioning(self, REQUEST, **kw)
                
            return self.index_html_template(self, REQUEST, **kw)

    security.declareProtected('View', 'index_html')
    index_html=__call__=view
    
    def _isFriedDocumentManager(self):
        """ return true if the currently logged in user has permission
        to see the unpublished changes to a document. """
        user = getSecurityManager().getUser()
        return user.has_permission(MANAGE_DOCUMENT, self)
        
        
    def _getTexts(self, ignore_versioning=False):
        """ return the dict where all the slots are defined. """
        
        # for debugging
        assert ignore_versioning in (True, False, 1,0)
        
        if self.inVersioning() and not ignore_versioning:
            try:
                return self._texts_versioning
            except AttributeError:
                self._initVersioningTexts()
                return self._getTexts(ignore_versioning=ignore_versioning)
        else:
            return self._texts
        
    
    def _saveTexts(self, new_texts):
        """ save to the _texts variable """
        raise DeprecatedError, "Use _saveSlotInfo() instead"
    
        
    def _reset_cached_template(self):
        """ if this Document has a cached version, remove it """
        base = getattr(self, 'aq_base', self)
        if hasattr(base, 'index_html_cached'):
            self.manage_delObjects(['index_html_cached'])
            
    def _reset_versioning_template(self):
        """ if this Document has a versioning version, remove it """
        base = getattr(self, 'aq_base', self)
        if hasattr(base, 'index_html_versioning'):
            self.manage_delObjects(['index_html_versioning'])            
            
    def _save_template(self, html_code, templateid,
                       view_permission_roles=None, encoding=None):
        """ make sure we have a Page Template in place with 
        this index_html html code. """
        if encoding == 'ascii':
            html_code = html_code.encode('ascii','xmlcharrefreplace')
            
        if templateid in self.objectIds('Page Template'):
            o = getattr(self, templateid)
            if o.wl_isLocked():
                o.wl_clearLocks()
            self.manage_delObjects([templateid])
        # create
        adderspace = self.manage_addProduct['PageTemplates']
        adderspace.manage_addPageTemplate(templateid)
        pt = getattr(self, templateid)
        pt.pt_setTitle(self.getTitle())
        
        # In zope's before Zope 2.8.0, the PageTemplate.write() method stupidly
        # only accepts pure strings, not unicode strings. If you try to write a 
        # unicode string into pt.write() you get an AssertionError.
        try:
            pt.write(html_code)
        except AssertionError:
            # if you get an UnicodeEncodeError here, then maybe it's time to 
            # upgrade your Zope to >= 2.8.0
            pt.write(html_code.encode('iso-8859-1'))
        
        if view_permission_roles:
            if isinstance(view_permission_roles, basestring):
                view_permission_roles = [view_permission_roles]
            view_permission_roles = list(view_permission_roles)
            
            # Set that you have to have any of these roles to 
            # have the View permission on this object
            pt.manage_permission('View', roles=view_permission_roles,
                                 acquire=False)
        
        

    def _findMetalSlots(self):
        """ re-prepare all the slots that should be editable """
        if self.inVersioning():
            raise NotImplementedError, \
            "Currently unable to refind MetalSlots in versioning mode"
            
        if self.metalobjectid is None:
            return 
        try:
            metaltemplate = self.restrictedTraverse(self.metalobjectid)
        except KeyError, msg:
            msg = "%s (url=%s)" % (msg, self.absolute_url_path())
            raise KeyError, msg
        _macros = metaltemplate.macros
        key1 = _macros.keys()[0]
        value = _macros[key1]
        slots = _find_metalslots(value)

        existing_slots = self._slots_order
        _texts = self._texts
        count_new_slots = 0
        for slot in slots:
            if slot not in existing_slots:
                # ! there is a new slot in the metal template!
                existing_slots.append(slot)
                _texts.update( _dict_constructor(slot))
                count_new_slots += 1
        
        if count_new_slots:
            # write back into ZODB
            self._texts = _texts
            self._slots_order = existing_slots
        
        return count_new_slots
     
    
    def _cook(self):
        """ prepare all the texts and create the correct page templates """
        
        if hasattr(self, 'error_template_temporary'):
            self.manage_delObjects(['error_template_temporary'])
            
        encoding = self.getUnicodeEncoding()
        
        # make sure the title is in unicode
        if isinstance(self.title, str):
            self.title = lazy_unicodify(self.title, encoding)
            
        prepared_texts = {}
        #_texts = self._getTexts(ignore_versioning=True)
        _texts = self._getTexts()
        for slot, revisions in _texts.items():
            if isinstance(revisions, dict):
                # Then it must be an old version that was created
                # before there were revisions
                self._convert_oldstyle_slots()
                return self._cook()
            
            latest_revision = revisions[0]

            raw = lazy_unicodify(latest_revision['raw'], encoding)
                
            fmt = latest_revision['format']
            
            # Check if there's a callable script in the zodb
            # called 'FriedPreRenderHook'
            if hasattr(self, 'FriedPreRenderHook') and \
              callable(getattr(self, 'FriedPreRenderHook')):
                raw_hook = self.FriedPreRenderHook(raw, fmt, slot)
                if raw_hook is not None:
                    raw = raw_hook
                
            
            rendered = self._prerenderText(raw, fmt)
           
            # Check if there's a callable script in the zodb
            # called 'FriedPostRenderHook'
            
            if hasattr(self, 'FriedPostRenderHook') and \
              callable(getattr(self, 'FriedPostRenderHook')):
                rendered_hook = self.FriedPostRenderHook(rendered, fmt, slot)
                if rendered_hook is not None:
                    rendered = rendered_hook

            latest_revision['rendered'] = rendered
            #self._saveSlotInfoPlain(slot, latest_revision, ignore_versioning=True)
            self._saveSlotInfoPlain(slot, latest_revision)

        
        # Ok. Now we can start creating the Page Templates (our ad-hoc cache)
        _tag = '<!-- FriedDocument-%s by Fry-IT Ltd. Generated %s -->\n'

        if self.macroname:
            head = '<html metal:use-macro="here/%s/macros/%s">\n'
            head = head % (self.metalobjectid, self.macroname)
            head_edit = '<br tal:replace="here/stopCache" />' + head
        else:
            head = '<html metal:use-macro="here/%s">\n'
            head = head % self.metalobjectid
            head_edit = '<br tal:replace="here/stopCache" />' + head
            
        head += _tag%(__version__, DateTime().rfc822())
        
        foot = '</html>'

        # If the document is being versioned we have to create three
        # new Page Templates:
        #    - index_html_versioning
        #    - index_html_template
        #    - editable
        #
        # If not, just these:
        #    - index_html_template
        #    - editable
        #
        # If not in versioning, make sure there's no 'index_html_versioning' 
        # template lying around. 
        if self.inVersioning():
            # get the code for index_html_versioning and editable
            html_edits, html_slots = self._getHTMLEditsAndSlots()
            
            html_code = head + '\n'.join(html_slots) + foot
            edit_code = head_edit + '\n'.join(html_edits) + foot
            self._save_template(html_code, 'index_html_versioning',
                                view_permission_roles='Manager',
                                encoding=encoding)
            self._save_template(edit_code, 'editable', 
                                view_permission_roles='Manager',
                                encoding=encoding)
                                
            # now we have to do one for the mortals who will be reading
            # from the index_html_template
            __, html_slots = self._getHTMLEditsAndSlots(ignore_versioning=True)
            html_code = head + '\n'.join(html_slots) + foot
            self._save_template(html_code, 'index_html_template',
                                encoding=encoding)
            
        else:
            self._reset_versioning_template()
            # We don't really need to pass ignore_versioning=True
            # to _getHTMLEditsAndSlots() but I do that just to be extra clear
            # on the understanding that _getHTMLEditsAndSlots() will return the
            # stuff based on the non-versioning and save this only to:
            #   index_html_template and editable
            html_edits, html_slots = self._getHTMLEditsAndSlots(ignore_versioning=True)
            
            html_code = head + '\n'.join(html_slots) + foot
            edit_code = head + '\n'.join(html_edits) + foot
            self._save_template(html_code, 'index_html_template', 
                                encoding=encoding)
            self._save_template(edit_code, 'editable', 
                                view_permission_roles='Manager',
                                encoding=encoding)

        self._reset_cached_template()
        
        self._is_cooked = True
        

    def _getHTMLEditsAndSlots(self, ignore_versioning=False):
        """ return two lists.
        
        A "slot" in this context is a piece of HTML that wraps the rendered
        text in a METAL macro fill command like this:
            '<div metal:fill-slot="someslotname">Bla bla bla</div>'
        
        A "edit" is similar to normal HTML slot except that the content inside
        is javascript loaded so that it can launch an editor.
        """
        
        html_edits = []
        html_slots = []

        
        _ajaxsaver_base = '<script type="text/javascript" '\
                     'src="%s"></script>\n' % \
                     self.getMiscAlias('/misc_/FriedDocument/fd-core.js')
                     
        _ajaxsaver_base += '<script type="text/javascript" '\
                     'src="%s"></script>\n' % \
                     self.getMiscAlias('/misc_/FriedDocument/jquery-1.2.3.min.js')
        
                     
        
        for key, revisions in self._getTexts(ignore_versioning=ignore_versioning).items():
            if isinstance(revisions, dict):
                # old style Fried Document
                value = revisions
            else:
                value = revisions[0]
                
            if not value['raw'].strip():
                continue
            elif not value.get('editable', 1):
                continue
            
            if value['format'] == 'javascript':
                metal_tag = '<script type="text/javascript" metal:fill-slot="%s">%s</script>\n'
            elif value['format'] == 'css':
                metal_tag = '<style type="text/css" metal:fill-slot="%s">\n%s\n</style>\n'
            else:
                metal_tag = '<div metal:fill-slot="%s">%s</div>\n'
            
            # in the rare exception of some keys, we add a omit-tag
            if key in ('title',):
                # override
                metal_tag = '\t<div metal:fill-slot="%s" tal:omit-tag="">%s</div>\n'

            # In zope versions <= 2.8.5 you can't write unicode strings to a 
            # page template. That's why we need to convert the string to ASCII.
            # XXX Todo: find out the Zope version and if > 2.8.5 don't do the encoding
            try:
                slot = metal_tag % (key, value['rendered'].encode('ascii'))
            except UnicodeEncodeError:
                slot = metal_tag % (key, value['rendered'].encode('ascii','xmlcharrefreplace'))
            html_slots.append(slot)
            
            if self.hasTinyMCEConfiguration() and value.get('wysiwyg'):
                _ajaxsaver = _ajaxsaver_base + '<script type="text/javascript" '\
                'src="/misc_/FriedDocument/TinyAjaxSaver.js"></script>\n'
            else:
                _ajaxsaver = _ajaxsaver_base + '<script type="text/javascript" '\
                'src="/misc_/FriedDocument/PlainAjaxSaver.js"></script>\n'
            
                     
            # for the editable version
            t = '''\t<div metal:fill-slot="%s" tal:omit-tag="">''' % key
            t += _ajaxsaver
            t += '''\n\t<script type="text/javascript"><!--
            function prepare2refresh(divid) {
              if (document.getElementById) {
                var ut="<fo" +"rm action=\\\"editable\\\"><"+"div align=\\\"center\\\">";
                ut += "<br/><br/><input type=\\\"submit\\\" value=\\\"Refresh\\\" /><br/><br/>&nbsp;<" +"/div><" +"/form>";
                document.getElementById(divid).innerHTML=ut;
              }
            }
            //--></script>\n\t'''
            
            ee_divtag = ''
            # if ExternalEditor is installed we want to enable a tiny little
            # ExternalEditor pen inside the double-clickable box
            if self.has_ExternalEditor:
                ee_divtag = '''<div style="float:right">
                <a onkeypress="prepare2refresh('%s')" onclick="prepare2refresh('%s')" href="../externalEdit_/%s?slot=%s"
                 ><img src="/misc_/ExternalEditor/edit_icon" border="0" alt="Edit with ExternalEditor" /></a>
                 </div>''' % ('slot-%s' % key,'slot-%s' % key, self.getId(), key)
                
            
            _url = 'editable'
            dblclick_url = Utils.AddParams2URL(_url, {'slot':key})
            border_colour = self.inVersioning() and 'red' or 'blue'
            t += '''<div tal:condition="not:python:request.get('slot')=='%s'"
                 id="slot-%s"
                 ondblclick="location.href='%s'"
                 style="border:1px dashed %s;"
                 title="Doubleclick to edit this area"
                 >%s%s</div>'''%\
                 (key, key, dblclick_url, border_colour, ee_divtag, value['rendered'])
            t += '<noscript>JavaScript required for editing</noscript>'
            t += '\n\n'

            
            editform_base_out = '''
            <textarea name="raw:%s:utext" cols="80%%" rows="15"
            tal:content="python:here.getText(request.get('slot'))"
            ></textarea><br />
            <div id="validationerror" style="display:none"></div>
            \n''' % self.getUnicodeEncoding()
            
            #if value['wysiwyg'] and self.hasTinyMCEConfiguration():
            if value['wysiwyg'] and self.hasTinyMCEConfiguration():
                tinymce_config = self.getTinyMCEConfiguration().getId()
                editform_out = '''<script tal:replace="structure here/%s"></script>\n'''\
                               % tinymce_config
                editform_out += editform_base_out
            else:
                editform_out = editform_base_out
            
            undo_form = ''
            if self.hasRevisions(key):
                unfo_form_html = self.show_revision_undo_form(self, 
                                       self.REQUEST, currentslotname=key,
                                       )
                undo_form_tmpl = '<br /><div id="revisionundoer"'\
                                 '>%s</div>'
                undo_form = undo_form_tmpl % unfo_form_html
                
            formatsourcebutton = ''
            
            # The following is commented out even if it works fine.
            # The reason is that maybe the "Format source" button should
            # only be in manage_Basic since that's the only interesting
            # place where you'll see HTML raw. 
            #
            #if self.canBeautifySource(key):
            #    formatsourcebutton = '<input type="submit" name="beautifysource" '\
            #                         'style="float:right;font-size:80%" '\
            #                         'onclick="id$(\'ajax_return\').value=\'0\'" '\
            #                         'value="Format source" />'
                
            t += '''<div tal:condition="python:request.get('slot')=='%s'"
                 tal:omit-tag=""><form action="manage_saveSlot"
                 method="post" enctype="multipart/form-data"
                 onsubmit="return ajaxSave(this)">
                 <input type="hidden" name="ajax_return" value="1" />
                 <input type="hidden" name="go_editable:int" value="1" />
                 <input type="hidden" name="slot" value="%s" />
                 %s
                 %s
                 <input type="submit" value="Save changes" id="savechangesbutton"
                 onclick="this.value='Saving changes...'" />
                 <input type="button" onclick="location.href='./editable'"
                  value="Exit" />
                 <span id="savemessage" style="font:bold 1.2em 'Trebuchet MS', Verdana, Arial, sans-serif;"></span>
                 </form>
                 %s</div>'''%(key, key, editform_out, formatsourcebutton, undo_form)
                 
            t += '\n</div>\n'
            
            html_edits.append(t)
            
        return html_edits, html_slots
        
    def _prerenderText(self, raw, fmt):
        """ convert the raw text to something more suitable """
        if fmt == 'html':
            prepared = Utils.ShowDescription(raw, fmt)
            tidied = self._tidyText(prepared)
            return tidied
        elif fmt == 'css':
            # Perhaps we should here try to use slimmer ??
            return raw
        
    
    def _tidyText(self, untidytext):
        """ fix up the XHTML if necessary """
        t = untidytext
        t = t.replace('<br>','<br />')
        return t
    
    def _convert_oldstyle_slots(self):
        """ for every slot that is old style, convert it to the new style """
        _texts = self._getTexts(ignore_versioning=True)
        count = 0
        for slot, revisions in _texts.items():
            if isinstance(revisions, dict):
                mod_time = self.bobobase_modification_time()
                revisions['revision_timestamp'] = float(mod_time)-1
                revisions = [revisions]
                _texts[slot] = revisions
                count += 1
                
        if count:
            self._texts = _texts
                

    def _resetVersioning(self):
        """ stop versioning altogether """
        self.in_versioning = False
        self._texts_versioning = {}
        self._reset_versioning_template()
        
    def _publishVersioningChanges(self):
        """ fold in the changes done in versioning into the plain fold """
        assert self.inVersioning(), "Can't publish when not in versioning"
        source = self._getTexts()
        destination = self._getTexts(ignore_versioning=True)
        
        for slot, revisions in source.items():
            # bare in mind that when we created _texts_versioning through
            # _initVersioningTexts() we copied latest revision of _texts
            # to be the first of _texts_versioning. Now when we're publishing
            # we can ignore that one.
            for i, revision in enumerate(revisions[:-1]):
                # insert these into the destination one by one
                destination[slot].insert(i, revision)

        # write this back now into _texts
        self._texts = destination
            
    ##
    ## Management stuff
    ##
    
    def manage_publishVersioning(self, versioning_off=False, REQUEST=None):
        """ fold in the changes from versioning into the non-versioning
        and stop the versioning by going back to auto-publish """
        self._publishVersioningChanges()
        if versioning_off:
            self._resetVersioning()
        self._cook()
        if REQUEST:
            if versioning_off:
                m = "All changes published and auto-publish started again"
            else:
                m = "All changes published"
            if REQUEST.get('HTTP_REFERER').find('/editable') > -1:
                self.http_redirect(self.absolute_url()+'/editable', msg=m)
            else:
                return self.manage_Basic(self, REQUEST, manage_tabs_message=m)        
    
    security.declareProtected(MANAGE_DOCUMENT, 'manage_scrapVersioning')
    def manage_scrapVersioning(self, REQUEST=None):
        """ delete the versioning content and stop being in versioning mode """
        self._texts_versioning = {}
        self.in_versioning = False
        if REQUEST:
            m = "Auto-publish started again"
            if REQUEST.get('HTTP_REFERER').find('/editable') > -1:
                self.http_redirect(self.absolute_url()+'/editable', msg=m)
            else:
                return self.manage_Basic(self, REQUEST, manage_tabs_message=m)
            
    
    security.declareProtected(MANAGE_DOCUMENT, 'manage_reinstateRevision')
    def manage_reinstateRevision(self, slot, revision_timestamp, REQUEST=None):
        """ make the latest revision be a copy of this revision_timestamp 
        from before.
        The slot and the revision_timestamp should exist.
        """
        try:
            revision_timestamp = float(revision_timestamp)
        except ValueError:
            if revision_timestamp == 'moreoptions':
                return self.http_redirect(self.absolute_url()+'/manage_UndoOptions')
            elif revision_timestamp == 'increasesizelimit':
                kw = {'undo_size_limit':self.countRevisionTimestamps(slot)}
                return self.http_redirect(self.absolute_url()+'/manage_Basic', **kw)
            else:
                raise
            
        self._reinstateRevision(slot, revision_timestamp)
        self._cook()
        
        if REQUEST is not None:
            formatted = format_timestamp(revision_timestamp)
            if re.findall(r'\beditable\b', REQUEST.HTTP_REFERER):
                return self.http_redirect('editable', slot=slot)
            else:
                return self.manage_Basic(self, REQUEST,
                  manage_tabs_message="Slot revision undone to that of %s" % formatted)
        

    security.declareProtected(MANAGE_DOCUMENT, 'manage_setCSSURL')
    def manage_setCSSURL(self, css_url, REQUEST=None):
        """ set the css_url attribute """
        self.css_url = str(css_url)
        if REQUEST is not None:
            return self.manage_Options(self, REQUEST, 
              manage_tabs_message="CSS URL set")
        
    security.declareProtected(MANAGE_DOCUMENT, 'manage_changeFirstslot')
    def manage_changeFirstslot(self, slot, REQUEST=None):
        """ put this slot (if possible) in the top of _slots_order """
        oldorder = self.manage_getSlots()
        neworder = []
        if slot in oldorder:
            neworder.append(slot)
        for each in oldorder:
            if each not in neworder:
                neworder.append(each)
        self._slots_order = Utils.uniqify(neworder)
            
        if REQUEST is not None:
            m = "Slot changed"
            return self.manage_Basic(self, REQUEST, manage_tabs_message=m)
        
    security.declareProtected(MANAGE_DOCUMENT, 'manage_startVersioning')
    def manage_startVersioning(self, REQUEST=None):
        """ enable the in_versioning """
        self.in_versioning = True
        self._initVersioningTexts()
        self._cook()
        if REQUEST is not None:
            m = "Auto-publish stopped"
            if REQUEST.get('HTTP_REFERER').find('/editable') > -1:
                self.http_redirect(self.absolute_url()+'/editable', msg=m)
            else:
                return self.manage_Basic(self, REQUEST, manage_tabs_message=m)
            
    security.declareProtected(MANAGE_DOCUMENT, 'manage_changeEditingmethod')
    def manage_changeEditingmethod(self, method, REQUEST=None):
        """ change the cookie for this user """
        then = DateTime()+300
        then = then.rfc822()
        cookiename = '__frieddoc_editmethod'
        recognized_options = ('wysiwyg','plain')
        assert method in recognized_options, "Unrecognized option for editing"
        self.REQUEST.RESPONSE.setCookie(cookiename, method, path='/',
                                        expires=then)
                                        
        if REQUEST is not None:
            m = "Editing method changed"
            REQUEST.set('editmethod', method)
            return self.manage_Basic(self, REQUEST, manage_tabs_message=m)

    def canBeautifySource(self, slot):
        """ return true if there's any beautification we can do to this 
        source. """
        fmt = self.getFormat(slot)
        if fmt == 'html':
            if beautifyhtml is not None:
                return True
            
        return False
    
    security.declareProtected(MANAGE_DOCUMENT, 'showDiffedHTML')
    def showDiffedHTML(self, html1, html2, show_inserts=False, show_deletions=False):
        """ compare the html of argument with that of the second html argument
        and return a block of HTML.
        """
        print "show_inserts", show_inserts
        print "show_deletions", show_deletions
        print
        
        if lxml_html_diff is None:
            logger.warn("lxml.html diff not installed")
            return html1
        
        d = lxml_html_diff.htmldiff(html1, html2)
        
        css = '<style type="text/css">'
        if show_deletions:
            css += 'del{background-color:#c9f}'
        else:
            css += 'del{display:none}'
        if show_inserts:
            css += 'ins{background-color:#cf9}'
        else:
            css += 'ins{display:none}'
        css += '</style>\n\n'
              
        return css + d
        

    security.declareProtected(MANAGE_DOCUMENT, 'manage_saveSlot')
    def manage_saveSlot(self, slot, raw=None, format=None, wysiwyg=None,
                        title=None, go_editable=False, goto_after=None,
                        ajax_return=False, beautifysource=False,
                        REQUEST=None):
        """ save this slot copy. """

        assert slot in self.manage_getSlots(), "slotname %r not recognized" % slot

        encoding = self.getUnicodeEncoding()
        
        #if self.wl_isLocked():
        #    raise ResourceLockedError, "FriedDocument is locked via WebDAV"
        if title is not None:
            if isinstance(title, unicode):
                self._saveTitle(title)
            else:
                self._saveTitle(unicodify(title, encoding))
            
        info = copy.copy(self._getSlotInfo(slot))

        if raw is not None:
            if isinstance(raw, unicode):
                info['raw'] = raw.strip()
            else:
                info['raw'] = unicodify(raw, encoding).strip()
        if format is not None:
            info['format'] = format
        if wysiwyg is not None:
            info['wysiwyg'] = wysiwyg

        self._saveSlotInfo(slot, info)
                
        if niceboolean(beautifysource):
            self._beautifySlot(slot)
            
        self._tidyRawSlot(slot)

        self._cook()

        self._incrementVersion()
        
        self.reindex_object()

        m = "Changes saved"
        if niceboolean(ajax_return):
            return m
        
        if REQUEST is not None:
            if go_editable:
                return self.editable(self, REQUEST, manage_tabs_message=m)
            elif goto_after:
                goto_after = Utils.AddParams2URL(goto_after, {'manage_tabs_message':m})
                self.REQUEST.RESPONSE.redirect(goto_after)
                return 
            else:
                return self.manage_Basic(self, REQUEST, manage_tabs_message=m)
            
    security.declareProtected(MANAGE_DOCUMENT, 'manage_changeDocumentTitle')
    def manage_changeDocumentTitle(self, new_title, 
                                   use_show_in_nav=False, show_in_nav=False,
                                   REQUEST=None):
        """ change the document title """
        encoding = self.getUnicodeEncoding()
        self._saveTitle(unicodify(new_title, encoding))
        
        if use_show_in_nav:
            self.manage_setShowInNav(show_in_nav)
        
        if REQUEST:
            if REQUEST.get('ajax_return'):
                return new_title
            else:
                REQUEST.RESPONSE.redirect(REQUEST.HTTP_REFERER)
            
    def embedDisplayInURL(self, url, display_size):
        """ if a the URL is 
        /somewhere/something/foo.jpg
        return 
        /somewhere/something/display-<display_size>/foo.jpg
        """
        if display_size:
            # remove previous display-<something>
            url = re.sub(r'display-\w+/', '', url)
            parent_path = '/'.join(url.split('/')[:-1])
            if parent_path and not parent_path.endswith('/'):
                parent_path += '/'
            objid = url.split('/')[-1]
            url = "%sdisplay-%s/%s" % (parent_path, display_size, objid)
        return url
         
        

    security.declareProtected(MANAGE_DOCUMENT, 'manage_basic_editing_method')
    def manage_basic_editing_method(self, currentslot=None):
        """ return what editing method the user prefers. """
        default = 'plain'
        if currentslot:
            info = self._getSlotInfo(currentslot)
            # maybe it should always be 'plain' for this slot
            if not info['wysiwyg']:
                return default
            
        cookiename = '__frieddoc_editmethod'
        if self.REQUEST.has_key('editmethod'):
            val = self.REQUEST.get('editmethod')
        else:
            val = self.REQUEST.cookies.get(cookiename, default)
            
        return ss(val)
    
    security.declareProtected(MANAGE_DOCUMENT, 'manage_setEditingOptions')
    def manage_setEditingOptions(self, enable_editing=[], enable_wysiwyg=[],
                                 formats=[],
                                 goto_after=None, REQUEST=None):
        """ expect a list of slot names where WYSIWYG should be enabled.
        'formats' is sorted exactly like slots is sorted, so we can use
        indexing to find out what format each slot should have. """
        slots = self.manage_getSlots()
        count = 0
        for slot in slots:
            info = self._getSlotInfo(slot)
            if slot in enable_wysiwyg:
                # yes, this slot should be editable with WYSIWYG
                info['wysiwyg'] = True
            else:
                info['wysiwyg'] = False
            if slot in enable_editing:
                # yes, this slot should be editable
                info['editable'] = True
            else:
                info['editable'] = False
            
            if formats is not None:
                format = formats[count]
                if format != 'html':
                    info['wysiwyg'] = False
                info['format'] = format
            count += 1
            
            self._saveSlotInfoPlain(slot, info)
    
        self._cook()
        
        # exit
        if REQUEST is not None:
            m = "Slot WYSIWYG options changed"
            if goto_after:
                goto_after = Utils.AddParams2URL(goto_after, {'manage_tabs_message':m})
                self.REQUEST.RESPONSE.redirect(goto_after)
                return 
            else:
                return self.manage_Options(self, REQUEST, manage_tabs_message=m)
        
            

    security.declareProtected(MANAGE_DOCUMENT, 'manage_setShowInNav')
    def manage_setShowInNav(self, show_in_nav=False, goto_after=None, REQUEST=None):
        """ set the show_in_nav boolean """
        self.show_in_nav = niceboolean(show_in_nav)

        if REQUEST is not None:
            if self.show_in_nav:
                m = "Included in navigation"
            else:
                m = "Not included in navigation"
            if goto_after:
                goto_after = Utils.AddParams2URL(goto_after, {'manage_tabs_message':m})
                self.REQUEST.RESPONSE.redirect(goto_after)
                return 
            else:
                return self.manage_Options(self, REQUEST, manage_tabs_message=m)
        
        
    security.declareProtected(MANAGE_DOCUMENT, 'manage_setExpiryOptions')
    def manage_setExpiryOptions(self, hours, disable=False, 
                                goto_after=None, REQUEST=None):
        """ method for letting you set the expiry hours """
        if disable:
            hours = 0
            self._reset_cached_template()
        else:
            if hours:
                hours = float(hours)
                if hours > 1000:
                    # insane value
                    raise SubmitError('Number of hours far too big')
                if hours < 0:
                    hours = 0
            else:
                hours = 0
            
        self.expiry_hours = hours
        
        if REQUEST is not None:
            m = "Expiry header set"
            if goto_after:
                goto_after = Utils.AddParams2URL(goto_after, {'manage_tabs_message':m})
                self.REQUEST.RESPONSE.redirect(goto_after)
                return 
            else:
                return self.manage_Options(self, REQUEST, manage_tabs_message=m)
        
            
        
    def tabs_path_default(self, REQUEST,
                          # Static var
                          unquote=urllib.unquote,
                          ):
        """ This I stole from App/Management.py because I want to use
        my own javascript links """
        steps = REQUEST._steps[:-1]
        script = REQUEST['BASEPATH1']
        linkpat = '<a href="%s/manage_workspace">%s</a>'
        
        out = []
        url = linkpat % (escape(script, 1), '&nbsp;/')
        
        if not steps:
            return url
        last = steps.pop()
        for step in steps:
            script = '%s/%s' % (script, step)
            out.append(linkpat % (escape(script, 1), escape(unquote(step))))
        script = '%s/%s' % (script, last)

        pat = '<a class="strong-link" href="%s/manage_workspace">%s</a>'
        
        out.append(pat%(escape(script, 1), escape(unquote(last))))
        return '%s%s' % (url, '/'.join(out))
    
        
    def tabs_path_default_js_enabled(self, REQUEST,
                          # Static var
                          unquote=urllib.unquote,
                          ):
        """ This I stole from App/Management.py because I want to use
        my own javascript links """
        steps = REQUEST._steps[:-1]
        script = REQUEST['BASEPATH1']
        #linkpat = '<a href="%s/manage_workspace">%s</a>'
        linkpat = """<a href="#" onclick="go('%s/manage_workspace')">%s</a>"""
        
        out = []
        url = linkpat % (escape(script, 1), '&nbsp;/')
        
        if not steps:
            return url
        last = steps.pop()
        for step in steps:
            script = '%s/%s' % (script, step)
            out.append(linkpat % (escape(script, 1), escape(unquote(step))))
        script = '%s/%s' % (script, last)

        pat = """<a class="strong-link" href="#" """\
              """onclick="go('%s/manage_workspace')">%s</a>"""
        
        out.append(pat%(escape(script, 1), escape(unquote(last))))
        return '%s%s' % (url, '/'.join(out))
    
    
    ##
    ## /manageable stuff
    ##
    
    def managable(self, REQUEST):
        """ wrong bad spelling """
        url = REQUEST.URL
        if REQUEST.get('QUERY_STRING'):
            url += '?' +REQUEST.get('QUERY_STRING')
        REQUEST.RESPONSE.redirect(url.replace('managable','manageable'))
    
    def getMETALHeader(self):
        """ return the header macro """
        metalheader = getattr(self, self.metalobjectid)
        if hasattr(metalheader, 'macros'):
            return metalheader.macros[self.macroname]
        else:
            return metalheader()
    
    def getObjectList(self):
        """ return all the viewable and interesting objects here """
        mtypes = [META_TYPE, 'Image', 'Photo','File']
        here = self.objectValues(mtypes)
        if self.getId() == 'index_html':
            add = aq_parent(aq_inner(self)).objectValues(mtypes)
            add = [x for x in add 
                     if x.getId() != 'index_html']
            here.extend(add)
        return here
    
    def getSpecialListIcon(self, obj):
        """ return the path to the icon file if we have a good one """
        try:
            ext = obj.getId().lower().split('.')[-1]
        except IndexError:
            return None
        
        maps = {
        'xls':'objecticon_xls.gif',
        'doc':'objecticon_doc.gif',
        'zip':'objecticon_zip.gif',
        'pdf':'objecticon_pdf.gif',
        'mp3':'objecticon_mp3.gif',
        }
        
        start = '/misc_/FriedDocument/'
        if maps.get(ext):
            return start + maps.get(ext)

        return None
        
    
    def getUpFolderLink(self):
        """ return the link to the parent folder with /manageable if possible """
        parent = aq_parent(aq_inner(self))
        if parent.meta_type == META_TYPE:
            return '../manageable'
        elif parent.isPrincipiaFolderish and 'index_html' in parent.objectIds(META_TYPE):
            return '../index_html/manageable'
        
        return None
    
    def showListObjectName(self, obj):
        """ show it nicely """
        if obj.meta_type == META_TYPE:
            id = obj.getId()
            title = obj.getTitle()
        else:
            id = obj.getId()
            title = obj.title
            
        if title:
            if title == id or cookDocumentId(title) == id:
                return title
            else:
                return '%s (%s)' % (id, title)
        else:
            return id
            
    security.declareProtected(VMS, 'saveObjectRenames')
    def saveObjectRenames(self, ids, REQUEST):
        """ save all the renamed objects.
        Expect to find, in the REQUEST, keys that are 
        'newid-%s' % id
        And titles to go with them, like 'titleof-%s' % id
        """
        new_titles = {}
        old_ids = []
        new_ids = []
        
#        return str(REQUEST)
        
        for id in ids:
            obj = getattr(self, id)
            if REQUEST.get('newid-%s' % id):
                new_id = REQUEST.get('newid-%s' % id).strip()
                if new_id != id:
                    old_ids.append(id)
                    new_ids.append(new_id)
            obj_title = obj.title
            # has the title changed?
            titleof = REQUEST.get('titleof-%s' % id).strip()
            if obj_title != titleof:
                obj.title = titleof
                
        # do the rename
        this = self
        if this.getId() == 'index_html':
            try:
                this = aq_parent(aq_inner(self))
            except:
                pass
        this.manage_renameObjects(old_ids, new_ids)
        
        msg = "Rename done"
        msg = urllib.quote_plus(msg)
        url = self.absolute_url()+'/manageable?msg=%s' % msg
        if hasattr(self, 'getRandomString'):
            url += '&randr=%s' % self.getRandomString()
        
        REQUEST.RESPONSE.redirect(url)
        
    security.declareProtected(VMS, 'copyObjectsSelected')
    def copyObjectsSelected(self, ids, REQUEST):
        """ wrapper on Zope's manage_copyObjects() """
        self.manage_copyObjects(ids, REQUEST=REQUEST)
        
        msg = "Objects copied"
        msg = urllib.quote_plus(msg)
        url = self.absolute_url()+'/manageable?msg=%s' % msg
        if hasattr(self, 'getRandomString'):
            url += '&randr=%s' % self.getRandomString()
        
        REQUEST.RESPONSE.redirect(url)

    security.declareProtected('Delete objects', 'cutObjectsSelected')
    def cutObjectsSelected(self, ids, REQUEST):
        """ wrapper on Zope's manage_copyObjects() """
        self.manage_cutObjects(ids, REQUEST=REQUEST)
        
        msg = "Objects cut"
        msg = urllib.quote_plus(msg)
        url = self.absolute_url()+'/manageable?msg=%s' % msg
        if hasattr(self, 'getRandomString'):
            url += '&randr=%s' % self.getRandomString()
        
        REQUEST.RESPONSE.redirect(url)
        
    def pasteObjectsSelected(self, REQUEST):
        """ wrapper on Zope's manage_copyObjects() """
        self.manage_pasteObjects(REQUEST=REQUEST)
        
        msg = "Objects pasted"
        msg = urllib.quote_plus(msg)
        url = self.absolute_url()+'/manageable?msg=%s' % msg
        if hasattr(self, 'getRandomString'):
            url += '&randr=%s' % self.getRandomString()
        
        REQUEST.RESPONSE.redirect(url)
        
    def deleteObjectsSelected(self, ids, REQUEST):
        """ wrapper on Zope's manage_copyObjects() """
        delspace = self
        if delspace.getId() == 'index_html':
            delspace = aq_parent(aq_inner(delspace))
        delspace.manage_delObjects(ids)
        
        msg = "Objects deleted"
        msg = urllib.quote_plus(msg)
        url = self.absolute_url()+'/manageable?msg=%s' % msg
        if hasattr(self, 'getRandomString'):
            url += '&randr=%s' % self.getRandomString()
        
        REQUEST.RESPONSE.redirect(url)
        
    #
    # Image, Photo related manageable
    #

    def addPictureSimple(self, id, file, title='', quality=100,
                         engine='ImageMagick', 
                         REQUEST=None):
        """ create a Photo object """
        if not self._isFile(file):
            raise SubmitError("No file content in file")
        
        id = id.strip()
        title = title.strip()
        
        if not id:
            filename = getattr(file, 'filename')
            id = filename[max(filename.rfind('/'),
                              filename.rfind('\\'),
                              filename.rfind(':'),
                              )+1:]
        id = internationalizeID(id)
        quality = int(quality)
        assert quality <= 100, "Quality can't be more than 100"
        
        addspace = self
        if addspace.getId() == 'index_html':
            addspace = aq_parent(aq_inner(addspace))
        adder = addspace.manage_addProduct['Photo'].manage_addPhoto
        objid = adder(id, title, file, engine=engine, quality=quality)
        obj = getattr(addspace, objid)
        self._addTinyPhotoDisplay(obj)
        
        if REQUEST is not None:
            self.http_redirect(self.absolute_url()+'/manageable',
                                msg="Picture added")


    security.declareProtected('Change Images and Files', 'editImageSave')
    def editPictureSimple(self, oldid, id, file, title, REQUEST):
        """ change a photo """
        try:
            obj = getattr(self, oldid)
        except Exception, m:
            obj = None
            if self.getId() == 'index_html':
                try:
                    obj = getattr(aq_parent(aq_inner(self)), oldid)
                except:
                    pass
            if obj is None:
                raise Exception, m
            
        id = id.strip()
        title = title.strip()
        
        changes = []
        
        if file is not None:
            if self._isFile(file):
                obj.manage_editPhoto(file)
                changes.append("file data")
                
        if title != obj.title:
            obj.title = title
            changes.append("title")
            
        if id != oldid:
            # rename
            parent = aq_parent(aq_inner(obj))
            parent.manage_renameObjects([oldid], [id])
            changes.append("id")
            
        if changes:
            msg = ", ".join(['%s changed' % x for x in changes])
        else:
            msg = "Nothing changed in image"
        url = self.absolute_url()+'/manageable'
        self.http_redirect(url, msg=msg, editid=id, randr=self.getRandomString())
        
        
    def _isFile(self, file):
        """ Check if Publisher file is a real file """
        if hasattr(file, 'filename'):
            if getattr(file, 'filename').strip() != '':
                # read 1 byte
                if file.read(1) == "":
                    m = "Filename provided (%s) but not file content"
                    m = m%getattr(file, 'filename')
                    raise NotFileError, m
                else:
                    file.seek(0) #rewind file
                    return True
            else:
                return False
        else:
            return False
        
    
    security.declareProtected('Change Images and Files', 'editImageSave')
    def editImageSave(self, oldid, id, title, REQUEST, filedata=None):
        """ save image data """
        try:
            obj = getattr(self, oldid)
        except Exception, m:
            obj = None
            if self.getId() == 'index_html':
                try:
                    obj = getattr(aq_parent(aq_inner(self)), oldid)
                except:
                    pass
            if obj is None:
                raise Exception, m
            
        content_type = obj.content_type
        precondition = obj.precondition
        id = id.strip()
        title = title.strip()
        
        changes = []
        
        if filedata is not None:
            if self._isFile(filedata):
                self._removeTinyPhotoDisplay(obj)
                obj.manage_upload(filedata)
                changes.append("file data")
                
        if title != obj.title:
            obj.manage_edit(title, content_type, precondition)
            changes.append("title")
            
        self._addTinyPhotoDisplay(obj)
            
        if id != oldid:
            # rename
            parent = aq_parent(aq_inner(obj))
            parent.manage_renameObjects([oldid], [id])
            changes.append("id")

        if changes:
            msg = ", ".join(['%s changed' % x for x in changes])
        else:
            msg = "Nothing changed in image"
        url = self.absolute_url()+'/manageable'
        self.http_redirect(url, msg=msg, editid=id, randr=self.getRandomString())
        

    def _addTinyPhotoDisplay(self, photoobject):
        photoobject.manage_addDisplay('tiny', 40, 40)

    def _removeTinyPhotoDisplay(self, photoobject):
        photoobject.manage_delDisplays(['tiny'])
        
                
    def _isFile(self, file):
        """ Check if Publisher file is a real file """
        if hasattr(file, 'filename'):
            if getattr(file, 'filename').strip() != '':
                # read 1 byte
                if file.read(1) == "":
                    m = _("Filename provided (%s) but not file content")
                    m = m%getattr(file, 'filename')
                    raise "NotAFile", m
                else:
                    file.seek(0) #rewind file
                    return True
            else:
                return False
        else:
            return False
      
        
    #
    # File related manageable
    #

    def addFileSimple(self, id, file, title='', 
                         REQUEST=None):
        """ create a Photo object """
        if not self._isFile(file):
            raise SubmitError("No file content in file")
        
        try:
            filename_ext = getattr(file, 'filename').split('.')[-1]
        except IndexError:
            filename_ext = ''
        if anyTrue(filename_ext.lower().endswith, ('png','jpeg','jpg','gif')):
            return self.addPictureSimple(id, file, title=title, REQUEST=REQUEST)
        
        
        id = id.strip()
        title = title.strip()
        
        if not id:
            filename = getattr(file, 'filename')
            id = filename[max(filename.rfind('/'),
                              filename.rfind('\\'),
                              filename.rfind(':'),
                              )+1:]
        id = internationalizeID(id)
        
        
        addspace = self
        if addspace.getId() == 'index_html':
            addspace = aq_parent(aq_inner(addspace))
        adder = addspace.manage_addFile
        obj = adder(id, file, title)
        
        self.http_redirect(self.absolute_url()+'/manageable',
                           msg="File added")



    security.declareProtected('Change Images and Files', 'editFileSimple')
    def editFileSimple(self, oldid, id, file, title, REQUEST):
        """ change a file """
        try:
            obj = getattr(self, oldid)
        except Exception, m:
            obj = None
            if self.getId() == 'index_html':
                try:
                    obj = getattr(aq_parent(aq_inner(self)), oldid)
                except:
                    pass
            if obj is None:
                raise Exception, m
            
        id = id.strip()
        title = title.strip()
        
        changes = []
        
        if file is not None:
            if self._isFile(file):
                obj.manage_upload(file)
                changes.append("file data")
                
        if title != obj.title:
            obj.title = title
            changes.append("title")
            
        if id != oldid:
            # rename
            parent = aq_parent(aq_inner(obj))
            parent.manage_renameObjects([oldid], [id])
            changes.append("id")
            
        if changes:
            msg = ", ".join(['%s changed' % x for x in changes])
        else:
            msg = "Nothing changed in file"
        url = self.absolute_url()+'/manageable'
        self.http_redirect(url, msg=msg, editid=id, randr=self.getRandomString())
        
        
    ##
    ## Ordering
    ##
    
    def reorderFriedObject(self, id, direction, ajax_return=False):
        """ change the order of an object using the OrderedFolder API
        and return the manageable_objectlist template rendered """
            
        ajax_return = niceboolean(ajax_return)
        
        this = self
        if this.getId() == 'index_html':
            try:
                this = aq_parent(aq_inner(self))
            except:
                pass

        if not hasattr(this, 'moveObjectsUp'):
            if ajax_return:
                return "ajax_error: Parent object does not have moveObjectsUp()"
            else:
                raise SubmitError, "Parent object does not have moveObjectsUp()"
        
        this_objectids = this.objectIds()
        this_objectvalues = this.objectValues()
        if id in this_objectids:
            index = this_objectids.index(id)
            delta = 1
            mtypes = [META_TYPE, 'Image', 'Photo']
            if direction == 'up':
                while this_objectvalues[index-delta].meta_type not in mtypes:
                    delta += 1
                this.moveObjectsUp([id], delta=delta)
            else:
                while this_objectvalues[index+delta].meta_type not in mtypes:
                    delta += 1
                this.moveObjectsDown([id], delta=delta)
            objects = self.getObjectList()
            return self.manageable_objectlist(self, self.REQUEST, objects=objects)
        return None    

    #
    # Document related manageable
    #
    def addFriedDocumentSimple(self, title, id=None, 
                               metalmacro=None, belike_path=None,
                               show_in_nav=False,
                               REQUEST=None):
        """ create another fried document """
        
        title = title.strip()
        if not title:
            raise SubmitError, "No title no document :)"
        
        if belike_path:
            if hasattr(self, 'getRoot') and belike_path.startswith('/'):
                root = self.getRoot()
                belike_path = root.absolute_url_path()+belike_path
                if belike_path.startswith('//'):
                    belike_path = belike_path[1:]
            try:
                self.restrictedTraverse(belike_path)
            #except AttributeError:
            except KeyError:
                if belike_path.startswith('/'):
                    # perhaps it's like '/About-me' but the site is actually
                    # virtually hosted in '/sites/SiteA' so that the true
                    # physcical path should be '/sites/SiteA/About-me'
                    try:
                        self.getRoot().restrictedTraverse(belike_path[1:])
                        belike_path = belike_path[1:]
                    except:
                        raise SubmitError, "Invalid belike_path %r" % belike_path
            
        if not belike_path:
            belike_path = self.absolute_url_path()
            
        if not metalmacro:
            # try to use the belike object otherwise use the parent (ie. this)
            if belike_path:
                try:
                    belike_object = self.restrictedTraverse(belike_path)
                    metalmacro = belike_path.metalobjectid
                except:
                    metalmacro = self.metalobjectid
            else:
                metalmacro = self.metalobjectid

            
        addspace = self
        if addspace.getId() == 'index_html':
            addspace = aq_parent(aq_inner(addspace))
        adder = addspace.manage_addProduct['FriedDocument'].manage_addFriedDocument
        obj = adder(id, title, metalmacro, belike_path=belike_path,
                    show_in_nav=show_in_nav)
        
        slotnames = obj.manage_getSlots()
        for slotname in slotnames:
            if slotname not in ('body',):
                continue
            slot_info = obj._getSlotInfo(slotname)
            if slot_info['wysiwyg'] and slot_info['format']=='html' \
              and slot_info['editable'] and not slot_info['raw']:
                # Warning! This slot is completely empty which will 
                # make it very hard to edit on the first /editable.
                # Add some simple data
                slot_info['raw'] = u'<p>&nbsp;</p>'
                obj._saveSlotInfoPlain(slotname, slot_info)
                obj._cook()
                
        self.http_redirect(self.absolute_url()+'/manageable',
                           msg="Document added")



    ##
    ## Access rights
    ## Userfriendly wrappers around permission management
    ##
    
    def getViewPermissionRoles(self):
        """ return a list of roles who can view this document """
            
        permissions = self.ac_inherited_permissions(1)
        permissions = [p for p in permissions if p[0] == 'View']

        name, value = permissions[0] #permissions[0][1]
        p=Permission(name, value, self)
        roles = p.getRoles(default=[])
        if isinstance(roles, basestring):
            roles = [roles]
        
        # note to self, to set the roles, try p.setRoles([...])
        if 'Anonymous' in roles:
            return []
        else:
            return roles
    
    def getAllAdHocRoles(self):
        """ reutn all groups """
        roles = list(self.valid_roles())
        if 'Owner' in roles:
            roles.remove('Owner')
        if 'Anonymous' in roles:
            roles.remove('Anonymous')
        #if 'Authenticated' in roles:
        #    roles.remove('Authenticated')
        return roles
    
    
    def isAccessProtected(self):
        """ return True if user Anonymous can't View this document """
        rs = self.getViewPermissionRoles()
        if 'Anonymous' in rs:
            rs.remove('Anonymous')
            
        return bool(rs)
        
    security.declareProtected(MANAGE_DOCUMENT, 'setDocumentAccessRights')
    def setDocumentAccessRights(self, make_public, view_roles=None, REQUEST=None):
        """ set the View permission to certain roles only. 
        If the say they want to make it public, that means there should be
        absolutely no special roles needed to view the document the 
        aquired things should be on. 
        If the select to make it private, the default role is 'Authenticated'
        unless the specify exactly what they want. 
        """
        permissions = self.ac_inherited_permissions(1)
        permissions = [p for p in permissions if p[0] == 'View']
        name, value = permissions[0][:2]
        p = Permission(name, value, self)
        
        acquire = isinstance(p.getRoles(default=[]), list)
        
        if make_public:
            p.setRoles([])
        else:
            if not view_roles:
                view_roles = 'Authenticated'
            p.setRoles(tuple(view_roles))
            # need to make it not acquire
            

        if REQUEST:
            msg = "Access rights changes saved"
            #url = self.absolute_url()+'/manageable?msg=%s' % msg
            #if hasattr(self, 'getRandomString'):
            #    url += '&randr=%s' % self.getRandomString()
            #REQUEST.RESPONSE.redirect(url)
            self.http_redirect(self.absolute_url()+'/manageable',
                               msg=msg, randr=self.getRandomString())
            

    def getUnicodeEncoding(self, default='utf8'):
        """ return the encoding you want to use for the documents.
        This is a zope property we expect to inherit via acquisition.
        """
    
        enc = getattr(self, 'frieddocument_encoding', default)
        if not enc:
            enc = default
        return enc
    
    security.declareProtected(VMS, 'manageable')
    manageable = PageTemplateFile('zpt/manageable', globals())
    
    security.declareProtected(VMS, 'manageable_objectlist')
    manageable_objectlist = PageTemplateFile('zpt/objectlist', globals())

    edit_image_form = PageTemplateFile('zpt/edit_image_form', globals())
    access_rights_form = PageTemplateFile('zpt/access_rights_form', globals())
    add_document_form = PageTemplateFile('zpt/add_document_form', globals())
    add_picture_form = PageTemplateFile('zpt/add_picture_form', globals())
    edit_picture_form = PageTemplateFile('zpt/edit_picture_form', globals())

    add_file_form = PageTemplateFile('zpt/add_file_form', globals())
    edit_file_form = PageTemplateFile('zpt/edit_file_form', globals())
    
    # for versioning
    manage_viewVersioningDifference = PageTemplateFile('zpt/view_versioning_difference',
                                                       globals())
    manage_viewVersioningFrame = PageTemplateFile('zpt/view_versioning_frame',
                                                  globals())
                                                  
    manage_viewSlotStraight = PageTemplateFile('zpt/view_slot_straight', globals())
    manage_viewSlotStraightDiffed = PageTemplateFile('zpt/view_slot_straight_diffed', globals())
    
    ## templates within
    show_revision_undo_form = DTMLFile('dtml/show_revision_undo_form', globals(), 
                            __name__='show_revision_undo_form')
    
    manage_Basic = DTMLFile('dtml/basic', globals(), 
                            __name__='manage_Basic')
                            
    manage_UndoOptions = DTMLFile('dtml/undooptions', globals(), 
                            __name__='manage_UndoOptions')
                            
                            
    manage_Advanced = DTMLFile('dtml/advanced', globals(),
                               __name__='manage_Advanced')

    manage_Options = DTMLFile('dtml/options', globals(),
                               __name__='manage_Options')
                               
    #manage_Library = DTMLFile('dtml/library', globals(),
    #                          __name__='manage_Library')

    manage_SlotFixer = DTMLFile('dtml/slotfixer', globals(), 
                            __name__='manage_SlotFixer')
                            

                              
stylesheet = DTMLFile('dtml/stylesheet.css', globals())
setattr(FriedDocument, 'stylesheet.css', stylesheet)

InitializeClass(FriedDocument)
