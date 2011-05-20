# Smurler - Make looong URLs shorter
# License: ZPL
# http://smurl.name
# Peter Bengtsson, mail@peterbe.com
#

import sys, os, re
from sets import Set

import random

from Globals import InitializeClass, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from zExceptions import BadRequest
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2


def factorial(n):
    assert n >=1
    if n == 1:
        return 1
    else:
        return n * factorial(n-1)
    
#-------------------------------------------------------------------------------

manage_addSmurlFolderForm = DTMLFile('dtml/addSmurlFolderForm', globals())

def manage_addSmurlFolder(dispatcher, id='smurl', REQUEST=None):
    """ add a SmurlFolder instance via the web """
    
    dest = dispatcher.Destination()
    inst = SmurlFolder(id)
    dest._setObject(id, inst)
    self = getattr(dest, id)
    
    if REQUEST is not None:
        # whereto next?
        redirect = REQUEST.RESPONSE.redirect
        redirect(REQUEST.URL1+'/manage_workspace')
    else:
        return self
    


#-------------------------------------------------------------------------------

class SmurlFolder(BTreeFolder2):
    
    meta_type = 'Smurl Folder'
    
    _properties = ({'id':'upper_and_lower',   'type':'boolean', 'mode':'w'},
                   {'id':'minlength_alpha',   'type':'int',     'mode':'w'},
                   {'id':'minlength_numeric', 'type':'int',     'mode':'w'},
                   {'id':'avoid_duplicates',  'type':'boolean', 'mode':'w'},
                   )

    manage_options = (BTreeFolder2.manage_options[0],) + \
                     ({'label':'Add Smurl', 'action':'AddSmurlZMI'},) + \
                     ({'label':'Find Smurl', 'action':'FindSmurlZMI'},) + \
                     BTreeFolder2.manage_options[1:]
                     
    security = ClassSecurityInfo()

    security.declareProtected('View management screens','AddSmurlZMI')
    AddSmurlZMI = DTMLFile('dtml/AddSmurlZMI', globals())
    
    security.declareProtected('View management screens','FindSmurlZMI')    
    FindSmurlZMI = DTMLFile('dtml/FindSmurlZMI', globals())    
                     

    avoid_duplicates = True # legacy

    def __init__(self, id=None):
        """ return a SmurlFolder instance """
        self.minlength_alpha = 1
        self.minlength_numeric = 1
        self.upper_and_lower = False
        self.avoid_duplicates = True
        BTreeFolder2.__init__(self, id)
    
    def _generateID(self):
        """ generate a new ID that hasn't been instanciated in this
        self before """
        this_base = getattr(self, 'aq_base', self)
        assert self.minlength_alpha >= 1
        assert self.minlength_numeric >= 1
        letters = "abcdefghjklmnpqrstuvwxyz" # o,i left out
        if self.upper_and_lower:
            letters += letters.upper()
        numbers = "23456789" # 0,1 left out

        while 1:
            try:
                genid_bits = random.sample(letters, self.minlength_alpha) + \
                             random.sample(numbers, self.minlength_numeric)
            except:
                letters += letters
                numbers += numbers
                continue
            unique = Set(genid_bits)
            possible_combinations = factorial(len(unique))
            combinations = []

            while len(combinations) < possible_combinations:
                random.shuffle(genid_bits)
                combination = ''.join(genid_bits)
                if combination not in combinations:
                    if not hasattr(this_base, combination):
                        return combination
                    combinations.append(combination)

                    
            if self.minlength_numeric < self.minlength_alpha:
                self.minlength_numeric += 1
            else:
                self.minlength_alpha += 1
            

    def _createSmurl(self, url, ip=''):
        """ create a Smurl object and return the object """
        if not url.startswith('http'):
            url = 'http://'+url
        
        if self.avoid_duplicates:
            for smurl in self.objectValues('Smurl'):
                if smurl.url == url:
                    return smurl
        
        genid = self._generateID()
        inst = Smurl(genid, url, ip=ip)
        self._setObject(genid, inst)
        return getattr(self, genid)
        
    def createSmurlZMI(self, url, ip=''):
        """ wrap createSmurl() but return back to AddSmurlZMI template """
        small_url = self.createSmurl(url, ip=ip)
        
        return self.AddSmurlZMI(self, self.REQUEST, url=url, small_url=small_url)
    
    def createSmurl(self, url, secret='', ip=''):
        """ wrap _createSmurl() by simply returning the URL as a string """
        if secret.lower() not in ('peterbe.com',): # more?
            raise BadRequest("Secret not provided. Spammer?")
        url = url.strip()
        assert url, "URL empty"
        obj = self._createSmurl(url, ip=ip)
        return obj.absolute_url()
    
    
    security.declareProtected('View management screens', 'findSmurls')
    def findSmurls(self, name):
        """ return all the smurl objects that match this name """
        name = name.strip()
        
        # Was something like this entered?
        #  'http://smurl.name/xy12, http://smurl.name/go82'
        if len(name.split(',')) > 1:
            names = [x.strip() for x in name.split(',')]
            # how many of them starts with http
            http_names = [x for x in names if x.startswith('http')]
            if len(names) == len(http_names):
                objs = []
                for name in names:
                    objs.extend(self.findSmurls(name))
                return objs
            
        # perhaps the variable name is something like 'http://smurl.name/xy21'
        # which is a URL but actually refers to a Smurl object.
        if name.startswith('http') and not name.endswith('*') and\
          hasattr(self, name.split('/')[-1]):
            obj = getattr(self, name.split('/')[-1])
            if obj.meta_type == 'Smurl':
                return [obj]

        # was it something like this: 'xy21, gh63'
        if len(name.split(',')) > 1:
            id_names = [x.strip() for x in name.split(',') if hasattr(self, x.strip())]
            if id_names:
                return [getattr(self, id) for id in id_names 
                        if getattr(self, id).meta_type == 'Smurl']
                        
        # is it simply 'xy231'
        if hasattr(self, name) and getattr(self, name).meta_type == 'Smurl':
            return [getattr(self, name)]
        
        
        # is it a URL?
        if name.startswith('http'):
            ending = None
            if name.endswith('*'):
                name = name[:-1]
                objs = []
                for smurl in self.objectValues('Smurl'):
                    if smurl.getURL().startswith(name):
                        objs.append(smurl)
                return objs
            elif name.find('*') > -1:
                expect_parts = name.split('*')
                objs = []
                for smurl in self.objectValues('Smurl'):
                    url = smurl.getURL()
                    if url.startswith(expect_parts[0]):
                        nr_found = 0
                        for part in expect_parts:
                            if url.find(part) > -1:
                                nr_found += 1
                        if nr_found == len(expect_parts) -1:
                            objs.append(smurl)
                return objs
        elif name.count('*'):
            regex_str = ''
            if name.startswith('*'):
                name = name[1:]
            if name.endswith('*'):
                name = name[:-1]
            parts = name.split('*')
            regex_str = '.*?'.join([re.escape(x) for x in parts])
            regex = re.compile(regex_str)
            objs = []
            for smurl in self.objectValues('Smurl'):
                if regex.findall(smurl.getURL()):
                    objs.append(smurl)
            return objs
        elif re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', name):
            objs = []
            for smurl in self.objectValues('Smurl'):
                if smurl.getIP() == name:
                    objs.append(smurl)
            return objs
        else:
            # search for it case insensitively
            for smurl in self.objectValues('Smurl'):
                if smurl.getId().lower() == name.lower():
                    return [smurl]
            
        
        return []
    
    security.declareProtected('View management screens', 'deleteSmurls')
    def deleteSmurls(self, ids, REQUEST=None):
        """ delete some smurl objects """
        if isinstance(ids, basestring):
            ids = [ids]
        del_ids = []
        for id in ids:
            id = id.strip()
            if hasattr(self, id) and getattr(self, id).meta_type == 'Smurl':
                del_ids.append(id)
            
        nr_deletes = len(del_ids)
        if del_ids:
            self.manage_delObjects(del_ids)
            
        if REQUEST:
            url = self.absolute_url()+'/FindSmurlZMI'
            url += '?manage_tabs_message=%s+deleted' % nr_deletes
            self.REQUEST.RESPONSE.redirect(url)
        else:
            return nr_deletes
        
InitializeClass(SmurlFolder)        


#-------------------------------------------------------------------------------

class Smurl(SimpleItem, PropertyManager):
    
    meta_type = 'Smurl'
    
    _properties=({'id':'title',                    'type':'string', 'mode':'w'},
                 {'id':'url',                      'type':'string', 'mode':'w'},
                 {'id':'create_date',              'type':'date',   'mode':'w'},
                 {'id':'ip',                       'type':'string', 'mode':'w'},
                )
                
    icon = 'misc_/Smurler/smurl.gif'
                
    manage_options = ({'label':'Properties', 'action':'manage_propertiesForm'},
                     )
    ip = '' # legacy attribute
    
    def __init__(self, id, url, ip=''):
        self.id = id 
        self.url = url
        self.title = url[:30]
        self.create_date = DateTime()
        self.page_title = None
        self.ip = ip
        
    def getId(self):
        """ return this id """
        return self.id
    
    def getURL(self):
        """ return url """
        return self.url
    
    def getCreateDate(self):
        """ return when this smurl was created """
        return self.create_date
    
    def getIP(self):
        return getattr(self, 'ip', None)
    
    def getPageTitle(self):
        """ return the page_title if there is one """
        return getattr(self, 'page_title', None)
    
    def setPageTitle(self, page_title):
        """ set the page_title """
        self.page_title = page_title    
        
    def view(self):
        """ redirect there """
        self.REQUEST.RESPONSE.redirect(self.url)
        return self.url
    
    def __str__(self):
        """ return a string representation """
        return "%s --> %s" % (self.url, self.absolute_url())
        
    index_html = __call__ = view
        
        
InitializeClass(Smurl)
