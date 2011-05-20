##
## FriedMessageQueue
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

#from Products.FriedZopeBase.Zope import registerIcons, registerIcon
from Products.FriedZopeBase.Zope import registerImages, registerImage
from Products.FriedZopeBase.Utils import uniqify
import Queue



""" FriedMessageQueue website """

IMAGES = ('message_icon.gif',
          )
          
import OFS
          
def initialize(context):
    """ Initialize product """
    try:
        
        context.registerClass(
        Queue.MessageQueue,
        constructors = (
            Queue.manage_addMessageQueueForm,
            Queue.manage_addMessageQueue
            ),
        icon = "www/queue_icon.gif"        
        )
		
        product = OFS.misc_.misc_.FriedMessageQueue

        registerImages(product, IMAGES, globals())

        
    except:
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb
