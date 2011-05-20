# Homepage that uses a SmurlFolder has a base

import sys, os, re
from cStringIO import StringIO

from Globals import InitializeClass, package_home, DTMLFile
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from DocumentTemplate import sequence
from zExceptions import BadRequest

from Products.Smurler.Smurl import SmurlFolder

from Products.FriedZopeBase.Bases import HomepageBase
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote
from Products.FriedZopeBase import Utils

from Titlefinder import fetchTitle

#-------------------------------------------------------------------------------

GOOGLE_SAFEBROWSING_URL = "http://www.google.com/safebrowsing/diagnostic?site=%s"

__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())

import urllib
import urllib2
def is_suspicious(url):
    check_url = GOOGLE_SAFEBROWSING_URL % urllib.quote(url)
    req = urllib2.Request(check_url)
    response = urllib2.urlopen(req).read()
    if 'Site is listed as suspicious' in response:
        return True
    return False


def _equalURL(url1, url2):
    def _stripendings(s, endings):
        for ending in endings:
            if s.endswith(ending):
                s = s[:-len(ending)]
        return s

    # normalize
    url1 = url1.strip().lower()
    url2 = url2.strip().lower()

    # normalize even more
    url1 = _stripendings(url1, ('index_html','index.html','/'))
    url2 = _stripendings(url2, ('index_html','index.html','/'))

    return url1 == url2


# note make sure they're all in lower case
BANNED_DOMAIN_NAMES = (
  'yalla-yalla.co.uk',
  'www.madsigns.it',
  'stereolife.org.ru',
  'eyegs.com',
  'darkprints.com',
  'mongolia24.com',
)

BANNED_ENDINGS = (
  '/pot.php',
  '/mosaik.php',
  '/script.php',
  '/keys.php',
  '/prev.php',
  '/star.php',
  '/rem.php',
  '/rsac.php',
  '/mac.php',
  '/dir.php',
  '/r.php',
  '.exe',
  '/common.php',
)

BANNED_MULTI_MATCHES = (
  ('loginbmo','.php'), # http://wegreener.com/loginbmo16/pot.php
  ('/www','.php'), # http://p15.gorzow.pl/www28bom/rsac.php
  ('bom','.php'), # http://abastuman.ge/www7bom/rsac.php
  ('makeSmurl','url'), # http://smurl.name/makeSmurl?url=http%3A//smurl.name/makeSmurl%3Furl%3Dhttp%253A//smurl.name/makeSmurl%253Furl%253Dhttp%2...
)

#-------------------------------------------------------------------------------

manage_addSmurlHomepageForm = DTMLFile('dtml/addSmurlHomepageForm', globals())

def manage_addSmurlHomepage(dispatcher, id, title='', REQUEST=None):
    """ add a SmurlHomepage instance via the web """

    dest = dispatcher.Destination()
    inst = SmurlHomepage(id, title)
    dest._setObject(id, inst)
    self = getattr(dest, id)

    if REQUEST is not None:
        # whereto next?
        redirect = REQUEST.RESPONSE.redirect
        redirect(REQUEST.URL1+'/manage_workspace')



#-------------------------------------------------------------------------------


class SmurlHomepage(SmurlFolder, HomepageBase):

    meta_type = 'Smurl Homepage'

    _properties = ({'id':'title',   'type':'string', 'mode':'w'},
                  )

    security = ClassSecurityInfo()

    def __init__(self, id, title=''):
        """ create a homepage instance """
        self.id = id
        self.title = title
        SmurlFolder.__init__(self, id)



    def makeSmurl(self, url):
        """ wrapper on createSmurl() """
        url = url.strip()
        if not url:
            return self.index_html(self, self.REQUEST)

        # Spambot quiz
        if not self.get_cookie('notsmurlsb'):
            today = self.REQUEST.get('today','')
            if today not in (DateTime().strftime('%y'), DateTime().strftime('%Y')):
                return self.index_html(self, self.REQUEST,
                                    submiterror="Failed anti-spambot quiz")
            else:
                # passed the test!
                self.set_cookie('notsmurlsb', 1, expires=30)

        if is_suspicious(url):
            raise BadRequest("Suspicious URL according to Google SafeBrowser")

        from urlparse import urlparse
        if urlparse(url)[1].lower() in BANNED_DOMAIN_NAMES:
            raise BadRequest("Banned domain name")

        for ending in BANNED_ENDINGS:
            if urlparse(url)[2].endswith(ending):
                raise BadRequest("Suspected phishing")

        for matches in BANNED_MULTI_MATCHES:
            all = True
            for m in matches:
                if m not in url:
                    all = False
                    break
            if all:
                raise BadRequest("Suspected phishing")

        if url.endswith('.zip'):
            raise BadRequest(
          "Not allowed to link to zip files. Too much virus")

        for e in ('http','ftp','https'):
            if url.startswith(e):
                break

            url = 'http://'+url
            break


        if _equalURL(url, self.absolute_url()):
            return self.index_html(self, self.REQUEST,
                                   self_recursive_url=1)

        ip = self.REQUEST.get('REMOTE_ADDR', '')
        if ip == '127.0.0.1':
            LOG("makeSmurl", INFO, "IP address is 127.0.0.1 :(")
            ip = ''
        LOG("makeSmurl", INFO, "Smurled this URL: %s" % url)
        obj = self._createSmurl(url, ip=ip) # inherited
        small_url = obj.absolute_url()

        self._remember_smurlid(obj.getId())


        return self.index_html(self, self.REQUEST,
                               url=url,
                               small_url=small_url)

    def _remember_smurlid(self, smurlid):
        """ remember that this has been used with a cookie """
        ckey = 'smurl_homepage_smurlids'
        prev = self.get_cookie(ckey, '')
        items = [x.strip() for x in prev.split('|')]
        if smurlid in items:
            items.remove(smurlid)
        items.insert(0, smurlid)
        items = [x.strip() for x in items if x.strip()]
        self.set_cookie(ckey, '|'.join(items), expires=100)

    def getRememberedSmurlIds(self, asobjects=False):
        """ return all the ids remembered """
        ckey = 'smurl_homepage_smurlids'
        prev = self.get_cookie(ckey, '')
        items = [x.strip() for x in prev.split('|')]

        checked = []
        for item in items:
            if hasattr(self, item):
                if asobjects:
                    checked.append(getattr(self, item))
                else:
                    checked.append(item)
        return checked


    def showLongURL(self, s, maxlength=50):
        """ if 's' is a really long string, return it as
        ssssssssssssssssss<br />ssssssssssssssssssss
        html_quoted
        """

        _hq_ = Utils.html_quote

        if len(s) > maxlength:
            parts = []
            no_parts = len(s)/ maxlength
            remainder = bool(len(s) % maxlength)

            for i in range(no_parts):
                parts.append(_hq_(s[i*maxlength:maxlength*(i+1)]))

            if remainder:
                parts.append(_hq_(s[maxlength*no_parts:]))

            return '<br />'.join(parts)

        return s

    def getHeader(self):
        """ return the template (and the macro within it) that is
        used to wrap all templates. """
        # Since we might be using CheckoutableTemplates and macro
        # templates are very special we are forced to do the follow$
        # magic to get the macro 'standard' from a potentially chec$
        # out StandardHeader
        zodb_id = 'standard_header.zpt'
        template = getattr(self, zodb_id, self.standard_header)
        return template.macros['standard']

    def domain_name_fixer(self):
        """ http://no-www.org/ """
        u = self.REQUEST.URL
        if u.endswith('/index_html'):
            u = u[:-len('/index_html')]

        if u.startswith('http://www.smurl.name'):
            redir = self.REQUEST.RESPONSE.redirect
            return redir(u.replace('http://www.smurl','http://smurl'))

        return ""

    def sendFeedback(self, feedback, your_email):
        """ send some feedback to the webmaster """

        if self.REQUEST.get('website'):
            raise "SubmitError", "Spammer?"

        feedback = feedback.strip()
        your_email = your_email.strip()
        if not feedback:
            raise "SubmitError", "No feedback provided"

        valid_email = Utils.ValidEmailAddress(your_email)

        To = "mail@peterbe.com"
        if valid_email:
            From = your_email
        else:
            From = To

        subject = "Feedback on smurl.name"
        self.sendEmail(feedback, To, From, subject)

        params = {'feedback-sent':'yes'}
        url = self.getRedirectURL(self.REQUEST.URL1+"/about", params)
        self.http_redirect(url)


    def countAllSmurls(self):
        """ return how many Smurls there are """
        return len(self.objectValues('Smurl'))

    def countPageTitledSmurls(self, include_failures=False):
        """ return how many smurls have a pagetitle """
        t=0
        for smurl in self.objectValues('Smurl'):
            ptitle = smurl.getPageTitle()
            if ptitle is not None:
                if include_failures:
                    t += 1
                elif ptitle:
                    t += 1
        return t


    first_smurl_id = None
    def getFirstSmurl(self, use_cache=True):
        """ return the first object added """
        if use_cache and self.first_smurl_id:
            return getattr(self, self.first_smurl_id)
        else:
            all = list(self.objectValues('Smurl'))
            all = sequence.sort(all, (('create_date',),))
            first_smurl = all[0]
            self.first_smurl_id = first_smurl.getId()
            return first_smurl

    last_smurl_id = None
    def getLastSmurl(self, use_cache=False):
        """ return the last object added """
        if use_cache and self.last_smurl_id:
            return getattr(self, self.last_smurl_id)
        else:
            all = list(self.objectValues('Smurl'))
            all = sequence.sort(all, (('create_date',),))
            last_smurl = all[-1]
            self.last_smurl_id = last_smurl.getId()
            return last_smurl

    def _fetchTitle(self, u):
        """ wrap self._fetchTitle_external() """
        # do a few tests to see if we should bother trying to
        # fetch the title
        zope_manage_url = re.compile(r'/manage_\w+')
        if zope_manage_url.findall(u):
            return None

        try:
            return self._fetchTitle_external(u)
        except:
            LOG(self.__class__.__name__, ERROR, "Failed to fetch title in _fetchTitle_external()",
                error=sys.exc_info())
            return None

    def _fetchTitle_external(self, u):
        """ wrap Titlefinder.fetchTitle() """
        old_stderr = sys.stderr
        stderr_file = StringIO()
        sys.stderr = stderr_file
        t = fetchTitle(u)
        errors = stderr_file.getvalue()
        if errors:
            LOG(self.__class__.__name__, PROBLEM, "Failed to fetch title of %r\n%s"%(u, errors))
        return t

    def fetchTitles(self, howmany=10):
        """ on the last couple of smurls, try to fetch the title """
        howmany = int(howmany)
        c = 0
        count_good = 0
        for smurl in self.objectValues('Smurl'):
            if smurl.getPageTitle() is None and smurl.getURL().startswith('http://'):
                title = self._fetchTitle(smurl.getURL())
                if title is None:
                    title = ''
                else:
                    count_good += 1
                smurl.setPageTitle(title)
                c += 1
                if c >= howmany:
                    break

        if count_good == 0:
            return "No new titles found"
        elif count_good == 1:
            return "One new title found"
        else:
            return "%s new titles found" % count_good







zpts = ('zpt/standard_header',
        {'f':'zpt/about', 'o':'XHTML'},
        {'f':'zpt/index_html', 'o':'XHTML'},
        'zpt/your_smurls',
        'zpt/stats',
        )
addTemplates2Class(SmurlHomepage, zpts)
dtmls = ({'f':'dtml/style.css', 'o':'CSS'},
        )
addTemplates2Class(SmurlHomepage, dtmls)


InitializeClass(SmurlHomepage)
