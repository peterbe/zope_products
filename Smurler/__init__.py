# Smurler - Make looong URLs shorter
# License: ZPL
# http://smurl.name
# Peter Bengtsson, mail@peterbe.com
#

import Smurl

def initialize(context):
    """ Initialize IssueTracker product """
    try:


        context.registerClass(
            Smurl.SmurlFolder,
            constructors = (
                # This is called when
                Smurl.manage_addSmurlFolderForm,
                # someone adds the product
                Smurl.manage_addSmurlFolder
                ),
            icon = "www/smurlfolder.gif"
            )
            
        registerIcon('smurl.gif')
        
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
        traceback.print_exc(sys.stdout) # for all those people in debug mode zope
        del type, val, tb
        
        
import OFS, App

def registerIcon(filename, idreplacer={}, epath=None):
    # A helper function that takes an image filename (assumed
    # to live in a 'www' subdirectory of this package). It 
    # creates an ImageFile instance and adds it as an attribute
    # of misc_.MyPackage of the zope application object (note
    # that misc_.MyPackage has already been created by the product
    # initialization machinery by the time registerIcon is called).
    objectid = filename
    if epath is not None:
        path = "www/%s/"%epath
    else:
        path = "www/"
    
    for k,v in idreplacer.items():
        objectid = objectid.replace(k,v)
    setattr(OFS.misc_.misc_.Smurler,
            objectid, 
            App.ImageFile.ImageFile('%s%s' % (path, filename), globals())
            )
        