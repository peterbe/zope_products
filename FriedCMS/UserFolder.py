# -*- coding: iso-8859-1 -*-

##
## News
## (c) Fry-IT, www.fry-it.com
## Lukasz Lakomy
##

# python
from urllib import urlencode

# Zope
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.User import BasicUserFolder
from Globals import InitializeClass
from Globals import MessageDialog, PersistentMapping
from Acquisition import aq_inner, aq_parent
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

# Our friend...
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

# Product
from User import FriedCMSUser
from Constants import *


#-----------------------------------------------------------------------------

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())
    
def manage_addUserFolder(context, REQUEST=None):
    """ """
    f = FriedCMSUserFolder()
    try:
        context._setObject('acl_users', f)
    except: 
        if REQUEST:
            return MessageDialog(
                title  ='Item Exists',
                message='This object already contains a User Folder',
                action ='%s/manage_main' % REQUEST['URL1'])
        else:
            raise AttributeError, "User folder already exists"
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(context.absolute_url()+'/manage_main')
        
#-----------------------------------------------------------------------------        
        
class FriedCMSUserFolder(BasicUserFolder):
    """
    """
    meta_type = METATYPE_USERFOLDER
    id = 'acl_users'
    title = 'User Folder'

    security = ClassSecurityInfo()
    manage_options = ({ 'label' : 'Details', 'action' : 'tabUserFolderContents'},)+\
                   BasicUserFolder.manage_options[:1]+\
                   ({ 'label' : 'Local Roles', 'action' : 'tabLocalRoles'},)+\
                   BasicUserFolder.manage_options[1:]
     
    def __init__(self):
        self._users = PersistentMapping()
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT,'index_html')
    def index_html(self, REQUEST=None):
        """ """
        if REQUEST:
            return self.http_redirect("viewUsers")


    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'countUsers')
    def countUsers(self):
        """ return integer of how many users there are in this user folder """
        return len(self._users)
    
        
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'getUserNames')
    def getUserNames(self):
        """
        Return a list of usernames
        """
        names = self._users.keys()
        names.sort()
        return names

    def getAuthenticatedUser(self):
        authenticated = getSecurityManager().getUser()
        return authenticated
        
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'getUsers')
    def getUsers(self):
        """
        Return a list of user objects, but only those who are
        defined below object to which current user has permissions.
        """
        result = self._users.keys()
        result.sort()
        users = [self._users[n] for n in result]
        return users
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'getUser')
    def getUser(self, name):
        """
        Return the named user object or None
        """
        user = self._users.get(name, None)
        return user

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'hasUsers')
    def hasUsers(self):
        """
        """
        if self._users:
            return True
        else:
            return False

    def _doAddUser(self, username, password, roles,
                   firstname='', lastname='',
                   email='', company='', **kw):
        """
        """
        parent = aq_parent(aq_inner(self))
        for role in roles:
            if role not in self.getAvailableRoles():
                parent._addRole(role)
                
        if password is not None and self.encrypt_passwords:
            password = self._encryptPassword(password)
        user = FriedCMSUser(username, password, roles,
                            firstname=firstname, lastname=lastname,
                            email=email, company=company, **kw)
        self._users[username] = user
        return True

    #deprecated
    def _doChangeUser(self, username, password, roles, domains, **kw):
        user = self._users[username]
        if password is not None:
            if (self.encrypt_passwords and not self._isPasswordEncrypted(password)):
                password = self._encryptPassword(password)
            user._setPassword(password)
        user.roles = roles

    def _doDelUsers(self, names):
        for username in names:
            del self._users[username]

    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'manage_addUser')
    def manage_addUser(self, username, password, repeat_password, roles=[],
                       firstname='', lastname='', new_role='',
                       email='', company='', REQUEST=None, **kw):
        """
        """
        msg = ""
        if not username:
            msg = "Usrename can not be empty."
        elif not password:
            msg = "Password can not be empty."
        elif password != repeat_password:
            msg = "Password does not match its confirmation."
        else:
            #No global roles for user, only local roles
            roles = [x.strip() for x in roles if x.strip()]
            if new_role.strip():
                roles.append(new_role)
            
            self._doAddUser(username, password, roles,
                            firstname=firstname, lastname=lastname,
                            email=email, company=company, **kw)
        if msg: #failed
            if REQUEST:
                REQUEST['msg'] = msg
                return self.addUserForm(self, REQUEST)
            else:
                return msg
        else:
            msg = "User added."
            if REQUEST:
                REQUEST['msg'] = msg
                return self.viewUsers(self, REQUEST)
            else:
                return msg
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT,'getAvailableRoles')
    def getAvailableRoles(self):
        """
        """
        roles = []
        all_roles = self.valid_roles()
        for r in all_roles:
            #if r not in ('Authenticated','Anonymous','Manager','Owner'):
            if r not in ('Authenticated','Owner'):
                roles.append(r)
        return roles

    security.declareProtected(PERMISSION_MANAGE_CONTENT,'manage_editUser')
    def manage_editUser(self, username, password='', repeat_password='', roles=[],
                        firstname = '', lastname='',
                        email='', company='', REQUEST=None, **kw):
        """
        """
        msg = ""
        if not username:
            msg = "Usrename can not be empty."
        elif password != repeat_password:
            msg = "Password does not match its confirmation."
        else:
            user = self._users[username]      
            params = {'username':username, 
                      'roles':roles,
                      'firstname':firstname, 'lastname':lastname,
                      'email':email, 'company':company,
                      }
            user.editUser(**params)
            self._users[username] = user
            #If password is empty dont change it
            if password:
                if (self.encrypt_passwords and not self._isPasswordEncrypted(password)):
                    password = self._encryptPassword(password)
                user._setPassword(password)      
        if msg: #failed
            if REQUEST:
                REQUEST['msg'] = msg
                return self.editUserForm(self,REQUEST)
            else:
                return msg
        else:
            msg = "User data changed."
            if REQUEST:
                REQUEST['msg'] = msg
                return self.viewUsers(self,REQUEST)
            else:
                return msg
    
    security.declareProtected(PERMISSION_MANAGE_CONTENT, 'manage_deleteUsers')
    def manage_deleteUsers(self, usernames, REQUEST=None):
        """
        """
        if not usernames:
            msg = "No users selected"
        else:
            if type(usernames) == type(''):
                usernames = [usernames]
                #remove user objects
                self._doDelUsers(usernames)
            msg = "%d user(s) deleted."%len(usernames)
        if REQUEST:
            url = "%s/%s"%(self.absolute_url(),"viewUsers")
            self.http_redirect(url,msg=msg)
        else:
            return msg
    
        
    security.declareProtected(VMS, 'manage_getLocalRoles')
    def manage_getLocalRoles(self):
        """
        Check all site objects for local roles
        """
        result = []
        parent = self.aq_parent
        self.getLocalRolesForObject(1, parent, result)
        return result
        
    def getLocalRolesForObject(self,level,object,result):
        """
        """
        record = {}
        objects = object.objectValues()
        raw_roles = object.get_local_roles()
        roles = []
        #omitt 'Owner' role
        for r in raw_roles:
            if 'Owner' not in r[1]:
                roles.append(r)
        record['level'] = level
        record['roles'] = roles
        record['title'] = object.title_or_id()
        record['url'] = object.absolute_url()
        record['icon'] = object.icon
        #return only objects with roles
        if roles:
            result.append(record)
        for ob in objects:
            self.getLocalRolesForObject(level+1,ob,result)
        
    def canAuthenticatedAccessUser(self, user):
        """
        Method used in templates to check if particular user
        can be accesed by logged in user. In general yes, but
        this function can be overriden in inheriting classes
        to check morer conditions
        """
        auth = self.getAuthenticatedUser()
        if auth.has_permission(MANAGE_CONTENT_PERMISSIONS,self):
            return True
        else:
            return False
        
        
templates = ('zpt/userfolder/viewUsers',
             'zpt/userfolder/macrosUserFolder',
             'zpt/userfolder/viewUserForm',
             'zpt/userfolder/editUserForm',
             'zpt/userfolder/deleteUserForm',
             'zpt/userfolder/addUserForm',
             'zpt/userfolder/tabLocalRoles',
             'zpt/userfolder/tabUserFolderContents',
             )  
addTemplates2Class(FriedCMSUserFolder, templates)
InitializeClass(FriedCMSUserFolder)
