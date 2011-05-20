##
## ThuaWood
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

# python
import os, re, sys
from time import sleep

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from OFS.PropertyManager import PropertyManager


# Our friend...
from Products.FriedZopeBase.Bases import HomepageBTreeBaseCatalogAware
from Products.FriedZopeBase.Bases import SimpleItemBaseCatalogAware
from Products.FriedZopeBase import Utils as FriedUtils
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote
from Products.FriedZopeBase.Utils import internationalizeID, unicodify
# Product
from Constants import *

#-----------------------------------------------------------------------------

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())

class BadEntryError(Exception):
    pass

#-----------------------------------------------------------------------------

manage_addGuestbookForm = PTF('zpt/addGuestbookForm', globals())

def manage_addGuestbook(dispatcher, id, title, REQUEST=None,
                   redirect_to=None):
    """ create instance """
    if not id:
        id = title.replace('&',' o ').strip().replace('  ',' ')
        id = id.replace(' ','-')
        id = internationalizeID(id)
     
    
    title = unicodify(title)
    
    dest = dispatcher.Destination()
        
    instance = Guestbook(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    
    if REQUEST is not None:
        if redirect_to:
            REQUEST.RESPONSE.redirect(redirect_to)
        else:
            REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
        

#-----------------------------------------------------------------------------

class Guestbook(HomepageBTreeBaseCatalogAware):
    """ guestbook for Thua """
    meta_type = METATYPE_GUESTBOOK
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'ustring', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    
    def __init__(self, id, title=u''):
        """ init """
        HomepageBTreeBaseCatalogAware.__init__(self, id)
        self.title = title
        self.create_date = DateTime()
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def addEntry(self, name, email, comment, city='', webpage='', how_found='',
                 gotoafter=None, REQUEST=None):
        """ create a new entry """
        name = name.strip()[:50]
        email = email.strip()[:50]
        city = city.strip()[:50]
        webpage = webpage.strip()[:50]
        if webpage == 'http://':
            webpage = ''
        elif webpage and not webpage.startswith('http'):
            webpage = 'http://' + webpage
        how_found = how_found.strip()[:50]
        comment = comment.strip()
        reject = True
        if comment:
            reject = False
        else:
            if (name or email) and (webpage or city or how_found):
                reject = False
                
        if reject:
            raise BadEntryError("Not enough data to submit")
        else:
            entry = self._createEntry(name, email, comment, city, webpage, how_found)
            
            # for now...
            entry.approve()
            
        if REQUEST:
            if gotoafter:
                return self.http_redirect(gotoafter, msg="Added")
            else:
                return self.http_redirect(self.absolute_url(), msg="Added")
        else:
            return entry
        
        
    def _createEntry(self, name, email, comment, city, webpage, how_found):
        id = DateTime().strftime('%Y%m%d')
        if hasattr(self, id):
            id = DateTime().strftime('%Y%m%d-%H%M')
            if hasattr(self, id):
                id = DateTime().strftime('%Y%m%d-%H%M%S')
                while hasattr(self, id):
                    id = DateTime().strftime('%Y%m%d-%H%M%S')
                    sleep(1)
        name = unicodify(name)
        email = unicodify(email)
        comment = unicodify(comment)
        city = unicodify(city)
        webpage = unicodify(webpage)
        how_found = unicodify(how_found)
        
        inst = Entry(id, name, email, comment, city, webpage, how_found)
        self._setObject(id, inst)
        entry = self._getOb(id)
        return entry
        
    
    def getEntries(self, sort=False, reverse=False, include_unapproved=False):
        """ return all entries """
        
        all = self.objectValues(METATYPE_GUESTBOOK_ENTRY)
        if not include_unapproved:
            all = [x for x in all if x.isApproved()]
        else:
            all = list(all)
            
        if sort:
            all.sort(lambda x,y: cmp(y.create_date, x.create_date))
        if reverse:
            all.reverse()
            
        return all

    security.declareProtected('View management screens','manage_deleteEntry')
    def manage_deleteEntry(self, id, REQUEST=None):
        """ delete an entry """
        assert getattr(self, id).meta_type == METATYPE_GUESTBOOK_ENTRY
        self.manage_delObjects([id])
        
        if REQUEST is not None:
            return self.http_redirect('GuestbookManagement')
        


templates = (#'dtml/something',
             'zpt/GuestbookManagement',
            )
addTemplates2Class(Guestbook, templates)
                
InitializeClass(Guestbook)
    
#-----------------------------------------------------------------------------

class Entry(SimpleItemBaseCatalogAware, PropertyManager):
    meta_type = METATYPE_GUESTBOOK_ENTRY
    security = ClassSecurityInfo()
    
    _properties=({'id':'name',         'type':'ustring', 'mode':'w'},
                 {'id':'email',        'type':'ustring', 'mode':'w'},
                 {'id':'comment',      'type':'utext', 'mode':'w'},
                 {'id':'city',      'type':'ustring', 'mode':'w'},
                 {'id':'create_date',  'type':'date', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())
    
    manage_options = ({'label':'Properties', 'action':'manage_propertiesForm'},
                         )
                         
    
    
    def __init__(self, id, name, email, comment, city, webpage, how_found, 
                 approved=False):
        """ init """
        self.id = id
        self.title = name + ' ' +email
        self.name = name
        self.email = email
        self.comment = comment
        self.city = city
        self.webpage = webpage
        self.how_found = how_found

        self.approved = bool(approved)
        self.create_date = DateTime()
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.name + ' ' + self.email
    
    def isApproved(self):
        return self.approved
    
    def approve(self, REQUEST=None):
        """ approve the entry """
        self.approved = True
        if REQUEST:
            return self.http_redirect(self.absolute_url(), msg="Approved")
        
    def showWebpage(self, maxlength=50):
        """ return the webpage as a tag """
        url = self.webpage
        if url.startswith('http'):
            title = url.replace('http://','')
        else:
            title = url
            url = 'http://' + url
            
        if len(title) > maxlength:
            title = title[:maxlength/2-1]+'...'+title[-(maxlength/2+1):]
            
        title = FriedUtils.html_quote(title)
        return '<a href="%s">%s</a>' % (url, title)
            
        
        