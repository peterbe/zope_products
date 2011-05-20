# Python
import os, time, sys
import inspect

# Zope
import Acquisition
from Globals import InitializeClass, package_home, DTMLFile
from Products.ZSQLMethods.SQL import SQL
from Shared.DC.ZRDB.DA import DA
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from AccessControl import ClassSecurityInfo
from DateTime import DateTime

# Product
from Constants import *
from Permissions import VMS
from Errors import MissingArgumentsError, ExcessArgumentsError
import Utils
from Utils import debug

sqlhome = os.path.join(package_home(globals()), 'sql')




def _debugSQLCall(object, kw):
    """ Write to debug file for log of all SQL calls """
    path = os.path.join(CLIENT_HOME, SQLCALLS_LOGFILENAME)
    if not os.path.isfile(path):
        fw = open(path, 'w')
        fw.close()
    sql_method = str(object.id)
    params = str(kw)
    relpath = object.relpath
    datetime = DateTime().strftime('%Y/%m/%d %H:%M:%S')
    line = '%s|%s|%s|%s\n'%(sql_method, relpath, params, datetime)
    f=open(path, 'a')
    f.write(line)
    f.close()
    
def _profileSQLCall(object, timetaken, kw):
    """ write to log file how long it took to execute
    this SQL statement. """
    path = os.path.join(CLIENT_HOME, SQLPROFILING_LOGFILENAME)
    if os.path.exists(path):
        fw = open(path, 'a')
    else:
        fw = open(path, 'w')
        
    out = [str(object.relpath), str(timetaken)]
    out = '|'.join(out)
    
    fw.write(out+'\n')
    fw.close()

    
    
    
        
class InterceptedSQLClass(SQL):
    """ subclass of the SQL (from ZSQLMethods) so that
    we can enable possible executions and initializations.
    """

    manage_options = DA.manage_options[:3]+\
                     ({'label':'Permanent Storage',
                       'action':'manage_permanent_storage'},)+\
                     DA.manage_options[3:]

    security=ClassSecurityInfo()

    security.declareProtected(VMS, 'manage_permanent_storage')
    manage_permanent_storage = DTMLFile('dtml/permanent_storage', globals())
    
    def __init__(self, id, title, connection_id, arguments, template,
                 relpath):
        self.id=str(id)
        try:
            self.manage_edit(title, connection_id, arguments, template)
        except:
            debug("id=%r, title=%r, arguments=%r" % (id, title, arguments), f=1)
            raise 
        self.relpath = relpath
        
    
    def __call__(self, REQUEST=None, __ick__=None, src__=0, test__=0, force_debug__=0, **kw):
        """ override __call__ for debugging purposes
        
        @ src__ = True: return the computed query before being tested about the database
        @ test__= True: return (query, result) and not just result
        @ force_debug__= True: print the SQL statement before running it (if in DEBUG mode)
        
        """
           
        if DEBUG_SQLCALLS or DEBUG and force_debug__:
            #_debugSQLCall(self, kw)
            query = apply(SQL.__call__, (self, REQUEST, __ick__, 1, test__), kw)
            out = "--- %s(%s) ---" % (self.__name__, kw)
            
            if len(out) < 80:
                out += (80 - len(out)) * '-'
            print out
            print query
            print 

        if DEBUG:
            required_arguments = self._arg.keys()
            missing_arguments = [a for a in required_arguments if not kw.has_key(a)]
            excess_arguments = [k for k in kw.keys() if k not in required_arguments]
            if excess_arguments:
                tmpl = self.getRelpath()
                m = "%s was called with " % tmpl
                if len(excess_arguments) > 1:
                    m += "arguments: %s passed " % ', '.join([repr(x) for x in excess_arguments])
                else:
                    m += "argument: %r passed " % excess_arguments[0]
                m += "but not needed."
                try:
                    stk = inspect.stack()[1]
                    module = stk[1].replace(INSTANCE_HOME, '')
                    if module.startswith('/'):
                        module = module[1:]
                    module = module.replace('/','.')
                    m += "Called from %s, line %s, in %s" % (module, stk[2], stk[3])
                    raise ExcessArgumentsError, m
                except IndexError:
                    raise ExcessArgumentsError, "%s excess arguments error" % tmpl
            
            if missing_arguments:
                tmpl = self.getRelpath()
                m = "%s was called without " % tmpl
                if len(missing_arguments) > 1: 
                    m += "arguments: %s passed." % ', '.join([repr(x) for x in missing_arguments])
                else:
                    m += "argument: %r passed." % missing_arguments[0]
                try:
                    stk = inspect.stack()[1]
                    module = stk[1].replace(INSTANCE_HOME, '')
                    if module.startswith('/'):
                        module = module[1:]
                        module = module.replace('/','.')
                        m += "Called from %s, line %s, in %s" % (module, stk[2], stk[3])
                    raise MissingArgumentsError, m
                except IndexError:
                    raise MissingArgumentsError, "%s missing arguments error" % tmpl

        if  PROFILE_SQLCALLS:
            t0=time.time()
            result = apply(SQL.__call__, (self, REQUEST, __ick__, src__, test__), kw)
            t1=time.time()
            _profileSQLCall(self, t1-t0, kw)
            return result

        result = apply(SQL.__call__, (self, REQUEST, __ick__, src__, test__), kw)
        return result
        
    def getRelpath(self):
        """ some doc string """
        return self.relpath

    def canCheckIn(self):
        """ true if in DEBUG mode """
        return DEBUGMODE >= 1

    security.declareProtected(VMS, 'manage_checkIn')
    def manage_checkIn(self, makebackupcopy=0, REQUEST=None):
        """ take the object and inspect it and write it back to file """
        file_write2 = self.relpath
        if file_write2.startswith('/'):
            file_write2 = file_write2[1:]
        filepath = os.path.join(sqlhome, file_write2)

        if makebackupcopy:
            incr = 1
            while os.path.isfile(filepath+'.bak%s'%incr):
                incr += 1
            filepath_backup = filepath+'.bak%s'%incr

            # write the backup
            fr = open(filepath, 'r')
            fw = open(filepath_backup, 'w')
            fw.write(fr.read())
            fw.close()
            fr.close()


        # write it back now
        codeblock = self.document_src()
        fw = open(filepath, 'w')
        fw.write(codeblock)
        fw.close()
        

        if REQUEST is not None:
            mtm = "Changes written to back to file"
            return self.manage_main(self, REQUEST, manage_tabs_message=mtm)
        else:
            return "Done"
        
InitializeClass(InterceptedSQLClass)

class PSQL(Acquisition.Implicit):
    """ QD SQL class that holds all the SQL Commands """
    
    dbConnection = DB_CONNECTION_ID
    
class SQLCommon(PSQL):
    """ SQL attributes """
    pass

class SQLUsers(PSQL):
    """ SQL attributes """
    pass

class SQLReminders(PSQL):
    """ SQL attributes """
    pass

class SQLSentInvitations(PSQL):
    """ SQL attributes """
    pass


##
## Define which folders to look in and which class to
## attach the attributes to.
## These keys() must match folders in sql/
## For subfolders, write key as "Customer:Advanced"
##
Folder2Class = {
    'Common':SQLCommon,
    'Users':SQLUsers,
    'Reminders':SQLReminders,
    'SentInvitations':SQLSentInvitations,
    }

    
##
## Load in all the SQL statements from the files in sql/
##

def _onlynonempty(somelist):
    checked=[]
    for item in somelist:
        if item != '':
            checked.append(item)
    return checked

def _getSQLandParams(filename):
    """ scan a SQL file and return the SQL statement as string
    and the params as a list """
    f= open(filename, 'r')
    data = f.read()
    f.close()
    statement = data[data.find('</params>')+len('</params>'):]
    paramsstr = data[data.find('<params>')+len('<params>'):data.find('</params>')]
    params = paramsstr.replace('\n',' ')
    params = params.split(' ')
    if params==['']:
        params = []
    else:
        params = _onlynonempty(params)
    return params, statement.strip()




def _filterSQLextension(filenames):
    checked = []
    for filename in filenames:
        if filename.lower().endswith('.sql'):
            if filename.startswith('.#'):
                continue
            checked.append(filename)
    return checked


def initializeSQLfiles(folder2class, sqlhomepath):
    for folder, Class in folder2class.items():
        Class.allsqlattributes = []
        if folder.count(':'):
            folder = folder.split(':')
            foldername = apply(os.path.join, folder)
        else:
            foldername = folder
        folder = os.path.join(sqlhomepath, foldername)
        for sqlfile in _filterSQLextension(os.listdir(folder)):
            # from the file, get the params and the statement
            params, statement = _getSQLandParams(os.path.join(folder, sqlfile))
                
            # make up an id
            id = sqlfile[:-4] # removes '.sql'

            # determine relpath
            relpath = os.path.join(folder, sqlfile).replace(sqlhomepath,'')
            
            # Hack that creates aliases 
            aliasid = 'SQL%s'%id
            # make ['par1:int', 'par2'] => 'par1:int par2'
            params = ' '.join(params)
            title = sqlfile
            
            # Now, create this attribute to 'Class'
            dbConnection = Class.dbConnection
            sqlclass = InterceptedSQLClass
            try:
                setattr(Class, id, sqlclass(id, title, dbConnection, 
                                            params, statement, relpath))
            except:
                print >>sys.stderr, "Failed to initialize %s" % relpath
                raise
            Class.allsqlattributes.append(id)
            # set alias
            # no
        
        
initializeSQLfiles(Folder2Class, sqlhome)
    

    
            
    

