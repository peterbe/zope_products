# -*- coding: iso-8859-1 -*-

##
## FriedCMS
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Acquisition import aq_inner, aq_parent
from OFS.PropertyManager import PropertyManager

from Products.FriedZopeBase.Bases import SimpleItemBase
from Products.FriedZopeBase.Utils import niceboolean

from Constants import *


#-------------------------------------------------------------------------------

manage_addModuleForm = DTMLFile('dtml/addModuleForm', globals())
def manage_addModule(dispatcher, id, title, meta_type, product_name,
                       management_home_page, management_page, adder_page, editor_page,
                       is_container=False, parent_meta_type='',
                       REQUEST=None):
    """ create instance """
    dest = dispatcher.Destination()

    instance = Module(id.strip(), title.strip(), meta_type.strip(), 
                      product_name.strip(), management_home_page.strip(),
                      management_page.strip(), adder_page.strip(), editor_page.strip(),
                      niceboolean(is_container), parent_meta_type.strip()
                      )
    dest._setObject(id, instance)
    object = dest._getOb(id)
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')


#-----------------------------------------------------------------------------

class Module(SimpleItemBase, PropertyManager):
    
    security = ClassSecurityInfo()

    _properties=({'id':'title',            'type':'string', 'mode':'w'},
                 {'id':'module_meta_type', 'type':'string', 'mode':'w'},
                 {'id':'product_name',     'type':'string', 'mode':'w'},
                 {'id':'management_home_page','type':'string', 'mode':'w'},
                 {'id':'management_page',  'type':'string', 'mode':'w'},
                 {'id':'adder_page',       'type':'string', 'mode':'w'},
                 {'id':'editor_page',      'type':'string', 'mode':'w'},
                 {'id':'is_container',     'type':'boolean','mode':'w'},
                 {'id':'parent_meta_type', 'type':'string', 'mode':'w'},
                 )    

    manage_options = ({'label':'Properties', 'action':'manage_propertiesForm'},
                     )
    
    meta_type = METATYPE_MODULE
    
    def __init__(self, id, title, meta_type, product_name,
                 management_home_page, management_page, adder_page, editor_page,
                 is_container=False, parent_meta_type='',
                 ):
        self.id = id
        self.title = title
        self.module_meta_type = meta_type
        self.product_name = product_name
        self.management_home_page = management_home_page
        self.management_page = management_page
        self.adder_page = adder_page
        self.editor_page = editor_page
        self.is_container = bool(is_container)
        self.parent_meta_type = parent_meta_type
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def getNiceMetaTypeName(self):
        """ return the module_meta_type name nicely """
        mt = self.module_meta_type
        pn = self.product_name
        return mt.replace(pn,'').strip()

    def isContainer(self):
        """ return true if this is a containerish module """
        return self.is_container
    
    def getHomeURL(self):
        """ return the home page url of the module """
        return self.management_home_page
    
    def getName(self):
        """ return the name """
        if self.getTitle():
            return self.getTitle()
        return self.getId()
    
    def inURL(self):
        """ return true if the REQUEST.URL indicates that we're in one
        of the management pages of this module """
        pages = (self.adder_page, self.management_page, self.editor_page)
        pages = [x.strip() for x in pages if x.strip()]
        if self.anyTrue(self.thisInURLEnding, pages):
            return True
        return False
        
    def findModuleObjects(self, startin=None):
        """ return list of objects (resurisive search) that match this meta_type """
        if startin is None:
            startin = self
            if startin.meta_type == METATYPE_MODULE:
                startin = aq_parent(aq_inner(startin))
        found = []
        for o in startin.objectValues():
            if o.meta_type == self.module_meta_type:
                found.append(o)
            if o.isPrincipiaFolderish:
                found.extend(self.findModuleObjects(o))
        return found
    
InitializeClass(Module)
    