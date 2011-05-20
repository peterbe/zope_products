##
## CookieCrumblerIssueTrackerProduct
## (c) Peter Bengtsson, mail@peterbe.com
## Oct, 2005
##
## Please visit www.issuetrackerproduct.com for more info
##


import IssueCrumbler

def initialize(context):
    context.registerClass(
        IssueCrumbler.CookieCrumblerIssueTrackerProduct,
        constructors=(IssueCrumbler.manage_addCCITPForm,
                      IssueCrumbler.manage_addCCITP),
        icon = 'www/cclogin_icon.gif'
        )
        
    registerIcon('padlock.gif')
    
    
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
    setattr(OFS.misc_.misc_.CookieCrumblerIssueTrackerProduct,
            objectid, 
            App.ImageFile.ImageFile('%s%s' % (path, filename), globals())
            )
    