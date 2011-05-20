##############################################################################
#
# Copyright (c) 2006 Fry-IT Ltd. All Rights Reserved.
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
import os

# zope
from Globals import package_home
from Products.FriedZopeBase.Utils import uniqify, anyTrue
from Products.FriedZopeBase.Zope import registerImages, registerJSFiles

# here
import Document
import Pan


_this_home = package_home(globals())
isimage = lambda x: anyTrue(x.lower().endswith, ('jpg','png','gif'))
isjsfile = lambda x: x.lower().endswith('.js')

IMAGES = [x for x in os.listdir(os.path.join(_this_home, 'www'))
          if isimage(x)]

JS_FILES = [x for x in os.listdir(os.path.join(_this_home, 'js'))
            if isjsfile(x)]

def initialize(context):
    """ Initialize FriedDocument product """
    try:
        context.registerClass(
            Document.FriedDocument,
            constructors = (
                # Used in the ZMI drop-down
                Document.manage_addFriedDocumentForm,
                Document.manage_addFriedDocument,
                Document.manage_suggestIdFromTitle,
                Document.manage_findMetalPTs,
                Document.manage_findCSSUrlAlts,
                Document.manage_findBeLikeDocuments,
                ),
            icon = "www/frieddoc_icon.gif"

            )
	    
        context.registerClass(
            Pan.DocumentPan,
            constructors = (
                # Used in the ZMI drop-down
                Pan.manage_addFryingDocumentPanForm,
                Pan.manage_addFryingDocumentPan,
                ),
            icon = "www/fryingpan_icon.gif"
            )	    

            
        product = OFS.misc_.misc_.FriedDocument
        
        registerImages(product, IMAGES, globals())
        registerJSFiles(product, JS_FILES, globals())
        
    except:
        """If you can't register the product, tell someone. 
        
        Zope will sometimes provide you with access to "broken product" and
        a backtrace of what went wrong, but not always; I think that only 
        works for errors caught in your main product module. 
        
        This code provides traceback for anything that happened in 
        registerClass(), assuming you're running Zope in debug mode."""
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb




import OFS, App



