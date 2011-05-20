##
## CheckoutableTemplates,
## By Peter Bengtsson, mail@peterbe.com, www.peterbe.com
## Copyright 2003-2005
## License ZPL
##

import os, cPickle, stat, sys, re
from types import DictType, ListType, StringType
from time import time
import marshal
from pprint import pprint
from random import shuffle
from Globals import DTMLFile
from zLOG import LOG, INFO, WARNING
from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent, aq_inner, aq_base
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Constants import *

import logging
logger = logging.getLogger('CheckoutableTemplates')

if DISABLE_CHECKOUTABLETEMPLATES:
    logger.info("CheckoutableTemplates is disabled")


try:
    from slimmer import slimmer, acceptableSyntax
except ImportError:
    def acceptableSyntax(*a, **k):
        return None
    def slimmer(inputtext, *a, **k):
        return inputtext
    
    if DEBUG:
        m = "slimmer not installed. Whitespace optimization disbled."
        m += " (see www.issuetrackerproduct.com)"
        LOG("CheckoutableTemplates", WARNING, m)


try:
    __test_dict={'a':'A'}
    __test_dict.pop('a')
    Python21 = 0
except:
    Python21 = 1
    def dict_popper(dict, key):
        """ simulate what {}.pop() does in Python 2.3 """
        if not dict:
            raise KeyError, 'dict_popper(): dictionary is empty'
        
        if not dict.has_key(key):
            raise KeyError, repr(key)
        
        new_dict = {}
        for k, v in dict.items():
            if k == key:
                value = v
            else:
                new_dict[k] = v
        return value, new_dict
    
    
def debug(debug_output):
    if DEBUG:
        print "CT|",
        if type(debug_output)==StringType:
            print debug_output
        else:
            pprint(debug_output)
        open('output.log','a').write(debug_output.strip()+'\n')
    

_id_junk_regex = re.compile('[\\/\s\.:]')
def _generateIdentifier(basepath, relpath, mtime):
    id = basepath + relpath
    id = _id_junk_regex.sub('', id)
    id = list(id[:3]+id[-3:]+str(mtime)[-5:])
    shuffle(id)
    id = "".join(id)
    return id



def _getAllconfigs():
    raise "NotUsed"


def _readAllConfigs():
    if os.path.isfile(CONFIGFILEPATH):
        try:
            #items, finder = cPickle.load(open(CONFIGFILEPATH))
            items, finder = cPickle.load(open(CONFIGFILEPATH,'rb'))
            #items, finder = marshal.load(open(CONFIGFILEPATH))
        except ValueError, e:
            if str(e) == "unpack list of wrong size":
                # Wohw! the config file is corrupted which could very 
                # much be because it's from an ancient version of
                # CheckoutableTemplates
                return [], {}
        try:
            assert type(items)==ListType, "items is not a list"
            assert type(finder)==DictType, "finder is not a dictionary"
        except AssertionError:
            return [], {}
        
    else:
        items, finder = [], {} # this is how it starts
        
    return items, finder

#def _findConfig(key):
#    """ key can be an identifier or basepath,relpath,filetype """
#    items, finder = _readAllConfigs()
#    if finder.has_key(key):
#        return items[finder.get(key)]
#    else:
#        return None

def _writeAllConfigs(items, finder):
    combined = items, finder
    # save new file
    cPickle.dump(combined, open(CONFIGFILEPATH, 'wb'), -1)
    
    
def _clean_itemlist(itemslist, basepath, relpath, filetype):
    """ return a _new list_ which doesn't have duplicate combinations of
    basepath, relpath and filetype and nothing of the params """
    copy = []
    newfinder = {}
    _template = "%s/%s/%s"
    skip_combo = _template%(basepath, relpath, filetype)
    for each in itemslist:
        combo = _template%(each['basepath'], each['relpath'], each['filetype'])
        if not newfinder.has_key(combo):
            if combo != skip_combo:
                copy.append(each)
                newfinder[combo] = copy.index(each)
        else:
            debug("Duplicate combo: %s"%combo)
            
    return copy, newfinder


def _write2config(basepath, relpath, description, mtime, filetype='DTML'):
    """ save an item serialized file """
    
    items, finder = _readAllConfigs()
    
    key = "%s/%s/%s" % (basepath, relpath, filetype)
    addthis = 1
    item_no = finder.get(key)
    if item_no is None:
        # ah! Nothing in the finder
        addthis = 1
                    
    else:
        try:
            item = items[item_no]
            # we have it already
            addthis = 0
        except IndexError:
            # Ghaa! we're out-of-sync with the finder
            addthis = 1 # force a new addition
            
        # test if we can change our mind based on the mtime
        if not addthis and mtime > item['mtime']: # has changed
            # remove it
            items.pop(item_no)
            if Python21:
                _value, finder = dict_popper(finder, key)
            else:
                finder.pop(key)
            addthis = 1
            
            

    if addthis:
        
        if CLEAN_CHECK: # read Constants.py
            items, finder = _clean_itemlist(items, basepath, relpath, filetype)

        identifier = _generateIdentifier(basepath, relpath, mtime)
        d = {'description':description, 
             'filetype':filetype,
             'relpath':relpath, 
             'basepath':basepath,
             'mtime':mtime, 
             'identifier':identifier
             }
        items.append(d)
        
        item_no = items.index(d)        
        finder[key] = item_no
        finder[identifier] = item_no

        debug("Write new identifier %s"%identifier)
        _writeAllConfigs(items, finder)

        return 1
    else:
        return 0    
    
def write2config(basepath, relpath, description, mtime,
                 filetype='DTML'):
    """ save a config item """
    return _write2config(basepath, relpath, description, mtime,
                         filetype=filetype)


    
class _CTDTMLFile(DTMLFile):
    def __init__(self, name, _prefix=None, **kw):
        " doc string "
        
        description = kw.get('description',kw.get('d',''))
        
        # 'optimize' argument
        optimize = kw.get('optimize', kw.get('opt', None))
        self.optimize = acceptableSyntax(optimize)
            
        if not kw.has_key('uncheckoutable'):
            sep = name[max(name.find('\\'), name.find('/'))]
            self.ctnamesplit = name.split(sep)

            prodpath = _prefix['__name__'].split('.')[:-1]
            prodpath = ".".join(prodpath).replace('.',os.sep)

            basepath = os.path.join(CT_INSTANCE_HOME, prodpath)
            if not os.path.isdir(basepath):
                if os.path.isdir(os.path.join(CT_SOFTWARE_HOME, prodpath)):
                    basepath = os.path.join(CT_SOFTWARE_HOME, prodpath)
                elif os.path.isdir(os.path.join(CT_INSTANCE_HOME, 'Products', prodpath)):
                    basepath = os.path.join(CT_INSTANCE_HOME, 'Products', prodpath)
            
            # first, open file to see how old it is.
            name = name.replace('/', os.sep).replace('\\',os.sep)
            
            t = os.stat(os.path.join(basepath, name+ '.dtml'))
            mtime = t[stat.ST_MTIME]
            
            # if already there there's no point to
            # add it again
            added = write2config(basepath, name, description,
                                 mtime, 'DTML')

            if DEBUG and added:
                LOG(self.__class__.__name__, INFO, name)

        apply(DTMLFile.__init__, (self, name, _prefix), kw)


    def _exec(self, bound_data, args, kw):
        """ Execute the template but first look for one instanciated
        in the ZODB based on the some filename conversion. """

        ctnamesplit = bound_data['self'].ctnamesplit
        if len(self.ctnamesplit) == 1:
            possibletemplate = ctnamesplit[0] + '.dtml'
        else:
            possibletemplate = '.'.join(ctnamesplit[1:]) + '.dtml'
            
        base = bound_data['context']

        if hasattr(base, possibletemplate):
            request = bound_data['context'].REQUEST
            params = (bound_data['context'], request)
            result = apply(getattr(base, possibletemplate), params, kw)
        else:
            result = apply(DTMLFile._exec, (self, bound_data, args, kw))
            
        if self.optimize and OPTIMIZE:
            result = slimmer(result, self.optimize)
            
        return result
    



class _CTPageTemplateFile(PageTemplateFile):
    """ CTPageTemplateFile subclasses PageTemplateFile and
    intercepts the __init__ and the _exec methods """
    
    def __init__(self, name, _prefix=None, **kw):
        """ doc string """
        
        description = kw.get('description',kw.get('d',''))

        # 'optimize' argument
        optimize = kw.get('optimize', kw.get('opt', None))
        self.optimize = acceptableSyntax(optimize)
        
        if not kw.has_key('uncheckoutable'):
            sep = name[max(name.find('\\'), name.find('/'))]
            self.ctnamesplit = name.split(sep)
            
            prodpath = _prefix['__name__'].split('.')[:-1]
            prodpath = ".".join(prodpath).replace('.', os.sep)
            
            basepath = os.path.join(CT_INSTANCE_HOME, prodpath)
            if not os.path.isdir(basepath):
                if os.path.isdir(os.path.join(CT_SOFTWARE_HOME, prodpath)):
                    basepath = os.path.join(CT_SOFTWARE_HOME, prodpath)
                elif os.path.isdir(os.path.join(CT_INSTANCE_HOME, 'Products', prodpath)):
                    basepath = os.path.join(CT_INSTANCE_HOME, 'Products', prodpath)
            
            # first, open file to see how long it is.
            name = name.replace('/', os.sep).replace('\\',os.sep)

            template_path = os.path.join(basepath, name)
            if not os.path.splitext(template_path)[1]:
                template_path += '.zpt'
            
            t = os.stat(template_path)
            mtime = t[stat.ST_MTIME]
            
            added = write2config(basepath, name, description,
                                 mtime, 'ZPT')
            
            if DEBUG and added:
                LOG(self.__class__.__name__, INFO, name)
            
        apply(PageTemplateFile.__init__, (self, name, _prefix), kw)

    def _exec(self, bound_data, args, kw):
        """ doc string """
        if len(self.ctnamesplit) == 1:
            possibletemplate = self.ctnamesplit[0]
        else:
            possibletemplate = '.'.join(self.ctnamesplit[1:])
    
        if not possibletemplate.endswith('.zpt'):
            possibletemplate += '.zpt'
        base = self
        
        if hasattr(base, possibletemplate):
            request = self.REQUEST
            result = apply(getattr(base, possibletemplate), (self, request), kw)
        else:
            result = apply(PageTemplateFile._exec, (self, bound_data, args, kw))
        
        if self.optimize and OPTIMIZE:
            
            try:
                result = slimmer(result, self.optimize)
            except:
                try:
                    err_log = self.error_log
                    err_log.raising(sys.exc_info())
                except:
                    pass
                
            
        return result


if DISABLE_CHECKOUTABLETEMPLATES:
    CTPageTemplateFile = PageTemplateFile
    CTDTMLFile = DTMLFile

else:
    CTPageTemplateFile = _CTPageTemplateFile
    CTDTMLFile = _CTDTMLFile