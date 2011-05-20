#-*- coding: iso-8859-1 -*
##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##
import os

import OFS, App
from Globals import package_home

from Products.FriedZopeBase.Zope import registerImages, registerImage, registerJSFiles, \
                                        registerCSSFiles
from Products.FriedZopeBase.Utils import uniqify, anyTrue
import Homepage

try:
    from slimmer import js_slimmer
except ImportError:
    js_slimmer = None

""" RememberYourFriends website """

isimage = lambda x: anyTrue(x.lower().endswith, ('.jpg','.png','.gif'))
WWW_IMAGES = [x for x 
            in os.listdir(os.path.join(package_home(globals()), 'www'))
            if isimage(x)]
WWW_IMAGES = uniqify(WWW_IMAGES)


isjsfile = lambda x: x.lower().endswith('.js')
JS_FILES = [x for x 
              in os.listdir(os.path.join(package_home(globals()), 'js'))
              if isjsfile(x)]
JS_FILES = tuple(uniqify(list(JS_FILES)))

iscssfile = lambda x: x.lower().endswith('.css')
CSS_FILES = [x for x 
              in os.listdir(os.path.join(package_home(globals()), 'css'))
              if iscssfile(x)]
CSS_FILES = tuple(uniqify(list(CSS_FILES)))
          
def initialize(context):
    """ Initialize product """
    try:
        
        context.registerClass(
            Homepage.Homepage,
            constructors = (
                Homepage.manage_addHomepageForm,
                Homepage.manage_addHomepage
                ),
            icon = "www/rememberyourfriends_icon.gif"        
        )
        		
        product = OFS.misc_.misc_.RememberYourFriends

        registerImages(product, WWW_IMAGES, globals(),
                       set_expiry_header=True)
        registerJSFiles(product, JS_FILES, globals(),
                        slim_if_possible=True,
                        gzip_if_possible=True,
                        max_age_production=3600*5,
                        set_expiry_header=True)
        registerCSSFiles(product, CSS_FILES, globals(),
                         slim_if_possible=True,
                         gzip_if_possible=True,
                         max_age_production=3600*5,
                         set_expiry_header=True,
                         replace_images_with_aliases=True)
        

        #icons = uniqify(ICON_ASSOCIATIONS.values())
        #for icon in icons:
        #    registerImage(product, icon, epath='icons', Globals=globals())
        
    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb

        

        
