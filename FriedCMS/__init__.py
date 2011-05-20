##
## FriedCMS
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##
import os, sys, re

from Globals import package_home

from Products.FriedZopeBase.Zope import registerImages, registerJSFiles, registerCSSFiles
from Products.FriedZopeBase.Zope import registerImage
from Products.FriedZopeBase.Utils import uniqify, anyTrue

import Homesite
import News
import Files
import Blogs
import Module
import UserFolder
import Page
import FAQ

from Constants import ICON_ASSOCIATIONS

_this_home = package_home(globals())

# Some functions that helps us filter through to the right
# kind of files.
isimage = lambda x: anyTrue(x.lower().endswith, ('jpg','png','gif'))
isjsfile = lambda x: x.lower().endswith('.js') and not x.startswith('.#')
iscssfile = lambda x: x.lower().endswith('.css') and not x.startswith('.#')


IMAGES = [x for x 
            in os.listdir(os.path.join(_this_home, 'images'))
            if isimage(x)]
IMAGES = tuple(uniqify(list(IMAGES)))

JS_FILES = [x for x 
              in os.listdir(os.path.join(_this_home, 'js'))
              if isjsfile(x)]
JS_FILES = tuple(uniqify(list(JS_FILES)))


CSS_FILES = [x for x 
               in os.listdir(os.path.join(_this_home, 'css'))
               if iscssfile(x)]
CSS_FILES = tuple(uniqify(list(CSS_FILES)))


          
import OFS
          
def initialize(context):
    """ Initialize product """
    try:
        context.registerClass(
            Homesite.Homepage,
            constructors = (
                Homesite.manage_addHomepageForm,
                Homesite.manage_addHomepage
                ),
            icon = "www/homepage_icon.gif"
        )
        
        context.registerClass(
            News.NewsContainer,
            constructors = (
                News.manage_addNewsContainerForm,
                News.manage_addNewsContainer
                ),
            icon = "www/newscontainer_icon.gif"
        )
        
        context.registerClass(
            News.NewsItem,
            constructors = (
                News.manage_addNewsItemForm,
                News.manage_addNewsItem,
                News.manage_suggestNewsItemId,
                ),
            icon = "www/newsitem_icon.gif"
        )        
        
        context.registerClass(
            Files.FilesContainer,
            constructors = (
                Files.manage_addFilesContainerForm,
                Files.manage_addFilesContainer
                ),
            icon = "www/filescontainer_icon.gif"
        )
        
        context.registerClass(
            Files.File,
            constructors = (
                Files.manage_addFileForm,
                Files.manage_addFile
                ),
            icon = "www/file_icon.gif"        
        )
        
        context.registerClass(
            Blogs.BlogContainer,
            constructors = (
                Blogs.manage_addBlogContainerForm,
                Blogs.manage_addBlogContainer
                ),
            icon = "www/blogcontainer_icon.gif"
        )
        
        context.registerClass(
            Blogs.BlogItem,
            constructors = (
                Blogs.manage_addBlogItemForm,
                Blogs.manage_addBlogItem,
                Blogs.manage_suggestBlogItemId,
                ),
            icon = "www/blogitem_icon.png"
        )
        
        context.registerClass(
            Module.Module,
            constructors = (
                Module.manage_addModuleForm,
                Module.manage_addModule,
                ),
            icon = "www/module_icon.gif"
        )
        
        context.registerClass(
            UserFolder.FriedCMSUserFolder,
            constructors = (
                UserFolder.manage_addUserFolder,
                ),
            icon = "www/userfolder_icon.gif"
        )   
        
        context.registerClass(
            Page.Page,
            constructors = (
                Page.manage_addPageForm,
                Page.manage_addPage,
                ),
            icon = "www/page_icon.gif"
        )
        	
        context.registerClass(
            FAQ.FAQContainer,
            constructors = (
                FAQ.manage_addFAQContainerForm,
                FAQ.manage_addFAQContainer,
                ),
            icon = "www/faqcontainer_icon.gif"
        )
        
        context.registerClass(
            FAQ.FAQ,
            constructors = (
                FAQ.manage_addFAQForm,
                FAQ.manage_addFAQ,
                ),
            icon = "www/faq_icon.gif"
        )
        
        product = OFS.misc_.misc_.FriedCMS
        
        registerImages(product, IMAGES, globals(), rel_path='images')
        registerJSFiles(product, JS_FILES, globals())
        registerCSSFiles(product, CSS_FILES, globals())

        icons = uniqify(ICON_ASSOCIATIONS.values())
        for icon in icons:
            registerImage(product, icon, epath='icons', Globals=globals())
        
    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb
