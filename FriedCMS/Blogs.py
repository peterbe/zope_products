# -*- coding: iso-8859-1 -*-

##
## Blogs
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
## 
## Refactoring to use Base classes 
## Lukasz Lakomy <lukasz@fry-it.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass#, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
#from DocumentTemplate import sequence
#from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
#from OFS.PropertyManager import PropertyManager
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Acquisition import aq_inner, aq_parent

# Our friend...
#from Products.FriedZopeBase.Bases import HomepageBTreeBase, SimpleItemBaseCatalogAware
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import internationalizeID, unicodify
#from Products.FriedZopeBase.feedcreator import Feed as RSSFeed, Item as RSSItem

# Product
from Constants import *
from BlogsComments import CommentsStorage
from BaseContent import BaseContent
from BaseContent import BaseContainer
from Categories import Categories
from Categories import CategoriesContainer
import Utils




#-----------------------------------------------------------------------------

manage_addBlogContainerForm = PTF('zpt/addBlogContainerForm', globals())


def manage_addBlogContainer(dispatcher, id, title=u'', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
    
    id = id.strip()
    title = unicodify(title.strip())
    if title and not id:
        id = internationalizeID(title.replace(' ','-'))
        
    instance = BlogContainer(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    
    if REQUEST is not None:
        if REQUEST.get('goto_after'):
            url = REQUEST.get('goto_after')
        else:
            url = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(url)
        

#-----------------------------------------------------------------------------

class BlogContainer(BaseContainer, CategoriesContainer):
    """
    BlogContainer
    """    
    meta_type = METATYPE_BLOGCONTAINER
    element_meta_type = METATYPE_BLOGITEM
    element_name = 'Blog item'    
    management_page = 'BlogManagement'
    
    security = ClassSecurityInfo()    
    _properties = BaseContainer._properties + CategoriesContainer._properties
    
    #def __init__(self, id, title=u''):
        #""" init """
        #self.title = title
        ##apply(HomepageBTreeBase.__init__, (self, id), {})
        #apply(BaseContainer.__init__, (self, id), {})
     
    security.declareProtected(PERMISSION_VIEW, 'getBlogItems')
    getBlogItems = CategoriesContainer.getItems
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'deleteBlogItem')
    deleteBlogItem = BaseContainer.deleteItem
            
    security.declareProtected(PERMISSION_VIEW, 'countBlogs')
    countBlogs = BaseContainer.countItems    
    
    def getDisplayFormatOptions(self):
        """
        Return what text format user can choose
        """
        return ({'label':'Plain text', 'name':'plaintext'},
                {'label':'HTML', 'name':'html'},
                {'label':'StructuredText', 'name':'structuredtext'},
                )
    
    #def getBlogItems(self, howmany=9999, filter_publish_date=1, sort=None,
                     #reverse=False, category = None):
        #"""
        #Return all the blog objects within. 
        #"""
        #ok = []
        #now = DateTime()
        #count = 0
        #objects = self.objectValues(self.element_meta_type)
        #objects = list(objects)
        #if sort:
            ##assert None not in objects
            #objects = [x for x in objects if x is not None]
            #objects = sequence.sort(objects, ((sort,),))

        #if not reverse:
            #objects.reverse()
                    
        #for blogitem in objects:
            #if not filter_publish_date or blogitem.getPublishDate() <= now:
                #if not category or blogitem.getCategory() == category:
                    #count += 1
                    #if count > howmany:
                        #break
                    #ok.append(blogitem)
        #return ok

    def getBlogItemsForMonth(self, year = None, month = None):
        """
        Return blog objects with given year and month. Month can
        be 'Jan' or 1
        """
        result = []
        now = DateTime()
        objects = self.objectValues(METATYPE_BLOGITEM)
        if year:
            year = int(year)
        if not year and month:
            year = now.year()
        if month: #name to int
            try:
                month = DateTime("1 %s 2008" % month).month()
            except:
                raise ValueError("Invalid month %r" % month)
        
        for object in objects:
            publish_date = object.getPublishDate()
            if year and month:
                if publish_date.year() == year and publish_date.month() == month:
                    result.append(object)
            if year and not month:
                if publish_date.year() == year:
                    result.append(object)
        return result

        
templates = ('zpt/BlogManagement',
             'zpt/deleteBlogItemForm',
            )
addTemplates2Class(BlogContainer, templates, globals_=globals())
setattr(BlogContainer, 'rss.xml', BlogContainer.RSS)

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deleteBlogItemForm')
security.apply(BlogContainer)


InitializeClass(BlogContainer)
        
        
#-------------------------------------------------------------------------------

manage_addBlogItemForm = PTF('zpt/addBlogItemForm', globals())


def manage_suggestBlogItemId(self):
    """ suggest a new id """
    return DateTime().strftime('blog-%d%b%Y')


def manage_addBlogItem(dispatcher, title,
                       abstract='', body='', publish_date=None,
                       abstract_display_format='plaintext',
                       body_display_format='plaintext',
                       blogitem_url='', id=None, category = None,
                       REQUEST=None):
    """ create """

    dest = dispatcher.Destination()

    if blogitem_url == 'http://':
        blogitem_url = ''

    if blogitem_url:
        if blogitem_url.startswith('http://http'):
            blogitem_url = blogitem_url[len('http://'):]

        if blogitem_url.startswith('http'):
            parsed = urlparse(blogitem_url)
            assert parsed[1], "URL has no domain"

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
        
    if not id:
        id = manage_suggestBlogItemId(dest)

        
    instance = BlogItem(id, title, abstract, body, publish_date, blogitem_url,
                        abstract_display_format=abstract_display_format,
                        body_display_format=body_display_format,
                        category = category)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    object.DeployStandards()
    object._cook()

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/BlogManagement')


class BlogItem(BaseContent, Categories, CommentsStorage):
    """ BlogItem """
    
    meta_type = METATYPE_BLOGITEM
    security = ClassSecurityInfo()
    
    _properties= BaseContent._properties +(
        {'id':'blogitemurl',   'type':'string','mode':'w'},
        )+ Categories._properties + CommentsStorage._properties
    blogitemurl = ''
        
    def __init__(self, id, title, abstract, body, publish_date=None,
                 blogitemurl='', abstract_display_format='html',
                 body_display_format='html', category = None):
        """ init """
        BaseContent.__init__(self, id, title, abstract = abstract, 
                             body = body, publish_date = publish_date,
                             abstract_display_format = abstract_display_format,
                             body_display_format = body_display_format)
        self.blogitemurl = blogitemurl
        self.setCategory(category)
        CommentsStorage.__init__(self)
        
    security.declareProtected(PERMISSION_VIEW, 'getBlogitemURL')
    def getBlogitemURL(self):
        return self.blogitemurl
    
    security.declareProtected(PERMISSION_VIEW, 'showBlogitemURL')
    def showBlogitemURL(self, html=0, label=None):
        url = self.getBlogitemURL()
        if label is None:
            label = url
        if url.lower().startswith('www'):
            url = 'http://'+url

        if html:
            return '<a href="%s">%s</a>'%(url, label)
        else:
            return url      

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'editBlogItem')
    def editBlogItem(self, title=None, abstract=None,
                     body=None, publish_date=None,
                     abstract_display_format=None,
                     body_display_format=None,
                     blogitemurl=None, category = None,
                     REQUEST=None):
        """ save changes to the blog item """
        if blogitemurl is not None:
            if blogitemurl.startswith('http://http'):
                blogitemurl = blogitemurl[len('http://'):]
            if blogitemurl.startswith('http'):
                parsed = urlparse(blogitemurl)
                assert parsed[1], "URL has no domain"                
            self.blogitemurl = blogitemurl        
        if category is not None:
            self.setCategory(category)
        #Update base attributes, render and reindex
        BaseContent.editBaseContent(self, title = title, abstract = abstract, 
                                    body = body, publish_date = publish_date, 
                                    abstract_display_format = abstract_display_format,
                                    body_display_format = body_display_format)        
        if REQUEST is not None:
            msg = "New details saved"
            url = self.absolute_url()+'/editBlogItemForm'
            self.http_redirect(url, msg=msg)        
        

templates = ('zpt/editBlogItemForm',
            )
addTemplates2Class(BlogItem, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editBlogItemForm')
security.apply(BlogItem)
                
InitializeClass(BlogItem)
        
