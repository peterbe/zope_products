##
## MUnderscorePatch
## A monkey patch hack that makes it possible to just write
## http://localhost:8080/something/m_ and it will redirect to
## http://localhost:8080/something/manage_main
##
## Peter Bengtsson
## www.fry-it.com
## Date: 27 Nov 2006

def m_(self):
    """ peter's hack """
    return self.REQUEST.RESPONSE.redirect('manage_main')

from OFS.ObjectManager import ObjectManager
setattr(ObjectManager, 'm_', m_)
