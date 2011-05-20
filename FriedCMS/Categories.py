# -*- coding: iso-8859-1 -*-

######################################################################
##                       CategoriesContainer class                  ##
##                                                                  ##
## A simple class to handle categories/keywords. It defines a       ##
## a list of available keywords to use in children objects          ##
##                                                                  ##
##                         Categories class                         ##
##                                                                  ##
## Class that defines 'category' attribute and set/get method       ##
##                                                                  ##
##                 (c) Fry-IT, www.fry-it.com                       ## 
##              Lukasz Lakomy <lukasz@fry-it.com>                   ##
######################################################################

# python
import types

# Zope
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from DocumentTemplate import sequence

# Product
from Constants import *

######################################################################
## CategoriesContainer
######################################################################
class CategoriesContainer:
    """
    Categories container
    """        
    security = ClassSecurityInfo()    
    _properties = (
        {'id':'categories', 'type':'lines', 'mode':'w'},
        )
    categories = ()  
    
    security.declareProtected(PERMISSION_VIEW, 'getCategories')
    def getCategories(self):
        """
        Get categories list
        """
        return self.categories
    
    security.declareProtected(PERMISSION_VIEW, 'hasCategories')
    def hasCategories(self):
        """
        True if there is at least 1 category
        """
        if len(self.categories) >0:
            return True
        else:
            return False
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'setCategories')
    def setCategories(self, categories):
        """
        Set categories list. Check for duplicates
        """
        existing = [] + list(self.getCategories())
        if type(categories) not in (types.ListType, types.TupleType):
            categories = (categories)
        for category in categories:
            if category not in existing:
                existing.append(category)
        existing.sort()
        self.categories = existing
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'getItems')
    def getItems(self, howmany=9999, filter_publish_date=1, sort=None,
                 reverse=False, category = None):
        """
        Override standard getItems to use 'category' attribute.
        Return all the objects within. 
        """
        result = []
        now = DateTime()
        count = 0
        objects = self.objectValues(self.element_meta_type)
        objects = list(objects)
        if sort:
            #assert None not in objects
            objects = [x for x in objects if x is not None]
            objects = sequence.sort(objects, ((sort,),))

        if not reverse:
            objects.reverse()
                    
        for object in objects:
            if not filter_publish_date or object.getPublishDate() <= now:
                if not category or object.getCategory() == category:
                    count += 1
                    if count > howmany:
                        break
                    result.append(object)
        return result
    
InitializeClass(CategoriesContainer)        

######################################################################
## Categories
######################################################################
class Categories:
    """
    Categories
    """
    security = ClassSecurityInfo()
    
    _properties = (
        {'id':'category', 'type':'string', 'mode':'w'},
        )
    category = ''
                
    security.declareProtected(PERMISSION_VIEW, 'getCategory')
    def getCategory(self):
        """
        Getter
        """
        return self.category        

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'setCategory')
    def setCategory(self, category):
        """
        Setter
        """
        self.category = category
        
InitializeClass(Categories)
