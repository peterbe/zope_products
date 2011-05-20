##
## ThuaWood
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

# python
import os, re, sys, cgi
from random import shuffle
from tempfile import gettempdir
from PIL import Image

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF



# Our friend...
from Products.FriedZopeBase.Bases import HomepageOrderedBaseCatalogAware, HomepageBaseCatalogAware
from Products.FriedZopeBase import Utils as FriedUtils
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote
from Products.FriedZopeBase.Utils import internationalizeID, unicodify
from Products.FriedZopeBase.feedcreator import Item, Feed
# Product
from Constants import *

#-----------------------------------------------------------------------------

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())
    
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()

#-------------------------------------------------------------------------------

        
manage_addBustForm = PTF('zpt/addBustForm', globals())
def manage_addBust(dispatcher, id, bigphoto, littleimage, title, 
                   description=u'', REQUEST=None,
                   redirect_to=None):
    """ create instance """
    
    if not id:
        id = title.replace('&',' o ').strip().replace('  ',' ')
        id = id.replace(' ','-')
        id = internationalizeID(id)
    
    dest = dispatcher.Destination()
        
    instance = Bust(id, title, description=description)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    #object.DeployStandards()
    object.uploadPhoto(bigphoto)
    if getattr(littleimage, 'filename', None):
        object.uploadThumbnail(littleimage)
    else:
        object.convertPhotoToThumbnail()
    
    if REQUEST is not None:
        if redirect_to:
            REQUEST.RESPONSE.redirect(redirect_to)
        else:
            REQUEST.RESPONSE.redirect(REQUEST.URL1+'/BustManagement')
        

#-----------------------------------------------------------------------------


class Bust(HomepageBaseCatalogAware):
    """ Bust of ThuaWood """
    
    meta_type = METATYPE_BUST
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'ustring', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    
    def __init__(self, id, title=u'', description=u''):
        """ init """
        self.id = id
        self.title = unicodify(title)
        self.description = unicodify(description)
        self.is_published = True
        self.create_date = DateTime()
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getDescription(self):
        """ return description """
        return self.description
    
    def showDescription(self):
        """ return description nicely """
        return self.ShowText(self.getDescription())
    
    def isPublished(self):
        """ return is_published """
        return self.is_published
    
    def getCreateDate(self):
        try:
            return self.create_date
        except AttributeError:
            self.create_date = self.bobobase_modification_time()
            return self.bobobase_modification_time()
    
    def uploadPhoto(self, file, id='', REQUEST=None):
        """ upload a photo object """
        if not id:
            id = getattr(file, 'filename')
            ext = id.split('.')[-1]
            id = 'foto.%s' % ext
        adder = self.manage_addProduct['Photo'].manage_addPhoto
        adder(id, '', file, engine='PIL', quality=100)

    def uploadThumbnail(self, file, id='', REQUEST=None):
        """ upload a image object """
        if not id:
            id = getattr(file, 'filename')
            ext = id.split('.')[-1]
            id = 'tumnagel.%s' % ext
        self.manage_addImage(id=id, file=file, title='')
        
    def getThumbnail(self):
        candidates = [x for x in self.objectValues('Image') 
                        if x.getId().startswith('tumnagel')]
        if candidates:
            return candidates[0]
        else:
            return None
        
    def getPhoto(self):
        candidates = [x for x in self.objectValues('Photo') 
                        if x.getId().startswith('foto')]
        if candidates:
            return candidates[0]
        else:
            return None        

        
    def manage_editBust(self, title, description, bigphoto, littleimage,
                        REQUEST=None):
        """ edit bust """
        self.title = unicodify(title)
        self.description = unicodify(description)
        
        big_photo_uploaded = False
        if getattr(bigphoto, 'filename', None):
            self.uploadPhoto(bigphoto)
            big_photo_uploaded = True
        
        if getattr(littleimage, 'filename', None):
            self.uploadThumbnail(littleimage)
        elif big_photo_uploaded:
            self.convertPhotoToThumbnail()
            
        if REQUEST is not None:
            self.http_redirect(self.absolute_url() + '/editBustForm',
                               msg="Sparad")
            
    def convertPhotoToThumbnail(self, max_size=50):
        """ there is a photo, create a thumbnail for it. """
        
        imagefilepath = os.path.join(gettempdir(), self.getPhoto().getId())
        imagefile = open(imagefilepath, 'wb')
        p = self.getPhoto()
        thumbdata = p._original._PILdata()
        imagefile.write(thumbdata.getvalue())
        imagefile.close()
        
        img = Image.open(imagefilepath)
        fmt = img.format
        size_x, size_y = img.size
        ratio = float(size_x)/ size_y
        
        if size_x > size_y:
            # make the lower bound be the y axis
            size_y = max_size
            size_x = int(size_y * ratio)
        else:
            size_x = max_size
            size_y = int(size_x / ratio)
        
        img.thumbnail((size_x, size_y), resample=True)
        cropbox = (0, 0, 50, 50)
        img = img.crop(cropbox)
        
        img.save(imagefilepath, fmt)
        
        thumbimage = open(imagefilepath, 'rb')
        ext = p.getId().split('.')[-1]
        id = 'tumnagel.%s' % ext
        self.uploadThumbnail(file=thumbimage.read(), id=id)

templates = (#'dtml/something',
             'zpt/editBustForm',
            )
addTemplates2Class(Bust, templates)
 
security = ClassSecurityInfo()
security.declareProtected(VMS, 'editBustForm')
security.apply(Bust)

InitializeClass(Bust)


#-----------------------------------------------------------------------------
        
manage_addBustFolderForm = PTF('zpt/addBustFolderForm', globals())
def manage_addBustFolder(dispatcher, id, title, REQUEST=None,
                   redirect_to=None):
    """ create instance """
    
    dest = dispatcher.Destination()
        
    instance = BustFolder(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    #object.DeployStandards()
    
    if REQUEST is not None:
        if redirect_to:
            REQUEST.RESPONSE.redirect(redirect_to)
        else:
            REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
        

#-----------------------------------------------------------------------------


class BustFolder(HomepageOrderedBaseCatalogAware):
    """ Bust of ThuaWood """

    meta_type = METATYPE_BUSTFOLDER
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'ustring', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    
    def __init__(self, id, title=''):
        """ init """
        self.id = id
        self.title = title
        self.create_date = DateTime()
	        
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getBusts(self, howmany=None, sort=None, reverse=False):
        """ return all busts """
        ok = []
        now = DateTime()
        count = 0
        objects = self.objectValues(METATYPE_BUST)
        objects = list(objects)
        if sort == 'random':
            shuffle(objects)
        elif sort:
            #assert None not in objects
            objects = [x for x in objects if x is not None]
            objects = sequence.sort(objects, ((sort,),))

        if reverse:
            objects.reverse()
            
        if howmany:
            howmany = int(howmany)
            assert howmany > 0, "howmany <= 0 :("

        for item in objects:
            count += 1
            if howmany and count > howmany:
                break
            yield item
            
            
    security.declareProtected(VMS, 'manage_deleteBust')
    def manage_deleteBust(self, id, REQUEST=None):
        """ delete a bust """
        obj = getattr(self, id)
        assert obj.meta_type == METATYPE_BUST, "Can only delete Busts"
        
        self.manage_delObjects([id])
        
        if REQUEST is not None:
            return self.http_redirect('BustManagement')
        
    security.declareProtected('View', 'RSS10')
    def RSS10(self, howmany=10, REQUEST=None):
        """ return a RSS feed """
        def u2s(ustr):
            return cgi.escape(ustr).encode('ascii','xmlcharrefreplace')
        
        feed = Feed(self.absolute_url()+'/rss.xml',
                    title=u2s(self.getRoot().getTitle()),
                    description='',
                    language='sv',
                    webmaster='')
                    
        for bust in self.getBusts(howmany=int(howmany), sort='getCreateDate', reverse=1):
            title = u2s(bust.getTitle())
            description = u2s(bust.getDescription())
            thumbnail = bust.getThumbnail()
            ahref = '<a href="%s">%s</a>' % (bust.absolute_url(),
                                             thumbnail.tag())
            description = ahref + ' ' + description
            
            feed.append(Item(title,
                             bust.absolute_url(),
                             description,
                             date=bust.getCreateDate().strftime('%Y-%m-%dT%H:%M')
                             )
                        )
            
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml')
                
        return feed.out().strip()
                    
        
    
templates = (
             'zpt/BustManagement',
             'zpt/deleteBustForm',
            )
addTemplates2Class(BustFolder, templates)

security = ClassSecurityInfo()
security.declareProtected(VMS, 'deleteBustForm')
security.declareProtected(VMS, 'BustManagement')
security.declareProtected('View', 'rss.xml')
security.apply(BustFolder)

setattr(BustFolder, 'rss.xml', BustFolder.RSS10)

InitializeClass(BustFolder)
        
        

