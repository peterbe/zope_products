# -*- coding: iso-8859-1 -*-

######################################################################
##                      BaseContent class                           ##
##                                                                  ##
## General class that should be used by all content elements.       ##
## Defines common functionality:                                    ##  
##  * Attributes: title, body, published date and accessors         ##
##  * Methods used by ZCatalog                                      ##
##  * Defines defaul_catalog to be HCatalog                         ##
##                                                                  ##
##                      BaseContainer class                         ##
##                                                                  ##
## General class that shoudl be used by all container elements.     ##
## Defines common functionality:                                    ##  
##  * Methods to get all items, delete item and count items         ##
##                                                                  ##
##                 (c) Fry-IT, www.fry-it.com                       ## 
##              Lukasz Lakomy <lukasz@fry-it.com>                   ##
######################################################################

#Python
import re

# Zope
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DocumentTemplate import sequence
from DateTime import DateTime
from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF

# Our friend...
from Products.FriedZopeBase.Bases import SimpleItemBaseCatalogAware
from Products.FriedZopeBase.Bases import HomepageBTreeBase
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import internationalizeID, unicodify
from Products.FriedZopeBase.feedcreator import Feed as RSSFeed, Item as RSSItem

# Product
from Constants import *

######################################################################
## Base container
######################################################################
class BaseContainer(HomepageBTreeBase):
    """
    Base Container
    """    
    security = ClassSecurityInfo()
    #Those must be defined in parent class
    element_meta_type = ''
    element_name = ''
    management_page = ''
    
    def __init__(self, id, title=u''):
        """ init """
        if isinstance(title, str):
            title = unicodify(title)
        self.title = title
        apply(HomepageBTreeBase.__init__, (self, id), {})
        
    def getId(self):
        """
        Return id
        """
        return self.id
    
    def getTitle(self):
        """
        Return title
        """
        return self.title
    
    def getContiner(self):
        """
        """
        return self
    
    security.declareProtected(PERMISSION_VIEW, 'getItems')
    def getItems(self, howmany = 9999, filter_publish_date = 1,
                 sort = None, reverse = False):
        """
        Return all the objects within
        """
        result = []
        now = DateTime()
        count = 0
        objects = self.objectValues(self.element_meta_type)
        objects = list(objects)
        if sort:
            objects = [x for x in objects if x is not None]
            objects = sequence.sort(objects, ((sort,),))

        if not reverse:
            objects.reverse()

        for item in objects:
            if not filter_publish_date or item.getPublishDate() <= now:
                count += 1
                if count > howmany:
                    break
                result.append(item)
        return result

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'deleteItem')
    def deleteItem(self, id, REQUEST=None):
        """
        Delete object of given id
        """
        assert getattr(self, id).meta_type == self.element_meta_type
        self.manage_delObjects([id])
        
        if REQUEST is not None:
            msg = "%s deleted"%(self.element_name)
            url = '%s/%s'%(self.absolute_url(),self.management_page)
            self.http_redirect(url, msg=msg)
            
    security.declareProtected(PERMISSION_VIEW, 'countItems')
    def countItems(self):
        """
        Return how many objects there are 
        """
        return len(self.objectValues(self.element_meta_type))
    
    def RSS(self, filter_publish_date=1, howmany=20, REQUEST=None):
        """
        Return a XML RSS feed item
        """

        feed = RSSFeed(self.absolute_url()+'/rss.xml',
                       items=[], 
                       title=self.getRoot().getTitle(),
                       webmaster=self.getWebmasterEmail(),
                       abouturl=self.getRoot().absolute_url())

        count = 0
        items = self.getItems(filter_publish_date=filter_publish_date,
                              sort='publish_date')
        for item in items:
            if hasattr(self,'abstract'):
                description = item.getAbstract()
            else:
                description = item.getBody()
            feed.append(RSSItem(item.getTitle(),
                                item.absolute_url(),
                                description,
                                date=item.getPublishDate(),
                                subject=self.getTitle())
                        )
            count += 1
            if count >= int(howmany):
                break
    
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type','text/xml')
            
        return str(feed).strip()
    
setattr(BaseContainer, 'rss.xml', BaseContainer.RSS)


######################################################################
## Base content
######################################################################
class BaseContent(SimpleItemBaseCatalogAware, PropertyManager):
    """    
    Common functionality for all FriedCMS addable types.
    """    
    #this trick allows automatic cataloging
    default_catalog = ID_ZCATALOG
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',                   'type':'ustring', 'mode':'w'},
                 {'id':'abstract',                'type':'text',    'mode':'w'},                 
                 {'id':'body',                    'type':'utext',   'mode':'w'},
                 {'id':'publish_date',            'type':'date',    'mode':'w'},
                 {'id':'abstract_display_format', 'type':'string',  'mode':'w'},
                 {'id':'body_display_format',     'type':'string',  'mode':'w'},
                 {'id':'create_date',             'type':'date',    'mode':'r'},                 
                 )
    abstract = ''
    body = ''
    abstract_display_format = 'html'
    body_display_format = 'html'
    
    manage_options = (PropertyManager.manage_options[0],)+\
                   ({'label':'View', 'action':'index_html'},) +\
                   ({'label':'Cataloger', 'action':'manage_editCatalogerForm'},) +\
                   SimpleItemBaseCatalogAware.manage_options                
    
    def __init__(self, id, title, abstract = '', body='', publish_date = None,
                 abstract_display_format='html',
                 body_display_format='html'):
        """ init """
        self.id = id
        self.title = unicodify(title)
        self.body = unicodify(body)  
        self.abstract = unicodify(abstract)
        self.create_date = DateTime()
        self.abstract_display_format = abstract_display_format
        self.body_display_format = body_display_format
        if not publish_date:
            publish_date = DateTime()
        elif isinstance(publish_date, basestring):
            publish_date = DateTime(publish_date)
        self.publish_date = publish_date   
        self._rendered_abstract = u''
        self._rendered_body = u''
        self._cook()
        
    ######################################################################
    ## Getters for attributes
    ######################################################################
    security.declareProtected(PERMISSION_VIEW, 'getId')
    def getId(self):
        """
        Return id
        """
        return self.id
    
    security.declareProtected(PERMISSION_VIEW, 'getTitle')
    def getTitle(self):
        """
        Return title
        """
        return self.title
    
    security.declareProtected(PERMISSION_VIEW, 'showTitle')
    def showTitle(self):
        """
        Return title
        """
        return FriedUtils.html_quote(self.getTitle())
    
    security.declareProtected(PERMISSION_VIEW, 'getAbstract')
    def getAbstract(self):
        """
        Return raw abstract
        """
        return self.abstract

    security.declareProtected(PERMISSION_VIEW, 'showAbstract')
    def showAbstract(self):
        """
        Return rendered abstract
        """
        return self._rendered_abstract
    
    security.declareProtected(PERMISSION_VIEW, 'getAbstractDisplayFormat')
    def getAbstractDisplayFormat(self):
        """
        """
        return self.abstract_display_format

    security.declareProtected(PERMISSION_VIEW, 'getBodyDisplayFormat')
    def getBodyDisplayFormat(self):
        """
        """
        return self.body_display_format
    
    security.declareProtected(PERMISSION_VIEW, 'getBody')
    def getBody(self):
        """
        Return raw body
        """
        return self.body
    
    security.declareProtected(PERMISSION_VIEW, 'showBody')
    def showBody(self):
        """
        Return the body formatted
        """
        return self._rendered_body
    
    security.declareProtected(PERMISSION_VIEW, 'getPublishDate')
    def getPublishDate(self):
        """
        Return raw published date as DateTime
        """
        return self.publish_date

    security.declareProtected(PERMISSION_VIEW, 'showPublishDate')
    def showPublishDate(self, fmt="%d %B %Y"):
        """
        Return published date as a string in given format
        """
        return self.getPublishDate().strftime(fmt)

    security.declareProtected(PERMISSION_VIEW, 'isPublished')
    def isPublished(self):
        """
        Return True if published date is less than now
        """
        return self.getPublishDate()<=DateTime()
    
    ######################################################################
    ## Updating methods
    ######################################################################
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'editBaseContent')
    def editBaseContent(self, title=None, abstract=None, body=None,
                        publish_date=None, abstract_display_format='html',
                        body_display_format='html'):
        """
        Update basic attributes title, body, publish date
        """
        if title is not None:
            if not title.strip():
                raise "NoTitleError", "Title must be something"
            self.title = unicodify(title.strip())
        if abstract is not None:
            self.abstract = self.tidyText(unicodify(abstract.strip()))
        if body is not None:
            self.body = self.tidyText(unicodify(body.strip()))
        self.abstract_display_format = abstract_display_format
        self.body_display_format = body_display_format
        if publish_date is not None:
            if not publish_date:
                raise "DateTimeError", "publish_date can not be blank"
            elif self.same_type(publish_date, 's'):
                self.publish_date = DateTime(publish_date)
            else:
                assert self.same_type(publish_date, DateTime())
                self.publish_date = publish_date
        self._cook()
        self.reindex_object()
    
    def _cook(self):
        """
        Prepare _rendered_abstract and _rendered_body
        """
        text, fmt = self.getAbstract(), self.getAbstractDisplayFormat()
        text = unicodify(text)
        self._rendered_abstract = self.ShowText(text, fmt)
        text, fmt = self.getBody(), self.getBodyDisplayFormat()
        text = unicodify(text)
        self._rendered_body = self.ShowText(text, fmt)
        
    security.declareProtected(PERMISSION_VIEW, 'removeWrappingTag')
    def removeWrappingTag(self, text, tag='p'):
        """
        Remove first <p> and last </p> tag. To use our p tag with class
        """
        if text.startswith('<%s>'%tag):
            text = text[len(tag)+2:]
        if text.endswith('</%s>'%tag):
            text = text[:-(len(tag)+3)]            
        return text
    
    ######################################################################
    ## Methods for indexes and metadata used in ZCatalog
    ######################################################################
    security.declareProtected(PERMISSION_VIEW, 'searchable_text')
    def searchable_text(self):
        """
        Remove all HTML tags from title and body
        """
        any_tag_regex = re.compile("<.*?>")
        text = "\n".join([self.getTitle(), self.getAbstract(), self.getBody()])
        text = any_tag_regex.sub("", text)
        return text
    
    security.declareProtected(PERMISSION_VIEW, 'searchable_text_ascii')
    def searchable_text_ascii(self):
        """
        Return the value of searchable_text() ASCII encoded
        """
        return internationalizeID(self.searchable_text())
    
    security.declareProtected(PERMISSION_VIEW, 'getTitle_ascii')
    def getTitle_ascii(self):
        """
        Return the value of getTitle() ASCII encoded
        """
        return internationalizeID(self.getTitle())    

InitializeClass(BaseContent)