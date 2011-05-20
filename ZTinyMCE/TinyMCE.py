##
## ZTinyMCE
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

# python
import os, re, sys
import itertools
import shutil
import tempfile
from time import time

# Zope
from App.Common import rfc1123_date
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Acquisition import aq_inner, aq_parent

# Product
from Constants import *
import Utils
from TemplateAdder import addTemplates2Class
from default_configurations import default_configurations

#-----------------------------------------------------------------------------

    
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()

ss = lambda s: s.strip().lower()

from Utils import anyTrue, debug


def _gzipText(content):
    import cStringIO,gzip
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(None, 'wb', 9, zbuf)
    zfile.write(content)
    zfile.close()
    return zbuf.getvalue()

#-------------------------------------------------------------------------------

manage_addZTinyMCEForm = PTF('zpt/addZTinyMCEForm', globals())
def manage_addZTinyMCE(dispatcher, id, title='', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
        
    instance = TinyMCE(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    object.Update()
    
    # create some default configurations
    maker = object.manage_addProduct['ZTinyMCE'].manage_addZTinyConfiguration
    for config in default_configurations:
        maker(config['name'], configuration=config['config'],
              tinymce_instance_path='/'.join(object.getPhysicalPath()),
              title='Example configuration',
              optimize=True)
    
    if REQUEST is not None:
        if REQUEST.get('addandedit'):
            u = object.absolute_url()+'/manage_workspace'
        else:
            u = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(u)
        

#-----------------------------------------------------------------------------


class TinyMCE(Folder):
    """ TinyMCE of ZTinyMCE """
    
    meta_type = METATYPE_TINYMCE
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                 {'id':'use_gzip',      'type':'boolean', 'mode':'w', 
                  'label':'Use GZip compression'},
                 {'id':'zipfile_used',  'type':'string', 'mode':'r'},
                 {'id':'last_update_date', 'type':'date', 'mode':'r'},
                )
                
    manage_options = Folder.manage_options[:1]+(
                     {'label':'Update', 'action':'manage_Update'},
                     ) + Folder.manage_options[1:]

    this_package_home = package_home(globals())
    
    # legacy: by default this is false
    use_gzip = False
    
    def __init__(self, id, title=''):
        """ init """
        self.id = id
        self.title = title
        self.last_update_date = None
        
        self.zipfile_used = TINYMCE_ZIPFILE
        self.use_gzip = False

    def _updateLastUpdateDate(self):
        self.last_update_date = DateTime()
        
    def _updateZipefileUsed(self):
        self.zipfile_used = TINYMCE_ZIPFILE
        
    def canUpgradeClean(self):
        """ return true if the zipfile used to deploy this ZTinyMCE
        is different from the current one """
        return getattr(self, 'zipfile_used','') != TINYMCE_ZIPFILE
    
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getVersion(self):
        """ return __version__ """
        return __version__

    def doDebug(self):
        """ return DEBUG """
        return DEBUG
    
    def useGZip(self):
        return self.use_gzip

    def doCache(self, hours=10):
        """ set cache headers on this request if not in debug mode """
        if not self.doDebug() and hours > 0:
            response = self.REQUEST.RESPONSE
            response.setHeader('Expires', rfc1123_date(time() + 3600*hours))
            response.setHeader('Cache-Control', 'public,max-age=%d' % int(3600*hours))
    
    
    security.declareProtected(MANAGE_CONFIGURATION, 'Update')
    def Update(self, clean=False, REQUEST=None):
        """ take everything inside the 'tinymce' folder and 
        instanciate in this instance. """

        producthome = package_home(globals())

        try:
            # 1. Create temp dir
            tmpdir = tempfile.mkdtemp()
            
            # 2. unpack tinymce
            Utils.extract(os.path.join(producthome, TINYMCE_ZIPFILE), tmpdir)

            # 3. unpack language pack (if exists)
            lpackage = os.path.join(producthome, LPACKAGE_ZIPFILE)
            if os.path.isfile(lpackage):
                Utils.extract(lpackage, tmpdir)
                          
            # 4. Unravel into zope
            self._uploadInto(tmpdir, self, clean=clean, create_zope_folder=0)

        finally:
            # 5. Remove the unpacked dir
            if os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir)


        self._updateLastUpdateDate()
        if clean:
            self._updateZipefileUsed()
        
        if REQUEST is not None:
            url = self.absolute_url() + '/manage_Update'
            url += '?manage_tabs_message=Update+finished'
            REQUEST.RESPONSE.redirect(url)

    def _uploadInto(self, os_folderpath, zope_container, clean=False, 
                    create_zope_folder=True):
        """ upload all files in 'os_folderpath' into 'zope_container' """
        
        folders_to_skip = 'examples', 'CVS', '_template'
        
        # basename
        assert os.path.isdir(os_folderpath), "os_folderpath is not a filesystem directory"
        basename = os_folderpath.split(os.path.sep)[-1]
        zope_container_base = getattr(zope_container, 'aq_base', zope_container)
        
        if clean and hasattr(zope_container_base, basename):
            zope_container.manage_delObjects([basename])
        
        if create_zope_folder:
            if not hasattr(zope_container_base, basename):
                zope_container.manage_addFolder(basename)

            container = getattr(zope_container, basename)
        else:
            container = zope_container
            
        for o in os.listdir(os_folderpath):
            os_folderpath_o = os.path.join(os_folderpath, o)
            if os.path.isdir(os_folderpath_o):
                if o not in folders_to_skip:
                    self._uploadInto(os_folderpath_o, container, clean=clean)
            else:
                
                content_buffer = open(os_folderpath_o, 'rb')
                
                if clean and hasattr(getattr(container, 'aq_base', container), o):
                    # delete it first 
                    container.manage_delObjects([o])
                    
                if hasattr(getattr(container, 'aq_base', container), o):
                    # it already exists
                    if DEBUG:
                        print "++SKIP++", o, "because it already exists"
                        #print "\t", o in container.objectIds()
                    continue
                    
                if o.endswith('.js'):
                    try:
                        self._uploadJavaScriptDTMLDocument(container, o, content_buffer)
                    except Exception, m:
                        _t = "_uploadJavaScriptDTMLDocument(%r, %r,"
                        _t = _t% (container.absolute_url_path(), o)
                        debug(_t, 1)
                        raise Exception, m
                        
                elif o.endswith('.css'):
                    self._uploadCSSDTMLDocument(container, o, content_buffer)
                elif anyTrue(o.lower().endswith, ('jpg','gif','png')):
                    self._uploadImage(container, o, content_buffer)
                elif anyTrue(o.lower().endswith, ('html','htm')):
                    self._uploadHTMLDTMLDocument(container, o, content_buffer)
                elif DEBUG:
                    print "WHAT ABOUT %s" % os_folderpath_o
                    
# The original _uploadJavaScriptDTMLDocument()        
#    def _uploadJavaScriptDTMLDocument(self, container, filename, data):
#        """ upload as a DTMLDocument with the correct headers """
#        tmpl = '''<dtml-call "doCache(%s)">''' % CACHE_HOURS
#        tmpl += '''<dtml-call "RESPONSE.setHeader('Content-Type','application/x-javascript')">'''
#        content = data.read()
#        content = tmpl + content
#        self._uploadDTMLDocument(container, filename, content)
        
    def _uploadJavaScriptDTMLDocument(self, container, filename, data):
        """ upload as a DTMLDocument with the correct headers """
        tmpl = '''<dtml-call "doCache(%s)">''' % CACHE_HOURS
        tmpl += '''<dtml-call "RESPONSE.setHeader('Content-Type','application/x-javascript')">'''
        filename_gzip = filename.replace('.js','-gzipped.js')
        tmpl += '''<dtml-if "useGZip() and REQUEST['HTTP_ACCEPT_ENCODING'].find('gzip')>-1 and _.getitem(%r)">'''\
                '''<dtml-call "RESPONSE.setHeader('Content-Encoding','gzip')">'''\
                '<dtml-var %s>'\
                '<dtml-else>' %\
                (filename_gzip, filename_gzip)
                
        content = data.read()
        dtml_content = tmpl + content
        dtml_content += '</dtml-if>'
        self._uploadDTMLDocument(container, filename, dtml_content)
        self._uploadFileGzipped(container, filename_gzip, content,
                    content_type='application/x-javascript')
        
    def _uploadFileGzipped(self, container, filename, data, content_type=None):
        container.manage_addFile(filename, title='', file=_gzipText(data),
                                 content_type=content_type)
        

# The original _uploadCSSDTMLDocument()                                 
#    def _uploadCSSDTMLDocument(self, container, filename, data):
#        tmpl = '''<dtml-call "doCache(%s)">''' % CACHE_HOURS
#        tmpl += '''<dtml-call "RESPONSE.setHeader('Content-Type','text/css')">'''
#        content = data.read()
#        content = tmpl + content
#        self._uploadDTMLDocument(container, filename, content)
        
        
    def _uploadCSSDTMLDocument(self, container, filename, data):
        tmpl = '''<dtml-call "doCache(%s)">''' % CACHE_HOURS
        tmpl += '''<dtml-call "RESPONSE.setHeader('Content-Type','text/css')">'''
        filename_gzip = filename.replace('.css','-gzipped.css')
        tmpl += '''<dtml-if "useGZip() and REQUEST['HTTP_ACCEPT_ENCODING'].find('gzip')>-1 and _.getitem(%r)">'''\
                '''<dtml-call "RESPONSE.setHeader('Content-Encoding','gzip')">'''\
                '<dtml-var %s>'\
                '<dtml-else>' %\
                (filename_gzip, filename_gzip)
        
        content = data.read()
        dtml_content = tmpl + content
        dtml_content += '</dtml-if>'
        self._uploadDTMLDocument(container, filename, dtml_content)
        self._uploadFileGzipped(container, filename_gzip, content,
                    content_type='text/css')
        

    def _uploadHTMLDTMLDocument(self, container, filename, data):
        tmpl = '''<dtml-call "doCache(%s)">''' % CACHE_HOURS
        content = data.read()
        content = tmpl + content
        self._uploadDTMLDocument(container, filename, content)
        
    def _uploadDTMLDocument(self, container, filename, content):
        """ create the DTML Document """
        debug("Adding DTMLDocument %r inside %s" % 
              (filename, container.absolute_url_path()))
        container.manage_addDTMLDocument(filename, title='', file=content)
        # XXX We might want to upload the optimized version here too
        
    def _uploadImage(self, container, filename, data):
        """ upload a plain image """
        debug("Adding Image %r inside %s" % 
              (filename, container.absolute_url_path()))
        container.manage_addImage(filename, title='', file=data)
        
    

templates = (#'dtml/something',
             'dtml/manage_Update',
            )
addTemplates2Class(TinyMCE, templates)
                
InitializeClass(TinyMCE)
        
        

    
    
    
