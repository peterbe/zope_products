# -*- coding: iso-8859-1 -*-

##
## Files
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
from DocumentTemplate import sequence
from OFS.Image import File as OFSFile
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from OFS.PropertyManager import PropertyManager
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Acquisition import aq_inner, aq_parent

# Our friend...
from Products.FriedZopeBase.Bases import HomepageBTreeBase, SimpleItemBaseCatalogAware
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import unicodify, internationalizeID

# Product
from Constants import *
import Utils

#-------------------------------------------------------------------------------

manage_addFilesContainerForm = PTF('zpt/addFilesContainerForm', globals())

def manage_addFilesContainer(dispatcher, id, title=u'', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
    
    id = id.strip()
    title = title.strip()
    if id == "":
        id = internationalizeID(title)
        id = id.replace(' ','-')
    title = unicodify(title)
        
    instance = FilesContainer(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    object.DeployStandards()
    
    if REQUEST is not None:
        if REQUEST.get('goto_after'):
            url = REQUEST.get('goto_after')
        else:
            url = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(url)
        

#-----------------------------------------------------------------------------


class FilesContainer(HomepageBTreeBase):
    """ FilesContainer """
    
    meta_type = METATYPE_FILESCONTAINER
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    
    def __init__(self, id, title=u''):
        """ init """
        self.title = unicodify(title)
        apply(HomepageBTreeBase.__init__, (self, id), {})
        
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def countFiles(self):
        """ return how many there are """
        return len(self.objectValues(METATYPE_FILE))
    
    def getFiles(self, howmany=9999, filter_publish_date=1,
                       sort=None, reverse=0):
        """ return all the good ones """
        ok = []
        count = 0
        now = DateTime()
        objects = self.objectValues(METATYPE_FILE)
        objects = list(objects)
        if sort:
            objects = sequence.sort(objects, ((sort,),))

        if not reverse:
            objects.reverse()

        for attachment in objects:
            if not filter_publish_date or attachment.getPublishDate() <= now:
                count += 1
                if count > howmany:
                    break
                yield attachment
                
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deleteFile')
    def deleteFile(self, id, REQUEST=None):
        """ show confirmation page or really delete """
        assert getattr(self, id).meta_type == METATYPE_FILE
        self.manage_delObjects([id])

        if REQUEST is not None:
            msg = "File deleted"
            url = self.absolute_url()+'/FileManagement'
            self.http_redirect(url, msg=msg)

    def getFileIconpath(self, filename):
        """ Try to find a suitable file icon """
        default = '/misc_/OFSP/File_icon.gif'
        icon_location = '/misc_/%s' % self.ProjectName()
        extension = filename.lower()[filename.rfind('.')+1:]
        if ICON_ASSOCIATIONS.has_key(extension):
            return '%s/%s'%(icon_location, ICON_ASSOCIATIONS[extension])
        else:
            return default

        
    
    #security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'FileManagement')

templates = ('zpt/FileManagement', 
             'zpt/deleteFileForm',
            )
addTemplates2Class(FilesContainer, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'FileManagement')
security.apply(FilesContainer)


InitializeClass(FilesContainer)
        
        
#-------------------------------------------------------------------------------

manage_addFileForm = PTF('zpt/addFileForm', globals())

def manage_addFile(dispatcher, title, file, fileid='',
                            abstract=u'', REQUEST=None):
    """ create """

    dest = dispatcher.Destination()
    if not fileid:
        filename = getattr(file, 'filename', '')
        fileid=filename[max(filename.rfind('/'),
                        filename.rfind('\\'),
                        filename.rfind(':'),
                        )+1:]
        filid = fileid.replace('&','-and-')
        
    title = unicodify(title)
    abstract = unicodify(abstract)

    instance = File(fileid, title, file, abstract=abstract.strip())
    dest._setObject(fileid, instance)
    object = dest._getOb(fileid)
    object.DeployStandards()
    object._cook()

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/FileManagement')


class File(OFSFile, SimpleItemBaseCatalogAware):
    """ File """
    
    meta_type = METATYPE_FILE
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string','mode':'w'},
                 {'id':'abstract',      'type':'text','mode':'w'},
                 {'id':'content_type',  'type':'string','mode':'w'},
                 {'id':'publish_date',  'type':'date','mode':'w'},
                 {'id':'create_date',   'type':'date','mode':'r'},
                 )
                
                
    this_package_home = package_home(globals())
    

    def __init__(self, id, title, file, abstract=u'', abstract_display_format='html',
                 content_type='', precondition='',
                 publish_date=None):
        """ init """
        self.abstract = abstract
        self.abstract_display_format = abstract_display_format
        self._rendered_abstract = u''
        if not publish_date:
            publish_date = DateTime()
        elif isinstance(publish_date, basestring):
            publish_date = DateTime(publish_date)
        self.publish_date = publish_date
        self.create_date = DateTime()
        apply(OFSFile.__init__, (self, id, title, file),
              {'content_type':content_type,
               'precondition':precondition})
    
        
        
    def getId(self):
        """ return id from base OFS File """
        return self.id()

    def getTitle(self):
        return self.title or self.getId()
    
    def getTitle_ascii(self):
        """ return getTitle() ascii encoded """
        return internationalizeID(self.getTitle())

    def getAbstract(self):
        return self.abstract
    
    def getAbstractDisplayFormat(self):
        return self.abstract_display_format

    def showAbstract(self):
        return self._rendered_abstract

    def getPublishDate(self):
        return self.publish_date

    def showPublishDate(self, fmt="%Y-%m-%d %H:%M"):
        return self.getPublishDate().strftime(fmt)

    def isPublished(self):
        """ true if less than now """
        return self.getPublishDate()<=DateTime()


    security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editFile')
    def editFile(self, title, abstract, new_file=None,
                           publish_date=None, REQUEST=None):
        """ save changes """
        self.title = unicodify(title.strip())
        self.abstract = unicodify(abstract.strip())
        if publish_date is not None:
            if not publish_date:
                raise "DateTimeError", "publish_date can not be blank"
            elif self.same_type(publish_date, 's'):
                self.publish_date = DateTime(publish_date)
            else:
                assert self.same_type(publish_date, DateTime())
                self.publish_date = publish_date

        if new_file is not None:
            if self.isFile(new_file):
                self.manage_upload(new_file)

        self._cook()

        if REQUEST is not None:
            msg = "New details saved"
            url = self.absolute_url()+'/editFileForm'
            self.http_redirect(url, msg=msg)
    
    def getFileInfo(self):
        """ return a nice dictionary of information about this file """
        d = {}
        d['content_type'] = self.content_type
        d['size'] = self.size
        d['size_nice'] = self.ShowFilesize(self.size)
        d['icon_nice'] = self.icon
        if 1:#try:
            d['icon_nice'] = self.getFileIconpath(self.getId())
        else:#except:
            pass

        return d
            
    def _cook(self):
        """ prepare the _rendered_abstract """
        text, fmt = self.getAbstract(), self.getAbstractDisplayFormat()
        text = unicodify(text)
        self._rendered_abstract = self.ShowText(text, fmt)


    security.declareProtected('View', 'searchable_text')
    def searchable_text(self):
        """ instead of a class instance attribute for the ZCatalog
        to work on we use this. It's a class method that returns all the text 
        of all slots' raw text without any HTML tags. """
        any_tag_regex = re.compile("<.*?>")
        text = self.getAbstract()
        text = any_tag_regex.sub("", text)
        return text
    
    security.declareProtected('View', 'searchable_text_ascii')
    def searchable_text_ascii(self):
        """ return the value of searchable_text() ASCII encoded """
        return internationalizeID(self.searchable_text())
    

    def index_object(self):
        """A common method to allow Findables to index themselves."""
        path = '/'.join(self.getPhysicalPath())
        idxs = ['id','title','searchable_text','path']
        self.getCatalog().catalog_object(self, path, idxs=idxs)
    

templates = ('zpt/editFileForm',
            )
addTemplates2Class(File, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editFileForm')
security.apply(File)

                
InitializeClass(File)
        
        
