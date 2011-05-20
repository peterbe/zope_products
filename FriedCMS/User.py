# -*- coding: iso-8859-1 -*-

##
## News
## (c) Fry-IT, www.fry-it.com
## Lukasz Lakomy
##
from datetime import datetime
# Zope
from AccessControl import ClassSecurityInfo
from AccessControl.User import BasicUser
from Globals import InitializeClass

# Product
from Constants import METATYPE_USER


#-----------------------------------------------------------------------------

class FriedCMSUser(BasicUser):
    """
    """
    meta_type =  METATYPE_USER
    
    def __init__(self, username, password, roles,
                 firstname = '', lastname='',
                 email='', company='', **kw):
        self.id = self.__name__ = username
        self.username  = username
        self.__password = password
        self.roles = roles
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.company = company
        self.created = datetime.now()
        #This enables new attributes without changes
        for key in kw.keys():
            if not hasattr(self,key):
                setattr(self,key,kw[key])
        
        #Not used, only for compatibility with ZMI
        self.__ = password
        self.name = username

    def getDomains(self):
        """
        Not used, only for compatibility with User interface
        """
        return []
        
    def getUserName(self):
        """
        Return the username of a user
        """
        return self.username

    def _getPassword(self):
        """
        Return the password of the user.
        """
        return self.__password
    
    def _setPassword(self,password):
        """
        Return the password of the user.
        """
        self.__password = password
        return True
    
    def getRoles(self):
        """
        Return the list of roles assigned to a user.
        """
        if self.username == 'Anonymous User':
            return tuple(self.roles)
        else: 
            return tuple(self.roles) + ('Authenticated',)
    
    
    def getFirstName(self):
        """
        """
        return self.firstname
    
    def getLastName(self):
        """
        """
        return self.lastname
    
    def getEmail(self):
        """
        """
        return self.email
       
    def getCompany(self):
        """
        """
        return self.company
    
    def getCreationDate(self,to_string=True):
        """
        """
        try:
            result = self.created
        except AttributeError:
            result = datetime.now()
            self.created = result
        if to_string:
            result = str(result)[:19]
        return result
    
    def getField(self, field):
        """
        Get value of any class field
        """
        result = None
        if hasattr(self, field):
            result = getattr(self, key)
        return result
    
    def setField(self, field, value):
        """
        Get value of any class field
        """
        if hasattr(self, field):
            setattr(self, field, value)
            return True
        else:
            return False
    
    def editUser(self, **kw):
        """
        Smart method for editing. Edits only existing fields
        """
        print kw
        for key in kw.keys():
            self.setField(key, kw[key])
        self._p_changed = 1
        return True
    
InitializeClass(FriedCMSUser)