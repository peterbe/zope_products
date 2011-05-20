##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner

# Our friend...
from Products.FriedZopeBase.Utils import AddParam2URL, getRandomString
#from Products.FriedZopeBase import Utils as FriedUtils
#from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

# Product
from Tables import Users
from Constants import *
from Utils import debug
from I18N import _

class SecurityBase(Users):
    
    ##
    ## Login and SESSION handling
    ##
    
    def getLoginUID(self):
        """ return the UID the user has logged in with (from SESSION) 
        
        If we can find it, we'll also renew so that the session is prolonged. """
        
        key = SESSIONKEY_LOGIN_UID
        value = self.get_session(key)
        if value:
            self._setLoginUID(value)
            return value
        else:
            return None
        
    def getLoggedinUser(self):
        """ wrapper around getLoginUID() and _getUser() """
        uid = self.getLoginUID()
        return self._getUser(uid) # from Tables.py
    
    def getLoggedinUserFull(self):
        """ wrapper around getLoginUID() and _getUser(full=True) """
        uid = self.getLoginUID()
        return self._getUser(uid, True) # from Tables.py
    
    
    def hasAutologinUID(self):
        """ return true if the user has a autologin cookie """
        cookie_key = COOKIEKEY_AUTOLOGIN_UID
        autologin_uid = self.get_cookie(cookie_key, None)
        return autologin_uid is not None
        
    def isLoggedIn(self):
        """ return true if logged in properly. 
        boolean wrapper on getLoginUID()
        """
        if bool(self.getLoginUID()):
            return True
        else:
            # check if perhaps the user has a autologin cookie
            cookie_key = COOKIEKEY_AUTOLOGIN_UID
            autologin_uid = self.get_cookie(cookie_key, None)

            if autologin_uid:
                try:
                    uid = int(autologin_uid)
                except ValueError:
                    return False
                
                # check that the user exits
                if self.hasUser(uid):
                    # autologin!
                    debug("Autologin user with uid=%r" % uid, steps=4)
                    self._loginUID(uid)
                    return True
                else: # ...there is something very wrong about that uid
                    debug("Autologin UID=%r does NOT exist" % uid)
                    # delete the autologin cookie
                    self.expire_cookie(cookie_key)
                    
            return False
        
    def Logout(self, came_from=None, redirect=True):
        """ clear the session and leave """
        
        if self.isLoggedIn():
            key = SESSIONKEY_LOGIN_UID
            self.REQUEST.SESSION.delete(key)
            
        # if they have a autologin, destroy that too
        cookie_key = COOKIEKEY_AUTOLOGIN_UID
        if self.has_cookie(cookie_key):
            self.expire_cookie(cookie_key)
            
        goto = self.getRootURL() + '/logged-out'
        if came_from:
            goto = came_from
            
        # in case the user was in HTTPS mode
        #goto = self.httpifyURL(goto)
            
        # this little trick we do to change the URL so that stupid caching
        # Internet Explorer won't think we're still logged in.
        if redirect:
            return self.http_redirect(goto, p=getRandomString(4))

    def loginPasskey(self, passkey, remember_passkey=False, REQUEST=None):
        """ try to log in """
        
        users = self._findUserByPasskey(passkey)
        
        _success = False
        
        if users:
            uid = users[0].uid
            self._loginUID(uid)
            
            if remember_passkey:
                # automatic login. We actually don't store the password in a cookie,
                # we just store the uid in a special cookie variable.
                cookie_key = COOKIEKEY_AUTOLOGIN_UID
                days = AUTOLOGIN_EXPIRES_DAYS
                self.set_cookie(cookie_key, uid, expires=days,
                                path='/'
                                )
            _success = True
            
        if REQUEST:
            if _success:
                success = _("Logged in")
            else:
                success = _("Could not log in :(")
            self.http_redirect(self.getRootURL(), success=success)
        else:
            return _success
    ##
    ## Private methods
    ##
    
    
    
    def _loginUID(self, uid):
        """ actually set the session on the user for the first time """
        # 
        # 1. Set the login session
        #
        self._setLoginUID(uid)
        
        #
        # 2. We might want to do more stuff here when the user logs in
        #

        # update the users last_login_time
        self._updateLastLoginTime(uid)
        

    def _setLoginUID(self, uid):
        """ set the session again """
        # Put their uid into SESSION
        key = SESSIONKEY_LOGIN_UID
        self.set_session(key, uid) 
    
    