##
## CookieCrumblerIssueTrackerProduct
## (c) Peter Bengtsson, mail@peterbe.com
## Oct, 2005
##
## Please visit www.issuetrackerproduct.com for more info
##

# python 
import re, sys, os

# zope
from Globals import InitializeClass, HTMLFile
from AccessControl import getSecurityManager, ClassSecurityInfo, Permissions
from DateTime import DateTime

# other products
from Products.CookieCrumbler.CookieCrumbler import CookieCrumbler
from Products.IssueTrackerProduct.TemplateAdder import addTemplates2Class as AT2C



#-------------------------------------------------------------------------------

def addTemplates2Class(klass, templates, optimize=None):
    AT2C(klass, templates, optimize, Globals=globals())
    

manage_addCCITPForm = HTMLFile('dtml/addCC', globals())

def manage_addCCITP(dispatcher, id, create_forms=0, long_login_days=61,
                    REQUEST=None):
    ' '
    ob = CookieCrumblerIssueTrackerProduct()
    ob.id = id
    ob.long_login_days = int(long_login_days)
    dispatcher._setObject(ob.getId(), ob)
    ob = getattr(dispatcher.this(), ob.getId())
    if create_forms:
        _create_forms(ob)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)
    
#-------------------------------------------------------------------------------

class CookieCrumblerIssueTrackerProduct(CookieCrumbler):
    """ subclass of CookieCrumbler that adds some design and other configurations
    for using a Cookie Crumbler. """
    
    meta_type = 'Cookie Crumbler (IssueTrackerProduct)'
    
    _properties = ({'id':'long_login_days', 'type': 'int', 'mode':'w',
                    'label':'Long login days'},) + CookieCrumbler._properties
    
    long_login_days = 61
    
    security = ClassSecurityInfo()
    
    def setAuthCookie(self, resp, cookie_name, cookie_value):
        """ this method overrides the default setAuthCookie so that we can
        set the cookie for a longer time. """
        kw = {}
        req = getattr(self, 'REQUEST', None)
        if req is not None and req.get('SERVER_URL', '').startswith('https:'):
            # Ask the client to send back the cookie only in SSL mode
            kw['secure'] = 'y'
            
        if req.get('remember_login_days'):
            days = int(req.get('remember_login_days'))
            then = DateTime() + days
            kw['expires'] = then.rfc822()
            resp.setCookie('use_remember_login_days', '1', 
                           path=self.getCookiePath(), **kw)
        else:
            resp.setCookie('use_remember_login_days', '0', 
                           path=self.getCookiePath(), **kw)
            
        resp.setCookie(cookie_name, cookie_value,
                       path=self.getCookiePath(), **kw)
            
        resp.setCookie('__issuetracker_logout_page', 
                       self.absolute_url()+'/logout', # that's how it's defined in CookieCrumbler
                       path=self.getCookiePath(), **kw)
            
    
    
zpts = ('zpt/header_footer',
        'zpt/logged_out',
        'zpt/login_form',
        'zpt/logged_in',
        )
addTemplates2Class(CookieCrumblerIssueTrackerProduct, zpts)

setattr(CookieCrumblerIssueTrackerProduct, 'index_html', CookieCrumblerIssueTrackerProduct.login_form)

InitializeClass(CookieCrumblerIssueTrackerProduct)