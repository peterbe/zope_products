##
## BetterSiteErrorLog
## An attempt to make the Zope error_log a bit more useful.
## License: ZPL
## By: Peter Bengtsson, Fry-IT, peter@fry-it.com
##

import logging
import os

from Globals import package_home
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog

logger = logging.getLogger('BetterSiteErrorLog')
security = ClassSecurityInfo()


# Set __version__ to SiteErrorLog
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()
setattr(SiteErrorLog, 'BetterSiteErrorLog_version', __version__)


# Patch manage_main
_www = os.path.join(os.path.dirname(__file__), 'www')
setattr(SiteErrorLog, 'manage_main', PageTemplateFile('main.pt', _www))
#logger.info("Patched SiteErrorLog's manage_main")

# Add an RSS version
_www = os.path.join(os.path.dirname(__file__), 'www')
setattr(SiteErrorLog, 'manage_rss_errorlog', PageTemplateFile('rss.pt', _www))


# Add a method that is used to support the RSS template because it was getting to
# complex for the TAL code. In fact, because of the RDF structure of that document
# it was not possible to have this TAL expression:
#   python: len(value) < 70 and value or value[:70] + '...'
# so I created a python method instead that does.
def showValueShortened(self, value, maxlength=70):
    return len(value) < maxlength and value or value[:maxlength] + '...'

setattr(SiteErrorLog, 'showValueShortened', showValueShortened)



# Patch the getLogEntries
def getLogEntries(self, q=None):
    """Returns the entries in the log, most recent first.
    
    Makes a copy to prevent changes.
    
    If @q is provided, do a search first
    """
    if q:
        def matchingQuery(entry, q):
            if entry['type'].lower() == q.lower():
                return True
            if entry['username'].lower() == q.lower():
                return True
            if entry['value'].lower().find(q.lower()) > -1:
                return True
            if q.find('/') > -1 and entry['url'].find(q) > -1:
                return True
                #print entry['url']
                #print entry['id']
                #print entry['req_html']
            
        res = [entry.copy() for entry in self._getLog() if matchingQuery(entry, q)]
    else:
        res = [entry.copy() for entry in self._getLog()]
    res.reverse()
    return res
setattr(SiteErrorLog, 'getLogEntries', getLogEntries)
                

# Add the getLogEntryErrorTypes
from Products.SiteErrorLog.SiteErrorLog import use_error_logging
security.declareProtected(use_error_logging, 'getLogEntryErrorTypes')
def getLogEntryErrorTypes(self):
    types = []
    for entry in self._getLog():
        if entry['type'] not in types:
            types.append(entry['type'])
    return types
setattr(SiteErrorLog, 'getLogEntryErrorTypes', getLogEntryErrorTypes)



# Set the security
security.apply(SiteErrorLog)
