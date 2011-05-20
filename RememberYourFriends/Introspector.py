#-*- coding: iso-8859-1 -*
##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys, cgi

# zope
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.FriedZopeBase.Utils import url_quote_plus, niceboolean

from Tables import Users
from I18N import _
from Constants import *
from Utils import debug


class IntrospectorBase(Users):
    
    security = ClassSecurityInfo()
    
    def findUsers(self, uid=0, email='', passkey='', first_name='', last_name='',
                  order_by=None, reverse=False):
        """ return found users """
        reverse = niceboolean(reverse)
        if uid or email or passkey or first_name or last_name:
            try:
                uid = int(uid)
            except ValueError:
                uid = 0
            if email is not None:
                email = '%%%s%%' % email.strip()
            if passkey is not None:
                passkey = passkey.strip()
            if first_name is not None:
                first_name = first_name.strip()
            if last_name is not None:
                last_name = last_name.strip()
            return self._findUsers(uid=uid, email=email, passkey=passkey,
                                   first_name=first_name, last_name=last_name,
                                   order_by=order_by, reverse=reverse)
         
        else:
            return self._getUsers(order_by=order_by, reverse=reverse)
        
    
                  
    def sortByHeader(self, key):
        """ return a query string which makes this key the 
        order_by key """
        
        qs = self.REQUEST.QUERY_STRING
        a = cgi.parse_qs(qs)
        if a.get('order_by',['add_date'])[0] == key:
            a['reverse'] = [not niceboolean(a.get('reverse', [True])[0])]
        else:
            a['reverse'] = [a.get('reverse', [True])[0]]

        a['order_by'] = [key]
        items = []
        for k, vs in a.items():
            for v in vs:
                items.append('%s=%s' % (k, url_quote_plus(v)))
        return '?' + '&'.join(items)
        
    
    security.declareProtected(VMS, 'getSomeonesReminders')
    def getSomeonesReminders(self, uid, order=None, reverse=None, 
                     only_with_email=False,
                     include_invite_option=False):
        """ wrapper on _getReminders() """
        return self._getReminders(uid, order=order, reverse=reverse,
                        only_with_email=only_with_email,
                        include_invite_option=include_invite_option)
                        

    security.declareProtected(VMS, 'deleteUser')
    def deleteUser(self, uid, REQUEST):
        """ delete the user """
        self._deleteUser(uid)
        return self.http_redirect('manage_find_users', 
                                  success='User deleted')
                        
                        


InitializeClass(IntrospectorBase)
                        