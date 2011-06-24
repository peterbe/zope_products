import os
import OFS, App
from Globals import package_home


# Zope products
from Products.FriedZopeBase.Zope import (
registerImages, registerImage, registerJSFiles, registerCSSFiles)
from Products.FriedZopeBase.Utils import uniqify, anyTrue

# Product
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
             Homepage.SmurlHomepage,
             constructors = (
                 # This is called when
                 Homepage.manage_addSmurlHomepageForm,
                 # someone adds the product
                 Homepage.manage_addSmurlHomepage
                 ),
                 icon = "www/homepage_icon.gif"
            )

        product = OFS.misc_.misc_.SmurlHomepage

        registerImages(product, WWW_IMAGES, globals())
        registerJSFiles(product, JS_FILES, globals(),
                        gzip_if_possible=False,
                        max_age_production=3600*5)
        registerCSSFiles(product, CSS_FILES, globals(),
                         gzip_if_possible=False,
                         replace_images_with_aliases=True,
                         max_age_production=3600*5)

    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb
