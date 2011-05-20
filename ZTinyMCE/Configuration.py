##
## ZTinyMCE
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

# python
import os, re, sys
from urllib import quote_plus

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from OFS.SimpleItem import SimpleItem
from Acquisition import aq_inner, aq_parent
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface

try:
    import transaction
except ImportError:
    # we must be in an older than 2.8 version of Zope
    transaction = None

# Product
from Constants import *
import Utils
from Utils import ConfigurationError
from TemplateAdder import addTemplates2Class

#-------------------------------------------------------------------------------

manage_addZTinyConfigurationForm = PTF('zpt/addZTinyConfigurationForm', globals())

def manage_addZTinyConfiguration(dispatcher, id, configuration, optimize=False,
                                 tinymce_instance_path=None, title='',
                                 REQUEST=None):
    """ create a ZTinyConfiguration object """
    dest = dispatcher.Destination()
    
    if not tinymce_instance_path:
        tinymce_instance_path = None
    else:
        o = dest.unrestrictedTraverse(tinymce_instance_path)
        assert o.meta_type==METATYPE_TINYMCE, \
        "TinyMCE instance path not to TinyMCE object"
    
    instance = TinyMCEConfiguration(id, title=title, configuration=configuration,
                                    optimize=optimize)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    
    if REQUEST is not None:
        if REQUEST.get('addandedit'):
            u = object.absolute_url()+'/manage_workspace'
        else:
            u = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(u)
    

def manage_findZTinyMCEInstances(self, return_nearest=False):
    """ return a list of all TinyMCE instances we can find """
    all = []
    all.extend(self.objectValues(METATYPE_TINYMCE))
    
    if return_nearest and all:
        return all[0]
    
    parent = aq_parent(aq_inner(self))
    while parent != self:
        if not hasattr(parent, 'meta_type'):
            break
        if not hasattr(parent, 'objectValues'):
            break
        
        all.extend(parent.objectValues(METATYPE_TINYMCE))
        if return_nearest and all:
            return all[0]
        parent = aq_parent(aq_inner(parent))
    if return_nearest:
        return None
    return all

#-------------------------------------------------------------------------------

class TinyMCEConfiguration(SimpleItem):
    """ a configuration is a simply a string that can look something like this:
        mode : "textareas",
        theme : "simple"
        
    Once you have created this configuration object so that it becomes for 
    example 'tinymce_simple.conf' then all you need to do is something like 
    this:
    <script tal:replace="structure here/tinymce_simple.conf"></script>
    in your page and it will take care of everything else for you. 
    """
    
    __implements__ = (WriteLockInterface,)
    
    #icon = 'misc_/ZTinyMCE/configuration_icon.gif' ## xxx: is this line still needed?
    
    meta_type = METATYPE_TINYMCECONFIGURATION
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                 {'id':'optimize',      'type':'bool',   'mode':'w'},
                 
                )
                
    manage_options = ({'label':'Configure', 'action':'manage_Configure'},
                      {'label':'Test configure', 'action':'manage_TestConfiguration'},
                     ) 

                     
    this_package_home = package_home(globals())
    
    def __init__(self, id, title='', configuration='', optimize=False,
                 tinymce_instance_path=None):
        """ init """
        self.id = id
        self.title = title
        self.optimize = bool(optimize)
        
        # ValidConfiguration(..., be_angry=True) will raise errors if there are any
        Utils.ValidConfiguration(configuration, be_angry=True)
        self.configuration = configuration
        
        self.tinymce_instance_path = tinymce_instance_path
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getConfiguration(self):
        """ return configuration """
        return self.configuration
    
    def doOptimize(self):
        """ return optimize """
        return self.optimize
    
    def useOnblurOnfocusHack(self):
        """ return use_onblur_onfocus_patch """
        import warnings
        warnings.warn("OnBlur/OnFocus hack is not no longer needed or used",
                      DeprecationWarning, 2)
    
    def _getTinyMCEInstance(self):
        """ return the TinyMCE instance object we intend to use """
        if self.tinymce_instance_path:
            try:
                return self.unrestrictedTraverse(self.tinymce_instance_path)
            except Exception:
                self.tinymce_instance_path = None
                return self._getTinyMCEInstance()
        else:
            # no tinymce_instance_path set, find a TinyMCE instance
            # and remember that
            
            inst = manage_findZTinyMCEInstances(self, True)
            if inst:
                self.tinymce_instance_path = '/'.join(inst.getPhysicalPath())
                return inst
            else:
                m = "No TinyMCE instance found back recursively.\n"
                m += "Create a ZTinyMCE instance in parent or parent's parent"
                raise AttributeError, m

    def get_size(self):
        """ Used for FTP and ZMI (possibly) """
        return len(self.getConfiguration())

        
    def render(self, **kwargs):
        """ return the HTML necessary to run the TinyMCE """
        if self.doOptimize():
            tinymce_js_file = "tiny_mce.js"
        else:
            tinymce_js_file = "tiny_mce_src.js"
        
        _tinymce_instance = self._getTinyMCEInstance()
        tmpl_start='<script type="text/javascript" src="%s/%s"></script>'
        tmpl = tmpl_start % (_tinymce_instance.tinymce.jscripts.tiny_mce.absolute_url(),
                             tinymce_js_file,
                            )
            
        tmpl += '<script type="text/javascript">\n'\
                'tinyMCE.init({\n'
        if self.doOptimize():
            configuration_string = self.getConfiguration()
            tmpl += ''.join([x.replace(' : ',':') for x in configuration_string.splitlines() 
                               if not x.strip().startswith('//')])
        else:
            tmpl += '\n'.join([x for x in self.getConfiguration().splitlines() 
                               if not x.strip().startswith('//')])
        tmpl = tmpl.strip()
        if tmpl.endswith(','):
            tmpl = tmpl[:-1]
        
        tmpl += '});\n</script>'
        return tmpl
    
    def __call__(self, **kw):
        return self.render(**kw)
    
    def __str__(self, **kw):
        return self.render(**kw)
    
   
    
    def manage_saveConfiguration(self, configuration, title,
                                 optimize=False,
                                 REQUEST=None):
        """ save the configuration """
        
        self.title = title.strip()
        self.optimize = Utils.niceboolean(optimize)
        
        def tidyline(x):
            x = x.rstrip()
            if not x.endswith(',') and not x.endswith('\\'):
                x += ','
            return x
        lines = [tidyline(x) for x in configuration.strip().splitlines() if x.strip()]
        if lines:
            if lines[-1].endswith(','):
                lines[-1] = lines[-1][:-1]
        configuration = '\n'.join(lines)
        try:
            Utils.ValidConfiguration(configuration, be_angry=True)
            configuration_warning = None
        except ConfigurationError, msg:
            configuration_warning = str(msg)
            
        self.configuration = configuration
        
        msg = "Configuration saved"
        
        if REQUEST is not None:
            return self.manage_Configure(self, REQUEST, manage_tabs_message=msg,
                                         configuration_warning=configuration_warning)
            
    ## 
    ## WebDAV
    ##
    
    security.declareProtected('View', 'manage_FTPget')
    def manage_FTPget(self, REQUEST, RESPONSE):
        """ get source for FTP download for ExternalEditor """
        self.REQUEST.RESPONSE.setHeader('Content-Type','text/plain')
        return self.getConfiguration()
    
    
    security.declareProtected(MANAGE_CONFIGURATION, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests 
        for ExternalEditor """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        
        if not REQUEST.get('BODY'):
            if transaction is None:
                get_transaction.abort()
            else:
                # the >2.8 way of doing it
                transaction.get().abort()
            RESPONSE.setStatus(405)
        else:
            body = REQUEST.get('BODY').strip()
            
            try:
                Utils.ValidConfiguration(body, be_angry=True)
                self.configuration = body
            except Utils.ConfigurationError, m:
                LOG("ZTinyMCE", ERROR, "Invalid configuration: %s"%m, error=sys.exc_info())
            except:
                LOG("ZTinyMCE", ERROR, "", error=sys.exc_info())
                
            RESPONSE.setStatus(204)
            return RESPONSE
        
    
        
        
templates = ('dtml/manage_Configure',
             'dtml/manage_TestConfiguration',
             'dtml/test_config_content',
            )
addTemplates2Class(TinyMCEConfiguration, templates)
                
InitializeClass(TinyMCEConfiguration)