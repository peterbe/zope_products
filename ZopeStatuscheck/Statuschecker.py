import sys, re, os
from time import time

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile, package_home
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from OFS.PropertyManager import PropertyManager
from DateTime import DateTime
from App.Common import rfc1123_date


__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()

PYTHONSCRIPT_POSSIBLE_IDS = ('statuscheck','status-check','status_check')

class Statuschecker(SimpleItem, PropertyManager):
    """ Statuschecker singleton """
    
    
    id = title = 'Statuschecker'
    
    meta_type = 'Zope Status checker'
    
    security= ClassSecurityInfo()
    
    manage_options = ({'label':'Readme', 'action':'manage_readme'},)
    
    def LifeStatusCheck(self, quiet=False, always_refresh=False,
                        simple_errors=False):
        """ return some sort of life sign """
        
        def test(istrue, then, otherwise):
            if istrue:
                return then
            else:
                return otherwise
            
        def pad(s, m=30):
            return s + ' ' * (m - len(s))
            
        tmpl = pad('Status:')+"\tOK\n"
        tmpl += pad('Uptime:') + "\t%(uptime)s\n"
        tmpl += pad('PID:')+ "\t%(pid)s\n"
        tmpl += pad('Product errors:') + "\t%(products)s\n"
        params = {}
        params['uptime'] = self._get_Uptime().strip()
        params['pid'] = self._get_PID().strip()
        _product_errors = self._get_Product_import_errors()
        if _product_errors:
            if quiet:
                if simple_errors:
                    if len(_product_errors) == 1:
                        return "NOT Product import error: %s" % ', '.join(_product_errors)
                    else:
                        return "NOT Product import errors: %s" % ', '.join(_product_errors)
                else:
                    return "NOT"
            else:
                params['products'] = '\n'.join(_product_errors)
        else:
            params['products'] = 'none'
        
        msg = tmpl % params
        msg += '\n'
        
        traverse_test_count = getattr(self, 'traverse_test_count', 0)
        refresh_traverse = False
        if always_refresh or not traverse_test_count or not traverse_test_count % 10:
            refresh_traverse = True
            
            
        msg += pad('Refresh traverse:') + '\t%s\n' % refresh_traverse
        msg += pad('Traverse test count:') + '\t%s\n' % traverse_test_count
        msg += '\n'

        self._reset_object_count()
        
        test_paths = []
        if refresh_traverse:
            self._reset_test_paths()
            iterator = self._test_objects()
        else:
            iterator = self._test_test_paths()
        self.traverse_test_count = traverse_test_count + 1
            
        t0 = time()
        for success, mtype, path, error in iterator:
            test_paths.append(path)
            if mtype == 'Z Psycopg Database Connection':
                msg += "%s\t%s\t%s\n" % (pad('Database:'), test(success, 'OK','ERR'), path)
            else:
                msg += "%s\t%s\t%s\t%s\n" % (pad(mtype+':'), test(success, 'OK','ERR'), path, error)

            if quiet and not success:
                if simple_errors:
                    return "NOT %s" % error
                else:
                    return "NOT"
            
        t1 = time()
        self._test_paths = test_paths
        if refresh_traverse:
            msg += pad('Object count:') + '\t%s\n' % self._object_count
        #else:
        #    msg += pad('Object count:') + '\t%s\n' % self._count_all_objects()
        
        msg += '\n'
        
        msg += 'Took %s seconds\n' % (t1-t0)
        msg += 'ZopeStatuscheck %s' % __version__
        
        if quiet:
            return "OK"
        return msg
    
    def _reset_test_paths(self):
        self._test_paths = []
    
    def _reset_object_count(self):
        self._object_count = 0
        
    def _test_test_paths(self):
        """ go through the list of previously found tests, extract them as objects
        and run them as tests """
        for test_path in self._test_paths:
            each = self.unrestrictedTraverse(test_path)
            if each.meta_type == 'Z Psycopg Database Connection':
                yield self._test_pg_adapter(each)
            elif each.meta_type == 'Script (Python)' and each.getId().lower() in PYTHONSCRIPT_POSSIBLE_IDS:
                yield self._test_run_pythonscript(each)
    
    def _test_objects(self, wherein=None):
        """ recursively look through the ZODB for objects that are worth checking """
        msgs = []
        if wherein is None:
            wherein = self.unrestrictedTraverse('/')
            
        for each in wherein.objectValues():
            if each.meta_type == 'Z Psycopg Database Connection':
                msgs.append(self._test_pg_adapter(each))
            elif each.meta_type == 'Script (Python)' and each.getId().lower() in PYTHONSCRIPT_POSSIBLE_IDS:
                msgs.append(self._test_run_pythonscript(each))
            elif each.isPrincipiaFolderish:
                msgs.extend(self._test_objects(each))
            self._object_count += 1
                
        return msgs
    
    def _test_run_pythonscript(self, pythonscript):
        path = '/'.join(pythonscript.getPhysicalPath())
        # if the python script returns False or raises an error,
        # then there is something seriously wrong about it. 
        try:
            r = pythonscript()
            if r == False:
                return False, pythonscript.meta_type, path, "Failed %s" % pythonscript.absolute_url_path()
            return True, pythonscript.meta_type, path, None
        except:
            err_type, err_value, traceback = sys.exc_info()
            return False, pythonscript.meta_type, path, "%s: %s (%s)" % (err_type, err_value, path)
    
    def _test_pg_adapter(self, adapterobject):
        """ do a test on this adapter and return a message that we've done so """
        path = '/'.join(adapterobject.getPhysicalPath())
        try:
            db = adapterobject()
            assert adapterobject.connected(), "Not connected to pg database"
            item, result = db.query('SELECT COUNT(relname) FROM pg_class;')
            assert isinstance(result[0][0], (long, int)), "Result %s" % result
            return True, adapterobject.meta_type, path, None
        except:
            err_type, err_value, traceback = sys.exc_info()
            return False, adapterobject.meta_type, path, "%s: %s" % (err_type, err_value)
        
    
    def _get_Uptime(self):
        """ return the Zope control panel uptime """
        return self.process_time()
    
    def _get_PID(self):
        """ return Zope's pid """
        return str(self.process_id)
    
    def _get_Product_import_errors(self):
        """ return a count of all installed products """
        errors = []
        for product in self.Control_Panel.Products.objectValues():
            if getattr(product, 'import_error', None):
                errors.append("%s (%s)" % (product.id, product.import_error))
        return errors
    
    def _count_all_objects(self, wherein=None):
        if wherein is None:
            wherein = self.unrestrictedTraverse('/')
        t = 0
        for each in wherein.objectValues():
            t += 1
            if each.isPrincipiaFolderish:
                t += self._count_all_objects(each)
            
        return t
            
    def index_html(self, REQUEST, quiet=False, always_refresh=False, 
                   simple_errors=False):
        """ return wrapped """
        
        # set some headers to prevent any caching
        response = self.REQUEST.RESPONSE
        #now = DateTime().toZone('GMT').rfc822()
        now = rfc1123_date(DateTime())
        response.setHeader('Content-Type', 'text/plain')
        response.setHeader('Expires', now)
        response.setHeader('Cache-Control','public,max-age=0')
        response.setHeader('Pragma', 'no-cache')
        
        return self.LifeStatusCheck(quiet=quiet, 
                                    always_refresh=always_refresh,
                                    simple_errors=simple_errors)
    

    manage_readme = DTMLFile('www/manage_readme', globals())
    
InitializeClass(Statuschecker)    
    
    
    