# -*- coding: iso-8859-1 -*-

######################################################################
##                          FAQ class                              ##
##                                                                  ##
## A simple page content type with tilte and body. Almost           ##
## Identical to BaseConntent                                        ##
##                                                                  ##
##                 (c) Fry-IT, www.fry-it.com                       ## 
##              Lukasz Lakomy <lukasz@fry-it.com>                   ##
######################################################################

# python
import os, re, sys

# Zope
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
#from DocumentTemplate import sequence
#from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
#from OFS.PropertyManager import PropertyManager
#from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
#from Acquisition import aq_inner, aq_parent

# Our friend...
#from Products.FriedZopeBase.Bases import HomepageBTreeBase, SimpleItemBaseCatalogAware
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import internationalizeID, unicodify

# Product
from Constants import *
from BaseContent import BaseContent
from BaseContent import BaseContainer
from Categories import Categories
from Categories import CategoriesContainer
#import Utils

######################################################################
## FAQContainer 
######################################################################

manage_addFAQContainerForm = PTF('zpt/faq/addFAQContainerForm', globals())
def manage_addFAQContainer(dispatcher, id, title=u'', REQUEST=None):
    """
    Create instance
    """
    if hasattr(dispatcher, 'Destination'):
        dest = dispatcher.Destination()
    else:
        dest = dispatcher
    id = id.strip()
    title = unicodify(title.strip())
    if title and not id:
        id = internationalizeID(title.replace(' ','-'))
        
    instance = FAQContainer(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    
    if REQUEST is not None:
        if REQUEST.get('goto_after'):
            url = REQUEST.get('goto_after')
        else:
            url = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(url)

class FAQContainer(BaseContainer, CategoriesContainer):
    """
    FAQContainer
    """    
    meta_type = METATYPE_FAQCONTAINER
    element_meta_type = METATYPE_FAQ
    element_name = 'FAQ'    
    management_page = 'FAQManagement'
    
    security = ClassSecurityInfo()    
    _properties = BaseContainer._properties + CategoriesContainer._properties
     
    security.declareProtected(PERMISSION_VIEW, 'getFAQs')
    getFAQs = CategoriesContainer.getItems
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'deleteFAQ')
    deleteFAQ = BaseContainer.deleteItem
            
    security.declareProtected(PERMISSION_VIEW, 'countFAQ')
    countFAQ = BaseContainer.countItems    
        
templates = ('zpt/faq/FAQManagement',
             #'zpt/faq/addPageForm',
             'zpt/faq/deleteFAQForm',
            )
addTemplates2Class(FAQContainer, templates, globals_=globals())

security = ClassSecurityInfo()
#security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'addFAQForm')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deleteFAQForm')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'FAQManagement')
security.apply(FAQContainer)
InitializeClass(FAQContainer)
        
        
######################################################################
## FAQ
######################################################################
manage_addFAQForm = PTF('zpt/faq/addFAQForm', globals())
def manage_addFAQ(dispatcher, id, title,
                  abstract='', body='', publish_date=None,
                  category = None, REQUEST=None):
    """
    Create FAQ object
    """

    if hasattr(dispatcher, 'Destination'):
        dest = dispatcher.Destination()
    else:
        dest = dispatcher
    if not title:
        raise "TitleError", "No title supplied"

    if isinstance(title, str):
        title = unicodify(title)        
    if isinstance(abstract, str):
        abstract = unicodify(abstract)
    if isinstance(body, str):
        body = unicodify(body)
    if isinstance(category, str):
        category = unicodify(category)
        
    instance = FAQ(id, title, abstract, body, publish_date,
                   category = category)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    object._cook()

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/FAQManagement')

class FAQ(BaseContent, Categories):
    """
    FAQ class
    """
    
    meta_type = METATYPE_FAQ
    security = ClassSecurityInfo()
    
    _properties= BaseContent._properties + Categories._properties
        
    def __init__(self, id, title, abstract, body, publish_date=None,
                 blogitemurl='', abstract_display_format='html',
                 body_display_format='html', category = None):
        """ init """
        BaseContent.__init__(self, id, title, abstract = abstract, 
                             body = body, publish_date = publish_date)
        self.setCategory(category) 

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'editFAQ')
    def editFAQ(self, title = None, abstract = None,
                body = None, publish_date = None,
                category = None, REQUEST = None):
        """
        Edit FAQ item
        """      
        if category is not None:
            self.setCategory(category)
        #Update base attributes, render and reindex
        BaseContent.editBaseContent(self, title = title, abstract = abstract, 
                                    body = body, publish_date = publish_date)        
        if REQUEST is not None:
            msg = "New details saved"
            url = self.getContiner().absolute_url()+'/FAQManagement'
            self.http_redirect(url, msg=msg)        
        
templates = ('zpt/faq/editFAQForm',
            )
addTemplates2Class(FAQ, templates, globals_=globals())
security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editFAQForm')
security.apply(FAQ)                
InitializeClass(FAQ)
