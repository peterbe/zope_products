# -*- coding: iso-8859-1 -*
##
## unittest RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

from Globals import SOFTWARE_HOME    
from Testing import ZopeTestCase


import Acquisition
from Products.ZSQLMethods.SQL import SQL
from Shared.DC.ZRDB.DA import DA

ZopeTestCase.installProduct('ZPsycopgDA')
ZopeTestCase.installProduct('RememberYourFriends')
ZopeTestCase.installProduct('MailHost')


#------------------------------------------------------------------------------
#
# Some constants
#
DB_CONNECTION_ID = 'Psycopg_database_connection'


#------------------------------------------------------------------------------

class PSQL(Acquisition.Implicit):
    """ QD SQL class that holds all the SQL Commands """
    dbConnection = DB_CONNECTION_ID

# Open ZODB connection
app = ZopeTestCase.app()
        
# Set up sessioning objects
ZopeTestCase.utils.setupCoreSessions(app)
        
# Set up example applications
#if not hasattr(app, 'Examples'):
#    ZopeTestCase.utils.importObjectFromFile(app, examples_path)
        
# Close ZODB connection
ZopeTestCase.close(app)
        
    
#------------------------------------------------------------------------------


class TestBase(ZopeTestCase.ZopeTestCase):

    def dummy_redirect(self, *a, **kw):
        self.has_redirected = a[0]
        if kw:
            print "*** Redirecting to %r + (%s)" % (a[0], kw)
        else:
            print "*** Redirecting to %r" % a[0]
    
    def afterSetUp(self):
        self._setupDBConnection()
        dispatcher = self.folder.manage_addProduct['RememberYourFriends']
        dispatcher.manage_addHomepage('ryf')
        self.ryf = self.folder['ryf']
        self.ryf.http_redirect = self.dummy_redirect
        
        request = self.app.REQUEST
        sdm = self.app.session_data_manager
        request.set('SESSION', sdm.getSessionData())
        
        self.has_redirected = False
        
        
        
    def _registerTestCompany(self):
        """ register a company that we can refer to later """
    
    def _setupDBConnection(self):
        into = self.folder
        dispatcher = into.manage_addProduct['ZPsycopgDA']
        dispatcher.manage_addZPsycopgConnection(DB_CONNECTION_ID,
                         title='Z Psycopg Database Connection',
                         connection_string='dbname=rememberyourfriends-test',
                         check=True,
                         zdatetime=True)
                         
        self.ps = self.folder[DB_CONNECTION_ID]
        
    def tearDown(self):
        pass
    
    def _login(self, email=None):
        """ a utility function that logs a person in into a SESSION """
        context = self.mexpenses
        try:
            self._logout()
        except:
            pass

        if not hasattr(self, 'test_admin_uid'):
            self._registerTestCompany()

        if email is None:
            uid = self.test_admin_uid
            user = context._getUser(uid)
            email = user.email
            pass_ = user.password
            context.attemptLogin(email, pass_)
        else:
            try:
                user = context._findByUsername(email)[0]
            except IndexError:
                raise IndexError, "No user found with email %r" % email
            context.attemptLogin(user.email, user.password)
            
        
        
    def _logout(self):
        """ a utility function that logs a person out from a SESSION """
        context = self.mexpenses
        context.Logout(redirect=False)
        
