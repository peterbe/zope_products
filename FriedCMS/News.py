# -*- coding: iso-8859-1 -*-

##
## News
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
from DocumentTemplate import sequence
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from OFS.PropertyManager import PropertyManager
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Acquisition import aq_inner, aq_parent

# Our friend...
from Products.FriedZopeBase.Bases import HomepageBTreeBase, SimpleItemBaseCatalogAware
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import internationalizeID, unicodify
from Products.FriedZopeBase.feedcreator import Feed as RSSFeed, Item as RSSItem

# Product
from Constants import *
import Utils


#-----------------------------------------------------------------------------

manage_addNewsContainerForm = PTF('zpt/addNewsContainerForm', globals())

def manage_suggestNewsItemId(self):
    """ suggest a new id """
    return DateTime().strftime('newsitem-%d%b%Y')


def manage_addNewsContainer(dispatcher, id, title='', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
    
    if not id and title:
        id = internationalizeID(title)
        id = id.replace(' ','-')
        
    title = unicodify(title)
        
    instance = NewsContainer(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    #object.DeployStandards()
    
    if REQUEST is not None:
        if REQUEST.get('goto_after'):
            url = REQUEST.get('goto_after')
        else:
            url = REQUEST.URL1+'/manage_workspace'
        REQUEST.RESPONSE.redirect(url)
    else:
        return object
        

#-----------------------------------------------------------------------------


class NewsContainer(HomepageBTreeBase):
    """ NewsContainer """
    
    meta_type = METATYPE_NEWSCONTAINER
    
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    
    def __init__(self, id, title=u''):
        """ init """
        self.title = title
        apply(HomepageBTreeBase.__init__, (self, id), {})
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def countNewsItems(self):
        """ return how many there are """
        return len(self.objectValues(METATYPE_NEWSITEM))
    
    def getNewsItems(self, howmany=9999, filter_publish_date=1, sort=None,
                     reverse=False):
        """ return all the news objects within """
        ok = []
        now = DateTime()
        count = 0
        objects = self.objectValues(METATYPE_NEWSITEM)
        objects = list(objects)
        if sort:
            #assert None not in objects
            objects = [x for x in objects if x is not None]
            objects = sequence.sort(objects, ((sort,),))

        if not reverse:
            objects.reverse()
            
        for newsitem in objects:
            if not filter_publish_date or newsitem.getPublishDate() <= now:
                count += 1
                if count > howmany:
                    break
                yield newsitem

    
    def RSS(self, filter_publish_date=1, howmany=20, REQUEST=None):
        """ return a XML RSS feed item """

        feed = RSSFeed(self.absolute_url()+'/rss.xml',
                       items=[], 
                       title=self.getRoot().getTitle(),
                       webmaster=self.getWebmasterEmail(),
                       abouturl=self.getRoot().absolute_url())

        count = 0
        for n in self.getNewsItems(filter_publish_date=filter_publish_date,
                                   sort='publish_date'):
            description = n.getAbstract() or n.getBody()
            feed.append(RSSItem(n.getTitle(),
                           n.absolute_url(),
                           description,
                           date=n.getPublishDate(),
                           subject='News')
                           )
            count += 1
            if count >= int(howmany):
                break
            
    
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type','text/xml')
            
        return str(feed).strip()

        


    def getDisplayFormatOptions(self):
        """ return what the user can choose """
        return ({'label':'Plain text', 'name':'plaintext'},
                {'label':'HTML', 'name':'html'},
                {'label':'StructuredText', 'name':'structuredtext'},
                )
              
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deleteNewsItem')
    def deleteNewsItem(self, id, REQUEST=None):
        """ delete the newsitem object """
        assert getattr(self, id).meta_type == METATYPE_NEWSITEM
        self.manage_delObjects([id])
        
        if REQUEST is not None:
            msg = "News item deleted"
            url = self.absolute_url()+'/NewsManagement'
            self.http_redirect(url, msg=msg)
        

templates = ('zpt/NewsManagement',
             'zpt/deleteNewsItemForm',
            )
addTemplates2Class(NewsContainer, templates, globals_=globals())
setattr(NewsContainer, 'rss.xml', NewsContainer.RSS)

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'deleteNewsItemForm')
security.apply(NewsContainer)


InitializeClass(NewsContainer)
        
        
#-------------------------------------------------------------------------------

manage_addNewsItemForm = PTF('zpt/addNewsItemForm', globals())

def manage_suggestNewsItemId(self):
    """ suggest a new id """
    return DateTime().strftime('newsitem-%d%b%Y')


def manage_addNewsItem(dispatcher, title,
                       abstract=u'', body=u'', publish_date=None,
                       abstract_display_format='plaintext',
                       body_display_format='plaintext',
                       newsitem_url='', id=None,
                       REQUEST=None):
    """ create """

    dest = dispatcher.Destination()

    if newsitem_url == 'http://':
        newsitem_url = ''

    if newsitem_url:
        if newsitem_url.startswith('http://http'):
            newsitem_url = newsitem_url[len('http://'):]

        if newsitem_url.startswith('http'):
            parsed = urlparse(newsitem_url)
            assert parsed[1], "URL has no domain"

    if not title:
        raise "TitleError", "No title supplied"

    if isinstance(title, str):
        title = unicodify(title)
        
    if isinstance(abstract, str):
        abstract = unicodify(abstract)

    if isinstance(body, str):
        body = unicodify(body)
        
    if not id:
        id = manage_suggestNewsItemId(dest)


    instance = NewsItem(id, title, abstract, body, publish_date, newsitem_url,
                        abstract_display_format=abstract_display_format,
                        body_display_format=body_display_format)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    object._cook()

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/NewsManagement')
    else:
        return object


class NewsItem(SimpleItemBaseCatalogAware, PropertyManager):
    """ NewsItem """
    
    meta_type = METATYPE_NEWSITEM
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string','mode':'w'},
                 {'id':'abstract',      'type':'text',  'mode':'w'},
                 {'id':'body',          'type':'text',  'mode':'w'},
                 {'id':'publish_date',  'type':'date',  'mode':'w'},
                 {'id':'newsitemurl',   'type':'string','mode':'w'},
                 {'id':'create_date',   'type':'date',  'mode':'r'},
                 )
                
    this_package_home = package_home(globals())
    
    manage_options = (PropertyManager.manage_options[0],)+\
                     ({'label':'View', 'action':'index_html'},) +\
                     SimpleItemBaseCatalogAware.manage_options
    
    
    
    def __init__(self, id, title, abstract, body, publish_date=None,
                 newsitemurl='', abstract_display_format='html',
                 body_display_format='html'):
        """ init """
        self.id = id
        self.title = title
        self.abstract = abstract
        self.abstract_display_format = abstract_display_format
        self.body = body
        self.body_display_format = body_display_format
        if not publish_date:
            publish_date = DateTime()
        elif self.same_type(publish_date, 's'):
            publish_date = DateTime(publish_date)
        self.publish_date = publish_date
        if newsitemurl == 'http://':
            newsitemurl = ''
        self.newsitemurl = newsitemurl
        self.create_date = DateTime()

        self._rendered_abstract = u''
        self._rendered_body = u''
        
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def showTitle(self):
        return FriedUtils.html_quote(self.getTitle())
    
    def getAbstract(self):
        return self.abstract

    def getAbstractDisplayFormat(self):
        return self.abstract_display_format

    def getBody(self):
        return self.body

    def getBodyDisplayFormat(self):
        return self.body_display_format

    def getPublishDate(self):
        return self.publish_date

    def showPublishDate(self, fmt="%d %B %Y"):
        return self.getPublishDate().strftime(fmt)

    def isPublished(self):
        """ true if less than now """
        return self.getPublishDate()<=DateTime()

    def getNewsitemURL(self):
        return self.newsitemurl

    def showNewsitemURL(self, html=0, label=None):
        url = self.getNewsitemURL()
        if label is None:
            label = url
        if url.lower().startswith('www'):
            url = 'http://'+url

        if html:
            return '<a href="%s">%s</a>'%(url, label)
        else:
            return url

    def showAbstract(self):
        return self._rendered_abstract

    def showBody(self):
        return self._rendered_body

    security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editNewsItem')
    def editNewsItem(self, title=None, abstract=None,
                           body=None, publish_date=None,
                           abstract_display_format=None,
                           body_display_format=None,
                           newsitemurl=None, REQUEST=None):
        """ save changes to the news item """
        if title is not None:
            if not title.strip():
                raise "NoTitleError", "Title must be something"
            self.title = unicodify(title.strip())

        if abstract is not None:
            self.abstract = self.tidyText(unicodify(abstract.strip()))

        if body is not None:
            self.body = self.tidyText(unicodify(body.strip()))

        if abstract_display_format is not None:
            self.abstract_display_format = abstract_display_format

        if body_display_format is not None:
            self.body_display_format = body_display_format

        if publish_date is not None:
            if not publish_date:
                raise "DateTimeError", "publish_date can not be blank"
            elif self.same_type(publish_date, 's'):
                self.publish_date = DateTime(publish_date)
            else:
                assert self.same_type(publish_date, DateTime())
                self.publish_date = publish_date

        if newsitemurl is not None:
            if newsitemurl.startswith('http://http'):
                newsitemurl = newsitemurl[len('http://'):]

            if newsitemurl.startswith('http'):
                parsed = urlparse(newsitemurl)
                assert parsed[1], "URL has no domain"

            self.newsitemurl = newsitemurl

        self._cook()
        
        if REQUEST is not None:
            msg = "New details saved"
            url = self.absolute_url()+'/editNewsItemForm'
            self.http_redirect(url, msg=msg)
        
    
    
    def _cook(self):
        """ prepare the _rendered_abstract and _rendered_body """
        text, fmt = self.getAbstract(), self.getAbstractDisplayFormat()
        text = unicodify(text)
        self._rendered_abstract = self.ShowText(text, fmt)
        text, fmt = self.getBody(), self.getBodyDisplayFormat()
        text = unicodify(text)
        self._rendered_body = self.ShowText(text, fmt)


    security.declareProtected('View', 'searchable_text')
    def searchable_text(self):
        """ instead of a class instance attribute for the ZCatalog
        to work on we use this. It's a class method that returns all the text 
        of all slots' raw text without any HTML tags. """
        any_tag_regex = re.compile("<.*?>")
        text = "\n".join([self.getAbstract(), self.getBody()])
        text = any_tag_regex.sub(u"", text)
        return text
    

    security.declareProtected('View', 'searchable_text_ascii')
    def searchable_text_ascii(self):
        """ return the value of searchable_text() ASCII encoded """
        return internationalizeID(self.searchable_text())
    
    security.declareProtected('View', 'getTitle_ascii')
    def getTitle_ascii(self):
        """ return the value of getTitle() ASCII encoded """
        return internationalizeID(self.getTitle())    
    
    def index_object(self):
        """A common method to allow Findables to index themselves."""
        path = '/'.join(self.getPhysicalPath())
        idxs = ['id', 'title', 'searchable_text','path']
        self.getCatalog().catalog_object(self, path, idxs=idxs)
        
        

templates = ('zpt/editNewsItemForm',
            )
addTemplates2Class(NewsItem, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editNewsItemForm')
security.apply(NewsItem)
                
InitializeClass(NewsItem)
        
