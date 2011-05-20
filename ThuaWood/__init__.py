##
## ThuaWood
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

from Products.FriedZopeBase.Zope import registerImages, registerImage
from Products.FriedZopeBase.Utils import uniqify
import Bust
import Guestbook


""" ThuaWood website """

IMAGES = (#{'n':'up-button.gif:down-button.gif', 'd':''},
          )
          
import OFS
          
def initialize(context):
    """ Initialize product """
    try:
        context.registerClass(
            Bust.Bust,
            constructors = (
                Bust.manage_addBustForm,
                Bust.manage_addBust
                ),
            icon = "www/bust_icon.gif"        
        )

        context.registerClass(
            Bust.BustFolder,
            constructors = (
                Bust.manage_addBustFolderForm,
                Bust.manage_addBustFolder
                ),
            icon = "www/bustfolder_icon.gif"        
        )

        context.registerClass(
            Guestbook.Guestbook,
            constructors = (
                Guestbook.manage_addGuestbookForm,
                Guestbook.manage_addGuestbook
                ),
            icon = "www/guestbook_icon.gif"
        )
        
        product = OFS.misc_.misc_.ThuaWood
        
        registerImages(product, IMAGES, globals())

        #icons = uniqify(ICON_ASSOCIATIONS.values())
        #for icon in icons:
        #    registerImage(product, icon, epath='icons', Globals=globals())
        
    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb
