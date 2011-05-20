# -*- coding: iso-8859-1 -*-

##
## FriedCMS
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##

# python
import os, re, sys
from urlparse import urlparse

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Acquisition import aq_inner, aq_parent

# Our friend...
from Products.FriedZopeBase.Bases import HomepageOrderedBaseCatalogAware, HomepageBase
from Products.FriedZopeBase.Bases import SimpleItemBaseCatalogAware, HomepageBTreeBase

from Products.FriedZopeBase import Utils as FriedUtils
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote
from Products.FriedZopeBase.feedcreator import Feed as RSSFeed, Item as RSSItem
from Products.FriedZopeBase.Utils import unicodify, html_quote

# Product
from Constants import *
import Utils
from UserFolder import manage_addUserFolder
from Page import PageContainer

#-----------------------------------------------------------------------------

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())
    
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()


DISPLAY_REGEX = re.compile('^display-(tiny|thumbnail|small|xsmall|medium|large|xlarge)$')
#-------------------------------------------------------------------------------

manage_addHomepageForm = DTMLFile('dtml/addHomepageForm', globals())
def manage_addHomepage(dispatcher, id, title=u'', REQUEST=None):
    """ create instance """
    dest = dispatcher.Destination()

    title = unicodify(title)
    
    instance = Homepage(id, title)
    dest._setObject(id, instance)
    site = dest._getOb(id)
    site.DeployStandards()
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
    else:
        return site
        


#-----------------------------------------------------------------------------

class Empty:
    pass

class Homepage(HomepageOrderedBaseCatalogAware, PageContainer):
    """ Homepage """
    
    meta_type = METATYPE_HOMEPAGE
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'ustring', 'mode':'w'},
                 {'id':'longtitle',     'type':'ustring', 'mode':'w'},
                 {'id':'webmasteremail','type':'string',  'mode':'w'},
                 {'id':'webmastername', 'type':'ustring', 'mode':'w'},
                 {'id':'developer_email','type':'string', 'mode':'w'},
                 {'id':'developer_name', 'type':'ustring','mode':'w'},
                 {'id':'menu_items',     'type':'lines',  'mode':'w'},
                 {'id':'always_metalmacro', 'type':'string', 'mode':'w'},
                 {'id':'always_belike', 'type':'string', 'mode':'w'},
                 {'id':'fried_management_modules', 'type':'lines', 'mode':'w'},
                 {'id':'breadcrumbs_omit_ids', 'type':'lines', 'mode':'w'},
                 {'id':'breadcrumbs_home_title', 'type':'string', 'mode':'w'},
                 )

    manage_options = HomepageOrderedBaseCatalogAware.manage_options[:3] + (
                     {'label':'Menu items', 'action':'manage_MenuItems'},
                     ) + HomepageOrderedBaseCatalogAware.manage_options[3:]
                     
    this_package_home = package_home(globals())

    # legacy
    menu_items = []
    always_metalmacro = ''
    always_belike = ''
    fried_management_modules = []
    breadcrumbs_omit_ids = []
    breadcrumbs_home_title = 'Home'
    
    def __init__(self, id, title=''):
        """ init """
        self.id = id
        self.title = title
        self.longtitle = title
        self.webmasteremail = DEFAULT_WEBMASTER_EMAIL
        self.webmastername = DEFAULT_WEBMASTER_NAME
        self.developer_email = DEFAULT_DEVELOPER_EMAIL
        self.developer_name = DEFAULT_DEVELOPER_NAME
        self.menu_items = []
        self.always_metalmacro = ''
        self.always_belike = ''
        self.fried_management_modules = ('News','Files','Blogs','Users')
        
    def getFriedModules(self):
        """ return which management modules to use """
        default = ('News','Files','Blogs','Users')
        r = getattr(self, 'fried_management_modules', default)
        assert isinstance(r, (tuple, list)), \
        "fried_management_modules not a list or tuple"
        
        r = [x.strip() for x in list(r) 
             if not x.strip().startswith('#')]
        
        return tuple(r)
        
    def ProjectName(self):
        """ name of the project """
        return PROJECT_NAME

    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getWebmasterName(self):
        return self.webmastername

    def getWebmasterEmail(self):
        return self.webmasteremail

    def getWebmasterFromfield(self):
        """ return webmastername and email """
        name = self.getWebmasterName()
        email = self.getWebmasterEmail()
        if name:
            return "%s <%s>" % (name, email)
        else:
            return email

    def getDeveloperEmail(self):
        """ return developer_email or getWebmasterEmail """
        try:
            return self.developer_email
        except AttributeError:
            return self.getWebmasterEmail()

    def getDeveloperName(self):
        """ return developer_name or getWebmasterName """
        try:
            return self.developer_name
        except AttributeError:
            return self.getWebmasterName()

    def getDeveloperFromfield(self):
        """ combine developer_name and developer_email """
        if self.getDeveloperName():
            return "%s <%s>"%(self.getDeveloperName(), 
                              self.getDeveloperEmail())
        else:
            return self.getDeveloperEmail()

        
    def getRootDocuments(self, include_index_html=False):
        """ return all the Fried Documents that are in the root """
        return self.getSubDocuments(self.getRoot(), include_index_html=include_index_html)
        
    def getSubDocuments(self, base=None, include_index_html=False):
        """ return all the documents here """
        if base is None:
            base = self
        user = getSecurityManager().getUser()
        
        for document in base.objectValues('Fried Document'):
            if document.showInNav():
                if document.getId() == 'index_html' and not include_index_html:
                    continue
                if not user.has_permission('View', document):
                    continue
                
                yield document
        
        
    def getMenuItems(self, base=None):
        """ return menu_items """
        if base:
            # only look up the property sub_menu_items in the acquisition free base
            aq_base = getattr(base, 'aq_base', base)
            return getattr(aq_base, 'menu_items', [])
        else:
            return self.REQUEST.PARENTS[0].menu_items
    
    def getMenuItemObjects(self, base=None):
        """ return a list of objects.
        A nifty wrapper around getMenuItems() """
        lookin = self.REQUEST.PARENTS[0]
        if base:
            lookin = base
            
        items = self.getMenuItems(base=base)
        for e in self.getMenuItems(base=base):
            if hasattr(lookin, e):
                yield getattr(lookin, e)
        
    
    def getMenuItemOptions(self):
        """ return all pages we might want to link to """
        values = self.objectValues(['Fried Document','Page Template','Folder'])
        _bad_ids = ('images','HeaderFooter','index_html')
        
        values = [x for x in values if x.getId() not in _bad_ids]
        return values
    
    def manage_setMenuItems(self, menu_items, REQUEST=None):
        """ set the menu_items """
        if isinstance(menu_items, basestring):
            menu_items = menu_items.split()
        menu_items = [x.strip() for x in menu_items if x.strip()]
        self.menu_items = menu_items
        if REQUEST:
            self.http_redirect('manage_MenuItems', manage_tabs_message='Saved')
        
        
    def getHTMLTitle(self):
        """ return a nice suitable title """
        roottitle = self.getRoot().title_or_id()
        try:
            here = self.REQUEST.PARENTS[0]
            try:
                thistitle = here.title_or_id()
                try:
                    base = getattr(here, 'aq_base', here)
                    if hasattr(base, 'getTitleTag'):
                        thistitle = base.getTitleTag()
                    elif hasattr(base, 'getTitle'):
                        thistitle = base.getTitle()
                except:
                    pass
            except:
                try:
                    thistitle = here.getTitle()
                except:
                    thistitle = roottitle


            if roottitle == thistitle:
                return roottitle
            else:
                return "%s - %s"%(thistitle, roottitle)
        except:
            return roottitle

    def getBreadcrumbs(self):

        ROOT_ID = self.getRoot().getId()

        def showBreadcrumbObj(obj):
            # pending usage :)
            return 1

        def getBreadcrumbRep(o, onlytext=0):
            """ depending on what object it is, display it
            differently """
            a = o.absolute_url()
            if o.getId() == ROOT_ID:
                t = self.breadcrumbs_home_title
            else:
                t = html_quote(o.title_or_id())
            if onlytext:
                return t
            else:
                return '<a href="%s">%s</a>'%(a, t)

        objects = []

        for each in self.REQUEST.PARENTS:
            
            objects.append(each)
            if each.getId() == ROOT_ID:
                break
            
        links = []
        objects.reverse()
        for object in objects:
            if object.getId() not in self.breadcrumbs_omit_ids:
                if showBreadcrumbObj(object):
                    if object == objects[-1]:
                        representation = getBreadcrumbRep(object, 1)
                    else:
                        representation = getBreadcrumbRep(object)
                    links.append(representation)
                
        return links
        
    def getRoot(self):
        """ return root object """
        mtype = METATYPE_HOMEPAGE
        r = self
        c =0
        
        while r.meta_type != mtype:
            r = aq_parent(aq_inner(r))
            c+=1
            if c>20:
                return None
            if not hasattr(r, 'meta_type'):
                break
        return r

    
    def getRootURL(self):
        """ return root's absolute_url """
        return self.getRoot().absolute_url()
    
    def getRootURLRelative(self):
        """ similar to getRootURLPath() but if the result is '/' we just return '' """
        r = self.getRoot().absolute_url_path()
        if r =='/':
            return ''
        return r
    
        
    def getRootURLPath(self):
        """ return root's absolute_url_path """
        return self.getRoot().absolute_url_path()
        
    security.declareProtected(VMS, 'DeployStandards')
    def DeployStandards(self, clean=0, REQUEST=None):
        """ Deploy standards """
        # Create ZCatalog
        self.InitZCatalog()
        dels = []
        if clean:
            dels = []
        if dels:
            self.manage_delObjects(dels)
        root = self.getRoot()
        standards_home = os.path.join(package_home(globals()), 'standards')
        if os.path.isdir(standards_home):
            self._deployImages(root, standards_home, clean=clean)
        self.UpdateCatalog()
        
        #add acl_users
        if not hasattr(self,'acl_users'):
            manage_addUserFolder(self)

        if REQUEST is not None:
            url = REQUEST.URL1+'/manage_AdvancedManagement'
            url += '?manage_tabs_message=Standards+Deployed'
            REQUEST.RESPONSE.redirect(url)

        
    security.declareProtected(VMS, 'InitZCatalog')
    def InitZCatalog(self, REQUEST=None):
        """ create a ZCatalog called 'Catalog' and change its properties
        accordingly """
        t = {}

        if not ID_ZCATALOG in self.objectIds('ZCatalog'):
            self.manage_addProduct['ZCatalog'].manage_addZCatalog(ID_ZCATALOG,'')
        zcatalog = self.getCatalog()
        indexes = zcatalog._catalog.indexes

        try:
            zcatalog._catalog.addColumn('meta_type')
        except:
            pass

        if not hasattr(zcatalog, 'Lexicon'):
            script = zcatalog.manage_addProduct['ZCTextIndex'].manage_addLexicon

            wordsplitter = Empty()
            wordsplitter.group = 'Word Splitter'
            wordsplitter.name = 'HTML aware splitter'

            casenormalizer = Empty()
            casenormalizer.group = 'Case Normalizer'
            casenormalizer.name = 'Case Normalizer'

            stopwords = Empty()
            stopwords.group = 'Stop Words'
            stopwords.name = 'Remove listed and single char words'

            script('Lexicon', 'Default Lexicon',
            [wordsplitter, casenormalizer, stopwords])
            
        add = ('id','url')
        for adder in add:
            if not indexes.has_key(adder):
                zcatalog.addIndex(adder, 'FieldIndex')
                
        if not indexes.has_key('path'):
            zcatalog.addIndex('path', 'PathIndex')

                
        # One day I need to look into UnicodeLexicon.
        # It's a Lexicon that supports Unicode without 
        # having to fiddle too much with the zope's locale.
        # Current problem (22 Aug 2006) is that UnicodeLexicon
        # requires GenericSetup. That might be a bug. 

        zctextindexes = (('title','getTitle_ascii'),
                         ('searchable_text','searchable_text_ascii'),
                         #('abstract','abstract'),
                         #('body','body'),
                         #('description','description')
                         )
        for idx, attributes in zctextindexes:
            extras = Empty()
            extras.doc_attr = attributes
            # 'Okapi BM25 Rank' is good if you match small search terms
            # against big texts. 
            # 'Cosine Rule' is useful to match similarity between two texts
            extras.index_type = 'Okapi BM25 Rank'
            extras.lexicon_id = 'Lexicon'

            if not indexes.has_key(idx):
                zcatalog.addIndex(idx, 'ZCTextIndex', extras)

        add=()
        for adder in add:
            if not indexes.has_key(adder):
                zcatalog.addIndex(adder, 'KeywordIndex')

        if REQUEST is not None:
            url = REQUEST.URL1+'/manage_AdvancedManagement'
            url += '?manage_tabs_message=Catalog+initialized'
            REQUEST.RESPONSE.redirect(url)

    security.declareProtected(VMS, 'UpdateCatalog')
    def UpdateCatalog(self, REQUEST=None):
        """ Re-catalog all objects that can be cataloged """
        catalog = self.getCatalog()
        catalog.manage_catalogClear()

        root = self.getRoot()
        count = 0
        
        count += self._index_documents(root)

        count += self._index_meta_objects()

        if REQUEST is not None:
            url = REQUEST.URL1+'/manage_AdvancedManagement'
            url += '?manage_tabs_message=Catalog+Updated'
            REQUEST.RESPONSE.redirect(url)
            
    def getCatalog(self):
        """ return the installed HCatalog object """
        catalog = getattr(self,ID_ZCATALOG)
        return catalog

    def _index_documents(self, container):
        """ recursively go throug all documents and index them """
        count = 0
        for document in container.objectValues('Fried Document'):
            document.index_object()
            count += self._index_documents(document)
            count += 1
        return count
            

    def _index_meta_objects(self):
        """ find all the meta objects. Meta objects are instances like News, 
        Files, etc.  """
        count = 0
        for container in self.manage_findNewsContainers():
            for newsitem in container.objectValues(METATYPE_NEWSITEM):
                newsitem.index_object()
                count += 1

        for container in self.manage_findBlogContainers():
            for newsitem in container.objectValues(METATYPE_BLOGITEM):
                newsitem.index_object()
                count += 1
                
        for container in self.manage_findFileContainers():
            for item in container.objectValues(METATYPE_FILE):
                item.index_object()
                count += 1
                
        return count
            
            
    def index_object(self, idxs=[]):
        """A common method to allow Findables to index themselves."""
        path = '/'.join(self.getPhysicalPath())
        self.getCatalog().catalog_object(self, path, idxs=idxs)

    def unindex_object(self):
        """A common method to allow Findables to unindex themselves."""
        self.getCatalog().uncatalog_object('/'.join(self.getPhysicalPath()))
        
    def __before_publishing_traverse__(self, object, request=None):
        """ do things with the request call before proceeding """
        self._set_environ(self.REQUEST)

    def _set_environ(self, REQUEST=None):
        """ set some things in REQUEST """
        disp_re = DISPLAY_REGEX
        
        stack = REQUEST['TraversalRequestNameStack']
        popped = []
        
        stack_copy = []
        if stack:
            stack_copy = stack[:]

            for stack_item in stack_copy:
                found_display = disp_re.findall(stack_item)
                if found_display and found_display[0]:
                    REQUEST.set('display', found_display[0])
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    

    def HEAD(self, REQUEST, RESPONSE):
        """ same as index_html but just returning the headers """
        html = self.index_html(REQUEST)
        RESPONSE.setHeader('Content-Length', len(html))
            
        return ''
        
    ##
    ## Supporting the templates
    ##
    
    def getHeader(self):
        """ return the appropriate Metal header object """
        # Since we might be using CheckoutableTemplates and macro
        # templates are very special we are forced to do the following
        # magic to get the macro 'standard' from a potentially checked
        # out StandardHeader
        try:
            zodb_id = 'HeaderFooter.zpt'
            template = getattr(self, zodb_id, self.HeaderFooter)
        except: #compatibility with old sites
            zodb_id = 'StandardHeaderFooter.zpt'
            template = getattr(self, zodb_id, self.StandardHeaderFooter)
        
        return template.macros['standard']
    
    def getManagementHeader(self):
        """ return the appropriate Metal header object """
        # see the long comment of getHeader()
        zodb_id = 'ManagementHeaderFooter.zpt'
        template = getattr(self, zodb_id, self.ManagementHeaderFooter)
        return template.macros['standard']        
    
    def FriedLogout(self, REQUEST):
        """ try to log the user out """
        raise NotImplemented("This doesn't work yet")
    
        from AccessControl.SecurityManagement import noSecurityManager
        print noSecurityManager.__doc__
        print noSecurityManager()
        return self.http_redirect(self.getRootURL(), randr=self.getRandomString(), 
                                  msg="Logged out")
    
    ##
    ## Finding other Containerish objects
    ## 
    
    def manage_findNewsContainers(self):
        """ return a list of objects that are news containers """
        return self._find_containers(METATYPE_NEWSCONTAINER, self.getRoot())
    
    def manage_findBlogContainers(self):
        """ return a list of objects that are blog containers """
        return self._find_containers(METATYPE_BLOGCONTAINER, self.getRoot())

    def manage_findFileContainers(self):
        """ return a list of objects that are attachment containers """
        return self._find_containers(METATYPE_FILESCONTAINER, self.getRoot())

    def manage_findFAQContainers(self):
        """
        Return a list of objects that are FAQ containers
        """
        return self._find_containers(METATYPE_FAQCONTAINER, self.getRoot())
    
    def _find_containers(self, metatype, startobject):
        foundhere = []
        for path, object in self.ZopeFind(self, obj_metatypes=[metatype], search_sub=1):
            if object.meta_type == metatype:
                foundhere.append(object)
        return foundhere

    
    ##
    ## Misc methods
    ##
    
    def tidyText(self, text, displayformat=None):
        """ fix a news text """
        s = text
        goodbad = {'<br>':'<br />', '<br/>':'<br />',
                   '<hr>':'<hr />', '<hr/>':'<hr />',
                   '</br>':'<br />',
                   }
                   
        for bad, good in goodbad.items():
            s = s.replace(bad, good)

        return s

    def isFile(self, file):
        """ Check if Publisher file is a real file """
        if hasattr(file, 'filename'):
            if getattr(file, 'filename').strip() != '':
                # read 1 byte
                if file.read(1) == "":
                    m = "Filename provided (%s) but not file content"
                    m = m%getattr(file, 'filename')
                    raise "NotAFile", m
                else:
                    file.seek(0) #rewind file
                    return True
            else:
                return False
        else:
            return False
    

    ##
    ## Search
    ##

    def doSearch(self, q, by=['title','searchable_text']):
        """ do they actual search """
        
        catalog = self.getCatalog()
        ok_search_keys = ('id','title','searchable_text')
        if FriedUtils.same_type(by, 's'):
            by = [by]

        by = [x for x in by if x in ok_search_keys]

        if not by:
            return []

        try:
            brains = []
            for searchkey in by:
                brains += apply(catalog.searchResults, (), {searchkey:q})

        except Exception, m:
            self.REQUEST.set('SEARCH_ERROR',m)
            LOG("%s.Homepage" % self.ProjectName(), INFO, "doSearch() error",
                error=sys.exc_info())
            return []

        user = getSecurityManager().getUser()

        now = DateTime()
        
        objects = []
        urls_met = {}
        for brain in brains:
            try:
                object = brain.getObject()
                if object is None:
                    continue
                object_base = getattr(object, 'aq_base', object)
                if not hasattr(object_base, 'searchable_text'):
                    continue
                
                if hasattr(object_base, 'getPublishDate'):
                    if object.getPublishDate() > now:
                        continue
                
                url = object.absolute_url()
                if not urls_met.has_key(url):
                    if user.has_permission('View', object):
                        objects.append(object)
                    urls_met[url] = 1
            except:
                pass

        return objects
        
    
    ##
    ## Error handling
    ## 
    
    def processErrorMessage(self, optionsdict):
        """ do something nice to the error """
        if not PROCESS_ERROR_MESSAGES:
            return ""

        # we can ignore the errors that the ZODB error_log ignores

        error_type = optionsdict.get('error_type',None)
        error_message = optionsdict.get('error_message',None)
        error_log_url = optionsdict.get('error_log_url',None)
        error_tb = optionsdict.get('error_tb',None)
        error_traceback = optionsdict.get('error_traceback',None)
        error_value = optionsdict.get('error_value',None)

        error_type = str(error_type)
        error_value = str(error_value)
        error_log_url = str(error_log_url)
        error_message = str(error_message)

        try:
            e_log = self.error_log
            ignored_exceptions = e_log.getProperties().get('ignored_exceptions', [])
            if error_type in ignored_exceptions:
                return ""
        except:
            LOG(self.__class__.__name__, ERROR, "bad", error=sys.exc_info())

        # Zope will already have pushed this to the error_log but
        # to be extra anal, stick a message in the stupid log file.
        if error_message:
            m = error_message
        else:
            m = "Type: %s\nValue: %s\nerror_log: %s"%\
               (error_type, error_value, error_log_url)
        if error_type != 'NotFound':
            LOG(self.__class__.__name__, PROBLEM, m)

        # Now send a nice email
        subject = "%s error: %s" % (self.ProjectName(), error_type)
        msg = "%s error, %s\n\n" % (self.ProjectName(), DateTime())
        msg += "Type: %s\n" % error_type
        if error_type == 'NotFound':
            msg += "404: %s\n" % self.REQUEST.URL
        else:
            msg += "Value: %s\n" % error_value
            if error_message:
                msg += "Message: %s\n\n" % error_message
            try:
                msg += Utils.dehtmlify(error_traceback)
            except:
                LOG(self.__class__.__name__, ERROR, "bad", error=sys.exc_info())

        msg += "\n\n"
        msg += "Log: %s\n"%error_log_url

        try:
            msg += FriedUtils.REQUEST2String(self.REQUEST)
        except:
            LOG(self.__class__.__name__, ERROR, "bad", error=sys.exc_info())

        try:
            sendto = self.getDeveloperFromfield()
            sendfrom = self.getWebmasterFromfield()
        except:
            LOG(self.__class__.__name__, ERROR, "bad",
                error=sys.exc_info())

        # Send it
        try:
            self.sendEmail(msg, sendto, sendfrom, subject,
                           swallow_errors=True)

        except:
            LOG(self.__class__.__name__, ERROR, "bad", error=sys.exc_info())


        return "" # in case this method is printed in template
    
    
    ## 
    ## Integration with the Javascript CMS banner
    ##
    
    def isLoggedInCMS(self):
        """ return true if the user has a management permission here """
        return self._hasPermission(VMS, self)
        
    def _hasPermission(self, permission, obj):
        user = getSecurityManager().getUser()
        return user.has_permission(permission, obj)
    
    def _getLoggedInUserName(self):
        user = getSecurityManager().getUser()
        if hasattr(user, 'getFullname'):
            return user.getFullname()
        else:
            return str(user)
    
    def cms_js(self, REQUEST, url=None):
        """ wrapper on cms.js template """
        
        if url is None:
            return "//cms.js used incorrectly. It should be cms.js?url=<currentURL>"
        
        kw = dict(options_logged_in=self.isLoggedInCMS(),
                  options_logged_in_name=self._getLoggedInUserName(),
                  )
         
        if url.startswith(self.getRootURL()):
            url = url.replace(self.getRootURL(),'')
        if url.startswith('/'):
            url = url[1:]

            
        on_editable = False
        on_manageable = False
        
        url = url.split('/')
        if 'editable' in url:
            on_editable = True
            url.remove('editable')
        elif 'manageable' in url:
            on_manageable = True
            url.remove('manageable')
        url = '/'.join(url)    
            
        on_object = self.restrictedTraverse(url)
        
        # The reason we're doing this odd meta_type attribute type test
        # is that when you use the URL to get the object it's quite possible
        # that the URL ends in a method (eg. index_html()).
        # XXX Perhaps we need to do a check on the type obj instead of a
        # string matching test of the last element of the URL.
        if not hasattr(on_object, 'meta_type'):
            if url.split('/')[-1] == 'index_html':
                url = '/'.join(url.split('/')[:-1])
                on_object = self.restrictedTraverse(url)

        
        if hasattr(on_object, 'meta_type'):
            if on_object.meta_type == 'Fried Document':
            
                if on_editable:
                    kw['options_on_editable'] = on_object.absolute_url()
                elif on_object.isEditable():
                    kw['options_editable_page'] = on_object.absolute_url()+'/editable'
                
                if on_manageable:
                    kw['options_on_manageable'] = on_object.absolute_url()
                else:
                    kw['options_manageable_page'] = on_object.absolute_url()+'/manageable'
                    
                if on_object.hasUnpublishedChanges():
                    kw['options_unpublished_changes'] = True
                    
                
        if hasattr(self, 'Management') and not getattr(self, 'disable_management_home', False):
            kw['options_management_home'] = self.getRootURL()+'/Management'
            

        return self.cms_js_template(self, REQUEST, **kw)


    ##
    ## Modules integration
    ##
    
    def getExtraModules(self, containers=None):
        """ return all modules available """
        objects = list(self.objectValues(METATYPE_MODULE))
        if containers:
            containers = bool(containers)
            objects = [x for x in objects
                       if containers == bool(x.isContainer())]
        return objects
    
templates = ('zpt/Management',
             'zpt/NewsManagementHome',
             'zpt/BlogManagementHome',             
             'zpt/FileManagementHome',
             'zpt/search',
             'dtml/manage_MenuItems',
             ('zpt/AdvancedManagement', 'manage_AdvancedManagement'),
             'zpt/ManagementHeaderFooter',
             'zpt/DocumentManagementHome',
             ('dtml/cms.js', 'cms_js_template'),
             'zpt/page/PagesManagementHome',
             'zpt/page/deletePageForm',
             'zpt/faq/FAQManagementHome',             
            )
            
addTemplates2Class(Homepage, templates)
                
security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'Management')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'NewsManagementHome')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'BlogManagementHome')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'FileManagementHome')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'DocumentManagementHome')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'PagesManagementHome')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'FAQManagementHome')
#security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'addPageForm')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deletePageForm')
security.apply(Homepage)

setattr(Homepage, 'cms.js', Homepage.cms_js)
InitializeClass(Homepage)
        
        
#-------------------------------------------------------------------------------

        

