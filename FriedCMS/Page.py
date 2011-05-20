# -*- coding: iso-8859-1 -*-

######################################################################
##                          Page class                              ##
##                                                                  ##
## A simple page content type with tilte and body. Almost           ##
## Identical to BaseConntent                                        ##
##                                                                  ##
##                 (c) Fry-IT, www.fry-it.com                       ## 
##              Lukasz Lakomy <lukasz@fry-it.com>                   ##
######################################################################

#Python
#import re

# Zope
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
#from DateTime import DateTime
#from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF

# Our friend...
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class# as addTemplates2ClassRemote
from Products.FriedZopeBase.Utils import unicodify

# Product
from Constants import *
from BaseContent import BaseContent
from BaseContent import BaseContainer


#def addTemplates2Class(Class, templates, optimize=None):
#    """ we do this so that we easy can send our own globals() """
#    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())

    
######################################################################
## Page container
######################################################################
class PageContainer(BaseContainer):
    """
    Pages Container
    """    
    meta_type = METATYPE_PAGECONTAINER
    security = ClassSecurityInfo()
    
    element_meta_type = METATYPE_PAGE
    element_name = 'Page'
    management_page = 'PagesManagementHome'
    
    security.declareProtected(PERMISSION_VIEW, 'getPages')
    getPages = BaseContainer.getItems
     
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'deletePage')
    deletePage = BaseContainer.deleteItem
            
    security.declareProtected(PERMISSION_VIEW, 'countPages')
    countPages = BaseContainer.countItems
    
templates = (
    'zpt/page/PagesManagementHome',
    'zpt/page/addPageForm',
    'zpt/page/deletePageForm',)            
addTemplates2Class(PageContainer, templates, globals_=globals())
                
security = ClassSecurityInfo()
security.declareProtected(PERMISSION_MANAGE_CONTENT, 'PagesManagementHome')
security.declareProtected(PERMISSION_MANAGE_CONTENT, 'addPageForm')
security.declareProtected(PERMISSION_MANAGE_CONTENT, 'deletePageForm')
security.apply(PageContainer)
InitializeClass(PageContainer)


######################################################################
## Page 
######################################################################

manage_addPageForm = PTF('zpt/page/addPageForm', globals())
def manage_addPage(context, id, title, abstract = u'',
                   body=u'',publish_date=None,
                   REQUEST=None):
    """ create """
    if isinstance(title, str):
        title = unicodify(title)
    if isinstance(abstract, str):
        abstract = unicodify(abstract)
    if isinstance(body, str):
        body = unicodify(body)
        
    obj = Page(id, title, abstract = abstract, body = body, 
               publish_date = publish_date)
    context._setObject(id, obj)
    item = context._getOb(id)
    
    if REQUEST is not None:
        msg = "Page created."
        url = REQUEST.URL1+'/PagesManagementHome'
        item.http_redirect(url, msg=msg)
    else:
        return item
        
class Page(BaseContent):
    """    
    A simple page with tilte and body
    """    
    meta_type = METATYPE_PAGE
    security = ClassSecurityInfo()
        
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'editPage')
    def editPage(self, title=None, abstract=None, body=None, publish_date=None, 
                 REQUEST=None):
        """
        Update the body of the page
        """
        #Update base attributes and reindex
        BaseContent.editBaseContent(self, title = title, abstract = abstract,
                                    body = body, publish_date = publish_date)
        if REQUEST is not None:
            msg = "New details saved"
            url = self.getRootURL()+'/PagesManagementHome'
            self.http_redirect(url, msg=msg)
        
templates = ( 'zpt/page/editPageForm',
            )
addTemplates2Class(Page, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(PERMISSION_MANAGE_CONTENT, 'editPageForm')
security.apply(Page)
InitializeClass(Page)        