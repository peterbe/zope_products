##
## ZTinyMCE
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

import TinyMCE
import Configuration
import OFS


""" ZTinyMCE """

          
def initialize(context):
    """ Initialize product """
    try:
        
        context.registerClass(
            TinyMCE.TinyMCE,
            constructors = (
                TinyMCE.manage_addZTinyMCEForm,
                TinyMCE.manage_addZTinyMCE
                ),
            icon = "www/tinymce_icon.gif"        
        )
        
        context.registerClass(
            Configuration.TinyMCEConfiguration,
            constructors = (
                Configuration.manage_addZTinyConfigurationForm,
                Configuration.manage_addZTinyConfiguration,
                Configuration.manage_findZTinyMCEInstances
                ),
            icon = "www/configuration_icon.gif"
        )        
        		
        product = OFS.misc_.misc_.ZTinyMCE
        #registerIcon(product, 'configuration_icon.gif')
        
        
    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb

        
##import App
##
##def registerIcon(product, filename, idreplacer={}, epath=None, startpath='www/'):
##    # A helper function that takes an image filename (assumed
##    # to live in a 'www' subdirectory of this package). It 
##    # creates an ImageFile instance and adds it as an attribute
##    # of misc_.MyPackage of the zope application object (note
##    # that misc_.MyPackage has already been created by the product
##    # initialization machinery by the time registerIcon is called).
##    objectid = filename
##    if epath is not None:
##        path = "%s%s/" % (startpath, epath)
##    else:
##        path = startpath
##    
##    for k,v in idreplacer.items():
##        objectid = objectid.replace(k,v)
##    setattr(product,
##            objectid, 
##            App.ImageFile.ImageFile('%s%s' % (path, filename), globals())
##            )
##        