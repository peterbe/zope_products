##
## CheckoutableTemplates,
## By Peter Bengtsson, mail@peterbe.com, www.peterbe.com
## Copyright 2003-2005
## License ZPL
##

__doc__="""CheckoutableTemplates by Peter Bengtsson,
Fry-IT Ltd, 2003-2005.

CheckoutableTemplates allows you to make exceptions
with DTML and PageTemplate attributes of a Python product.
This is highly usable if you have an instance of a Python 
product class, and you want to change some little thing in one
of its templates.
"""

__refresh_module__ = 0


# python
import os

# Zope
from OFS.Application import Application
from Globals import HTMLFile
from AccessControl.Permission import registerPermissions
from OFS.SimpleItem import Item
from AccessControl.PermissionRole import PermissionRole

# Product
from Permission import ViewCTPermission, ViewCTDefaultRoles
from CTFiles import CTDTMLFile, CTPageTemplateFile
from Constants import *
from findCTs import CheckoutableTemplatesBase



    # Delete the old config file when Zope starts
    #if os.path.isfile(CONFIGFILEPATH):
        # Delete it!
        #os.remove(CONFIGFILEPATH)



def initialize(context):
        
    registerPermissions(((ViewCTPermission, (), ViewCTDefaultRoles),))
                        

if DISABLE_CHECKOUTABLETEMPLATES:
    from zLOG import LOG, WARNING
    LOG('CheckoutableTemplates', WARNING, 'CheckoutableTemplates disabled')
    
else:
    Application.CheckoutableTemplates = CheckoutableTemplatesBase()
    
    showCT = HTMLFile('showCheckoutableTemplates', globals())
    ViewCTRoles = PermissionRole(ViewCTPermission, ViewCTDefaultRoles)
    Item.showCheckoutableTemplates = showCT
    Item.showCheckoutableTemplates__roles__ = ViewCTRoles

    if DEBUG:
        from zLOG import LOG, INFO
        LOG('CheckoutableTemplates', INFO, 'installed')


    



