#-*- coding: iso-8859-1 -*
##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##


# python
import os, re, sys
from string import zfill
from random import shuffle

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage


# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner
from Products.PageTemplates.PageTemplateFile import PageTemplateFile as PTF
from Products.PythonScripts.standard import newline_to_br


# Our friend...
from Products.FriedZopeBase.Bases import HomepageBase
from Products.FriedZopeBase import Utils as FriedUtils
from Products.FriedZopeBase.Utils import getRandomString, niceboolean, ValidEmailAddress
from Products.FriedZopeBase.Utils import anyTrue, unicodify
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

    
# Product
from Tables import Common, Reminders, SentInvitations
from Security import SecurityBase
from Cron import CronBase
from BirthdayWidget import BirthdayWidgetBase
from Stats import StatsBase
from Introspector import IntrospectorBase
from Errors import SubmitError, InvalidURLError
from I18N import _
import allcountries
import Utils
debug = Utils.debug

from zope.component import getUtility
from zope.i18n.interfaces import ILanguageAvailability
from zope.i18n.locales import locales #, LoadLocalError
domain = 'ryf'

from Constants import *

#-----------------------------------------------------------------------------

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())
    
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()


PASSKEY_REGEX = re.compile('^(p-|_)([A-Za-z0-9]{5,9})$')
UNSUBSCRIBE_PASSKEY_REGEX = re.compile('^u_([A-Za-z0-9]{7,11})$')
REMINDER_REGEX = re.compile('^r(\d{1,8})$')
ID_REGEX = re.compile('^id-(\d{1,8})$')
SNOOZE_REGEX = re.compile('^snooze\.\.\.(\d)\.(day|days|week|weeks|month|months)', re.I)
COMMON_EMAIL_DOMAINS = re.compile(r'@(gmail|hotmail|msn|yahoo|web)\b', re.I)
INVITATION_REGEX = re.compile('^si([0-9]{1,6})$')


def _validateInterval(interval):
    if not Utils.anyTrue(interval.lower().endswith, ('day','days','week','month','months')):
        return False
    if not len(interval.split())==2:
        return False
    try:
        nr = int(interval.split()[0])
        assert nr>0
        assert nr<100
    except ValueError:
        return False
    except AssertionError:
        return False
    return True

def find_emails(s):
    pre_tidy = lambda x: x.replace(')','').replace('(','').strip()
    return [x for x 
              in s.split()
              if ValidEmailAddress(pre_tidy(x))]
#-------------------------------------------------------------------------------

manage_addHomepageForm = PTF('zpt/addHomepageForm', globals())
def manage_addHomepage(dispatcher, id, title='', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
        
    instance = Homepage(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    #object.DeployStandards()
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
        

#-----------------------------------------------------------------------------



class Homepage(HomepageBase, SecurityBase, CronBase, StatsBase,
               IntrospectorBase,
               Common, 
               Reminders, 
               SentInvitations,
               BirthdayWidgetBase,
               ):
    """ Homepage of RememberYourFriends """
    
    meta_type = METATYPE_HOMEPAGE
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                )
                
    this_package_home = package_home(globals())

    def __init__(self, id, title=''):
        """ init """
        self.id = id
        self.title = title
        self.longtitle = title	     
        #self.webmasteremail = WEBMASTER_EMAIL
        #self.webmastername = WEBMASTER_NAME
        #self.developer_email = DEVELOPER_EMAIL
        #self.developer_name = DEVELOPER_NAME
        
    def inDEBUGMode(self):
        """ return true if in DEBUG mode """
        return DEBUG
        
    def getLanguages(self):
        options = getUtility(ILanguageAvailability,
                             domain).getAvailableLanguages()
        options.sort()
        result = []
        for option in options:
            lang = option[0]
            try:
                locale = locales.getLocale(lang)
            except LoadLocaleError:
                # probably not a real locale
                continue
            result.append(
            {'code':lang,
            'name':locale.displayNames.languages[lang],},
            )
        return result

    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title

    def getWebmasterName(self):
        return WEBMASTER_NAME

    def getWebmasterEmail(self):
        return WEBMASTER_EMAIL

    def getWebmasterFromfield(self):
        """ return webmastername and email """
        name = self.getWebmasterName()
        email = self.getWebmasterEmail()
        if name:
            return "%s <%s>" % (name, email)
        else:
            return email

    def getDeveloperEmail(self):
        """ return developer_email or getWebmasterEmail """
        try:
            return DEVELOPER_EMAIL
        except AttributeError:
            return self.getWebmasterEmail()

    def getDeveloperName(self):
        """ return developer_name or getWebmasterName """
        try:
            return DEVELOPER_NAME
        except AttributeError:
            return self.getWebmasterName()

    def getDeveloperFromfield(self):
        """ combine developer_name and developer_email """
        if self.getDeveloperName():
            return "%s <%s>"%(self.getDeveloperName(), self.getDeveloperEmail())
        else:
            return self.getDeveloperEmail()

    def getRoot(self):
        """ return root object """
        mtype = METATYPE_HOMEPAGE
        r = self
        c = 0
        while r.meta_type != mtype:
            r = aq_parent(aq_inner(r))
            c += 1
            if c > 20:
                return None
            if not hasattr(r, 'meta_type'):
                break
        return r
    
    def url_quote_plus(self, q):
        if isinstance(q, unicode):
            q = q.encode(UNICODE_ENCODING)
        return FriedUtils.url_quote_plus(q)

    def getRootURL(self):
        """ return root's absolute_url """
        return self.getRoot().absolute_url()
	
    def getRootURLPath(self):
        """ return root's absolute_url """
        return self.getRoot().absolute_url_path()	
	
    def getHTMLTitle(self):
        """ return a nice suitable title """
        roottitle = self.getRoot().title_or_id()
        try:
            here = self.REQUEST.PARENTS[0]
            try:
                thistitle = here.title_or_id()
                try:
                    base = getattr(here, 'aq_base', here)
                    if hasattr(base, 'getTitleTag'):
                        thistitle = base.getTitleTag()
                    elif hasattr(base, 'getTitle'):
                        thistitle = base.getTitle()
                except:
                    pass
            except:
                try:
                    thistitle = here.getTitle()
                except:
                    thistitle = roottitle


            if roottitle == thistitle:
                return roottitle
            else:
                return "%s - %s"%(thistitle, roottitle)
        except:
            return roottitle
        
        
    def getHeader(self, which=None):
        """ return the appropriate Metal header object """
        if which is not None:
            template = which
        else:
            # Since we might be using CheckoutableTemplates and macro
            # templates are very special we are forced to do the following
            # magic to get the macro 'standard' from a potentially checked
            # out StandardHeader
            zodb_id = 'HeaderFooter.zpt'
            template = getattr(self, zodb_id, self.HeaderFooter)
        return template.macros['standard']
    
    def getManagementHeader(self, which=None):
        """ return the appropriate Metal header object """
        if which is not None:
            template = which
        else:
            # Since we might be using CheckoutableTemplates and macro
            # templates are very special we are forced to do the following
            # magic to get the macro 'standard' from a potentially checked
            # out StandardHeader
            zodb_id = 'ManagementHeaderFooter.zpt'
            template = getattr(self, zodb_id, self.ManagementHeaderFooter)
        return template.macros['standard']    
        
        
    def __before_publishing_traverse__(self, object, REQUEST=None):
        """ sort things out before publising object """
        stack = REQUEST['TraversalRequestNameStack']
        popped = []
        
        passkey_regex = PASSKEY_REGEX
        stack_copy = []
        if stack:
            stack_copy = stack[:]

            for stack_item in stack_copy:
                found_item = False
                
                found_passkeys = passkey_regex.findall(stack_item)
                if found_passkeys and found_passkeys[0]:
                    found_passkey = found_passkeys[0][1]
                    if self.loginPasskey(found_passkey, remember_passkey=True):
                        # cool, you're logged in!
                        REQUEST.set('login-by-url', found_passkey)
                    else:
                        REQUEST.set('failed-login', True)
                    
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    found_item = True
                    
                    
                found_ids = ID_REGEX.findall(stack_item)
                if found_ids and found_ids[0]:
                    found_id = found_ids[0]
                    REQUEST.set('id', found_id)
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    found_item = True                    
                
                found_snoozes = SNOOZE_REGEX.findall(stack_item)
                if found_snoozes:
                    nr, label = found_snoozes[0]
                    interval = nr + " " + label
                    assert _validateInterval(interval), "Invalid interval specified"
                    REQUEST.set('snoozed-by-url', interval)
                    
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    
                found_reminders = REMINDER_REGEX.findall(stack_item)
                if found_reminders:
                    rid = found_reminders[0]
                    try:
                        self._getReminder(rid)
                    except IndexError:
                        raise InvalidURLError, "Invalid reminder Id"
                    REQUEST.set('reminder-by-url', int(rid))
                    
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    
                found_invitations = INVITATION_REGEX.findall(stack_item)
                if found_invitations:
                    siid = found_invitations[0]
                    try:
                        self._getSentInvitation(siid)
                    except IndexError:
                        raise InvalidURLError, "Invalid invitation id %s" % siid
                    REQUEST.set('invitation-by-url', int(siid))
                    stack.remove(stack_item)
                    popped.append(stack_item)
                    
                found_unsubscription_passkeys = \
                   UNSUBSCRIBE_PASSKEY_REGEX.findall(stack_item)
                if found_unsubscription_passkeys:
                    passkey = found_unsubscription_passkeys[0]
                    users = self._findByUnsubscribePasskey(passkey)
                    if not users:
                        raise InvalidURLError, "No valid user to unsubscribe"
                    REQUEST.set('unsubscribe-by-url', users[0].uid)
                    
                    stack.remove(stack_item)
                    popped.append(stack_item)

                    
        # Check some combinations
        if REQUEST.get('reminder-by-url') and not REQUEST.get('login-by-url'):
            raise InvalidURLError, "Reminder specified but not passkey"
        elif REQUEST.get('reminder-by-url') and REQUEST.get('login-by-url'):
            rid = REQUEST.get('reminder-by-url')
            passkey = REQUEST.get('login-by-url')
            user = self._findByPasskey(passkey)[0]
            reminder = self._getReminder(rid)
            if not reminder.uid == user.uid:
                raise InvalidURLError, "Reminder id and passkey missmatch"

            if 'send-invite' in stack_copy:
                kw = {}
                if reminder.email:
                    kw['email'] = reminder.email
                if reminder.name:
                    kw['name'] = reminder.name
                kw['periodicity'] = reminder.periodicity
                return self.http_redirect(self.getRootURL()+'/send-invite', **kw)
            
        
        if REQUEST.get('snoozed-by-url') and not REQUEST.get('reminder-by-url'):
            raise InvalidURLError, "Snooze specified but not reminder id"
        elif REQUEST.get('snoozed-by-url') and REQUEST.get('reminder-by-url'):
            rid = REQUEST.get('reminder-by-url')
            interval = REQUEST.get('snoozed-by-url')
            self._snoozeReminder(rid, interval)
            
        if REQUEST.get('invitation-by-url') and not self.isLoggedIn():
            self._setSentInvitationClicked(REQUEST.get('invitation-by-url'))
            return self.http_redirect(self.getRootURL()+'/accept-invite', 
                                      siid=REQUEST.get('invitation-by-url'))
        
        if REQUEST.get('unsubscribe-by-url'):
            self._unsubscribeUser(REQUEST.get('unsubscribe-by-url'))
            return self.http_redirect(self.getRootURL()+'/unsubscribed')
        
        if REQUEST.get('login-by-url'):
            debug("DID login-by-url")
            # This is only true if someone has clicked on one of those
            # links with the passkey in an email, eg.
            # http://ryf.com/p-xfe523etg (or http://ryf.com/_xfe523etg)
            # We don't then want to continue to show that in the URL
            # so we redirect out to http://ryf.com/
            # since the user has already been logged in.
            url = PASSKEY_REGEX.sub('', REQUEST.URL)
            url = url.replace('index_html','')
            url = re.sub('\w(//)\w','/',url)
            
            remaining_stack = REQUEST.get('TraversalRequestNameStack',[])
            qs = REQUEST.QUERY_STRING
            
            if remaining_stack:
                remaining_url = '/'.join(remaining_stack)
                if url.endswith('/'):
                    url += remaining_url
                else:
                    url += '/' + remaining_url
                if qs:
                    url += '?' + qs
                return self.http_redirect(url)
            else:
                # homepage!
                if qs:
                    url += '?' + qs
                return self.http_redirect(url, success=_("Logged in"))
                    

        if popped:
            REQUEST.set('popped', popped)
            

    def enableGoogleAnalytics(self):
        """ return true if in live mode """
        if DEBUG:
            return False
        if self.REQUEST.BASE0.find('localhost') > -1:
            return False
        return True
    
    def SignUp(self, email, friends, REQUEST):
        """ sign up to the service """
        # check that the user isn't already signed up
        
        email = email.strip()

        submiterrors = {}
        
        if not self.ValidEmailAddress(email):
            submiterrors['email'] = _("Invalid")
        elif self._findUserByEmail(email):
            submiterrors['email'] = _("Already signed up")

        #friends = [x for x in friends if len((x['email']+x['name']).strip())]
        friends = [x for x in friends if len((x['name']).strip())]
        if not friends:
            submiterrors['friends'] = _("No friends entered")
            
        if submiterrors:
            REQUEST.set('submiterrors', submiterrors)
            template = self.index_html
            return template(REQUEST, REQUEST.RESPONSE)
        
        # sign up the user
        uid = self._addUser(email, html_emails=DEFAULT_HTML_EMAILS)

        # add some friends right away
        count = 0
        for friend in friends:
            name = friend['name'].strip()
            email = friend.get('email','').strip()
            if len(name.split(','))==2:
                part2 = name.split(',')[1]
                part2 = part2.strip()
                if self.ValidEmailAddress(part2):
                    name, email = [x.strip() for x in name.split(',')]
            elif self.ValidEmailAddress(name):
                email = name
                name = ''
            elif not email and bool(find_emails(name)):
                emails = find_emails(name)
                email = emails[0].replace('(','').replace(')','')
                name = name.replace(email, '')
                name = name.replace('()','').strip()
                
            periodicity = friend['periodicity']
            if (name or email) and self._validatePeriodicity(periodicity):
                try:
                    self.addReminder(name, email, periodicity, uid=uid)
                    count += 1
                except SubmitError, msg:
                    LOG(self.__class__.__name__, INFO, "Failed to addReminder()",
                        error=sys.exc_info())

        if not count:
            raise SubmitError, "No reminders could be added"
        
            
        self._generatePasswordAndWelcomeUser(uid)
        
        user = self._getUser(uid)
        
        # We use loginPasskey() because it's got the practical 
        # remember_passkey thing and it embeds _loginUID() which
        # sets the logged in SESSION
        self.loginPasskey(user.passkey, remember_passkey=True)
        
        msg = "You have successfully joined RememberYourFriends.com"
        self.http_redirect('change-reminders', success=msg)
        
        
    def addReminder(self, name, email, periodicity, uid=None,
                    birthday=None, birthmonth=None, birthyear=None,
                    REQUEST=None):
        """ nice wrapper on _addReminder() in Tables """
        
        if uid is None:
            if not self.isLoggedIn():
                return self.http_redirect(self.getRootURL(), 
                        failure="Not logged in")
            uid = self.getLoggedinUser().uid
            
        name = unicodify(name)

        if not email and \
          name.find('<') > -1 and name.find('>') > -1 and name.find('"') > -1:
            name, email = self._parseAndSplitToAddress(name)
    
        submiterrors = self._validateReminderData(name, email,
                              periodicity, uid, 
                              birthday, birthmonth, birthyear,
                              )
                        
        if submiterrors and REQUEST:
            REQUEST.set('submiterrors', submiterrors)
            template = getattr(self, 'change-reminders')
            return template(self, REQUEST, submiterrors=submiterrors)
        elif submiterrors:
            raise SubmitError, submiterrors
            
        # enough validating, let's add it
        rid = self._addReminder(uid, name, email, periodicity, 
                                birthday, birthmonth, birthyear)
                          
        if REQUEST:
            self.http_redirect('change-reminders', 
                               success="Added reminder",
                               addedrid=rid
                               )
        else:
            return rid
        
    def _parseAndSplitToAddress(self, name):
        """ perhaps someone entered 
        name: "Peter Bengtsson" <mail@peterbe.com>
        email:
        Then convert this automatically to
        name: Peter Bengtsson
        email: mail@peterbe.com
        """
        name_regex = re.compile(r'"([\w\s]+)"')
        email_regex = re.compile(r'<([\w@\.-]+)>')
        
        email = ''
        
        if len(email_regex.findall(name))==1 and \
          self.ValidEmailAddress(email_regex.findall(name)[0]):
            email = email_regex.findall(name)[0]
            name = email_regex.sub('', name).strip()
            # if possible, remove the "
        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]
        return name, email
        
        
    def deleteReminder(self, rid, REQUEST=None):
        """ delete a reminder and all the logs belonging to it """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure="Not logged in")
        uid = self.getLoggedinUser().uid
        
        rid = int(rid)
        reminder = self._getReminder(rid)
        assert reminder.uid == uid, "Not your reminder to delete"
        
        # delete all the logs
        self._deleteSentReminders(rid)
        self._deleteReminder(rid)
        
        if REQUEST:
            self.http_redirect('change-reminders', success="Gone.")

            
    def pauseReminder(self, rid, REQUEST=None):
        """ pause a reminder """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure="Not logged in")
        uid = self.getLoggedinUser().uid
        
        rid = int(rid)
        reminder = self._getReminder(rid)
        assert reminder.uid == uid, "Not your reminder"
        
        # delete all the logs
        self._pauseReminder(rid)
        
        if REQUEST:
            self.http_redirect('change-reminders#currentreminders', 
                               success="Reminder paused")

            
    def resumeReminder(self, rid, REQUEST=None):
        """ resume a reminder """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure="Not logged in")
        uid = self.getLoggedinUser().uid
        
        rid = int(rid)
        reminder = self._getReminder(rid)
        assert reminder.uid == uid, "Not your reminder"
        
        # delete all the logs
        self._resumeReminder(rid)
        
        if REQUEST:
            self.http_redirect('change-reminders#currentreminders', 
                               success="Reminder resumed")
            
                
    def editReminder(self, rid, name, email, periodicity,
                     dob=None,
                     REQUEST=None):
        """ nice wrapper on _editReminder() """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure="Not logged in")
        uid = self.getLoggedinUser().uid
        
        rid = int(rid)
        
        birthday = birthmonth = birthyear = None
        if dob is not None:
            dob = dob.strip()
            if dob.endswith(','):
                dob = dob[:-1]
                
            jscalendar_format_wy_regex = re.compile(r'(\w{3,9})\s+(\d{1,2}),\s+(\d{4})')
            found_wy = jscalendar_format_wy_regex.findall(dob)

            jscalendar_format_woy_regex = re.compile(r'(\w{3,9})\s+(\d{1,2})')
            found_woy = jscalendar_format_woy_regex.findall(dob)
            if found_wy:
                month, day, year = found_wy[0]
                try:
                    day = zfill(int(day), 2)
                    ok = DateTime('%s %s %s' % (day, month, year))
                except:
                    ok = None
                    debug("Failed to combine %r, %r, %r" % (day, month, year))
                if ok:
                    birthday = int(ok.strftime('%d'))
                    birthmonth = int(ok.strftime('%m'))
                    birthyear = int(ok.strftime('%Y'))
                    
            elif found_woy:
                month, day = found_woy[0]
                year = DateTime().strftime('%Y')
                try:
                    day = zfill(int(day), 2)
                    ok = DateTime('%s %s %s' % (day, month, year))
                except:
                    ok = None
                    debug("Failed to combine %r, %r, %r" % (day, month, year))
                if ok:
                    birthday = int(ok.strftime('%d'))
                    birthmonth = int(ok.strftime('%m'))

                
        
        submiterrors = self._validateReminderData(name, email, 
                                periodicity, uid,
                                birthday, birthmonth, birthyear,
                                rid=rid)
        if submiterrors and REQUEST:
            REQUEST.set('submiterrors', submiterrors)
            REQUEST.set('rid', rid)
            template = getattr(self, 'change-reminders')
            return template(self, REQUEST, submiterrors=submiterrors)
        elif submiterrors:
            raise SubmitError, submiterrors
            
        # save the changes
        self._editReminder(rid, name, email, periodicity, 
                           birthday, birthmonth, birthyear)
        
        if REQUEST:
            self.http_redirect('change-reminders', 
                               success=_(u"Reminder changed"),
                               )
        else:
            return rid        
        
    def _validateReminderData(self, name, email, periodicity, uid, 
                              birthday, birthmonth, birthyear, rid=None):
        """ check the reminder data """
        submiterrors = {}
        if not (name or email):
            submiterrors['name'] = _(u"Empty")
        else:
            for r in self._getReminders(uid):
                if r.name.lower() == name.lower() and \
                   r.email.lower() == email.lower() and \
                   r.periodicity == periodicity:
                    if rid is None or rid != r.rid:
                        msg = _(u"Exact same reminder already exists")
                        submiterrors['name'] = msg
        
        if not self._validatePeriodicity(periodicity):
            submiterrors['periodicity'] = _(u"Invalid")
            
        # validate birthday
        
        this_year = int(DateTime().strftime('%Y'))
        
        if birthday is not None:
            birthday = int(birthday)
            if birthday not in range(1,32):
                submiterrors['birthday'] = _(u"Not in valid range")
            
        if birthmonth is not None:
            birthmonth = int(birthmonth)
            if birthmonth not in range(1,13):
                submiterrors['birthyear'] = _(u"Not in valid range")
                
        if birthyear is not None:
            birthyear = int(birthyear)
            if birthyear not in range(1900, this_year+1):
                submiterrors['birthyear'] = _(u"Not in valid range")
                
        
        def sum_numbers(*a):
            t=0
            for e in a:
                t += e
            return t
            
        
        if sum_numbers(int(submiterrors.has_key('birthday')),
                       int(submiterrors.has_key('birthmonth')),
                       int(submiterrors.has_key('birthyear'))) == 0:
            # no submiterrors on any of those
            if birthday and birthmonth:
                if birthyear:
                    date = '%s/%s/%s' % (birthday, birthmonth, birthyear)
                    try:
                        DateTime(date)
                    except:
                        submiterrors['birthday'] = _(u"Invalid date")
                else:
                    date = '%s/%s/%s' % (birthday, birthmonth, this_year)
                    try:
                        DateTime(date)
                    except:
                        submiterrors['birthday'] = _(u"Invalid date")
        return submiterrors
        
        
            
                    
        
    def _validatePeriodicity(self, periodicity):
        
        regex = re.compile('(\d{1,2}) (week|weeks|month|months|year|years)')
        
        nr, measure = regex.findall(periodicity)[0]
        try:
            nr = int(nr)
        except:
            return False
        if nr < 1:
            return False
        elif nr > 10:
            return False
        if not measure in ('week','weeks','month','months','year','years'):
            return False
        return True


    def _generatePassword(self, uid):
        passkey = Utils.nicepass(4, 2)
        while self._findByPasskey(passkey):
            passkey = Utils.nicepass(4, 2)
        self._updateUserPasskey(uid, passkey)
        return passkey
	    
    def _generatePasswordAndWelcomeUser(self, uid):
        """ create a passkey and send out a welcome-email """
        passkey = self._generatePassword(uid)
        
        count_reminders = self.countReminders(uid)
        
        next_reminders = []
        _on_date = None
        for reminder in self._getReminders(uid, order='next_date'):
            if _on_date is None: # first time
                _on_date = reminder.next_date.strftime('%Y%m%d')
                next_reminders.append(reminder)
            elif reminder.next_date.strftime('%Y%m%d') == _on_date:
                # also on the same date
                next_reminders.append(reminder)
            else: # subsequence
                break

        # now next_reminders is a list of records, all with the same
        # next_date stuff
        if next_reminders[0].age_days <= 31:
            next_reminder_on = next_reminders[0].next_date_month_formatted
        else:
            next_reminder_on = next_reminders[0].next_date_year_formatted
        
        names = []
        for reminder in next_reminders:
            if reminder.name and reminder.email:
                names.append('%s (%s)' % (reminder.name, reminder.email))
            elif reminder.name:
                names.append(reminder.name)
            elif reminder.email:
                names.append(reminder.email)
                
        next_reminder_name = ', '.join(names)
        
        message = self.welcome_message(self, self.REQUEST,
                      passkey=passkey, count_reminders=count_reminders,
                      next_reminder_name=next_reminder_name,
                      next_reminder_on=next_reminder_on)
                      
        user = self._getUser(uid)
        
        self.sendEmailNG(message, user.email, self.getWebmasterFromfield(),
                       _(u"RememberYourFriends.com welcome email"),
                       debug=DEBUG)

                       
    def countReminders(self, uid=None):
        """ return how many reminders this user has """
        if uid is None:
            uid = self.getLoggedinUser().uid
        return self._countReminders(uid)
    
    
    def getReminders(self, order=None, reverse=None, only_with_email=False,
                     include_invite_option=False):
        """ wrapper on _getReminders() """
        uid = self.getLoggedinUser().uid
        return self._getReminders(uid, order=order, reverse=reverse,
                                  only_with_email=only_with_email,
                                  include_invite_option=include_invite_option)
    
    def getReminder(self, rid):
        """ wrapper on _getReminder() but with isYourReminder() baked in """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure=_(u"Not logged in"))
        assert rid, "rid invalid: %r" % rid
        assert self.isYourReminder(rid), "Not your reminder"
        return self._getReminder(rid)
    
    def isYourReminder(self, rid):
        """ does it belong to you """
        uid = self.getLoginUID()
        try:
            reminder = self._getReminder(rid)
        except IndexError:
            return False
        
        return reminder.uid == uid
        
        
    def getSignature(self):
        return EMAIL_SIGNATURE

    DEFAULT_PERIODICITY = "3 weeks"
    
    def getPeriodicityOptions(self):
        return (
          {'value':'1 week', 'label':_(u'Every week')},
          {'value':"2 weeks", 'label':_(u'Every two weeks')},
          {'value':"3 weeks", 'label':_(u'Every three weeks')},
          {'value':"1 month", 'label':_(u'Every month')},
          {'value':"2 months", 'label':_(u'Every two months')},
          {'value':"3 months", 'label':_(u'Every three months')},
          {'value':"6 months", 'label':_(u'Every six months')},
          {'value':"1 year", 'label':_(u'Every year')},
        )
        
    def translatePeriodicityOption(self, value):
        for item in self.getPeriodicityOptions():
            if item['value'] == value:
                return item['label']
        return value
    
    def showReminderName(self, name, email):
        """ return the name and email nicely """
        email_tmpl = '<a href="mailto:%s">%s</a>'
        if name and email:
            return email_tmpl % (email, name)
        elif email:
            return email_tmpl % (email, email)
        return name

    def showName(self, email, first_name, last_name):
        """ return name nicely if possible """
        if first_name and last_name:
            return first_name + ' ' + last_name
        
        name = None
        if first_name:
            name = first_name
        elif last_name:
            name = last_name 
            
        if name:
            return '%s (%s)' % (name, email)
        else:
            return email
        
    def showMonthNumber(self, nr):
        """ return the full english version """
        return {1:_("January"),
                2:_("February"),
                3:_("March"),
                4:_("April"),
                5:_("May"),
                6:_("June"),
                7:_("July"),
                8:_("August"),
                9:_("September"),
                10:_("October"),
                11:_("November"),
                12:_("December"),
                }[int(nr)]
            
                
        
    def showReminderBirthday(self, day, month, year):
        """ return it nicely 
        If the year is known, include it
        """
        if day and month and year:
            d = DateTime('%s/%s/%s' % (year, month, day))
            return d.strftime('%B %d, %Y')
        elif day and month:
            now = DateTime()
            d = DateTime('%s/%s/%s' % (now.strftime('%Y'), month, day))
            return d.strftime('%B %d')
        else:
            return ""
        
    def showReminderBirthdayRecord(self, record):
        """ wrapper on showReminderBirthday() """
        d, m, y = record.birthday, record.birthmonth, record.birthyear
        return self.showReminderBirthday(d, m, y)
    
    def showNameCarefully(self, email, first_name, last_name):
        """ don't reveal the whole email address if you really have to """
        if first_name and last_name:
            return first_name + ' ' + last_name
        
        name = None
        if first_name:
            name = first_name
        elif last_name:
            name = last_name
            
        if COMMON_EMAIL_DOMAINS.match(email):
            first_half, second_half = email.split('@')
            show_email = first_half[:-2]+ '..' + '@' + second_half[:-4]+'...'
        else:
            first_half, second_half = email.split('@')
            show_email = first_half + '@' + second_half[:-4]+'...'
            
        if name:
            return '%s (%s)' % (name, show_email)
        else:
            return show_email
        
    def showCountdown(self, age_days):
        """ return a nicely formatted count down """
        if age_days > 50:
            age_months = int(age_days) / 30
            if age_months == 1:
                return _("1 month")
            else:
                return _("%s months") % age_months
        elif age_days >= 7:
            age_weeks = int(age_days) / 7
            if age_weeks == 1:
                return _("1 week")
            else:
                return _("%s weeks") % age_weeks
        else:
            if age_days == 1:
                return _("1 day")
            elif age_days < 1:
                #return _("less than 1 day")
                return _("< 1 day")
            else:
                return _("%s days") % age_days
                

    def getSentReminders(self, offset=0, limit=100, count=False):
        """ soft wrapper on _getSentReminders() """
        assert self.isLoggedIn(), "Not logged in"
        uid = self.getLoggedinUser().uid
        offset = int(offset)
        limit = int(limit)
        return self._getSentReminders(uid, offset=offset, limit=limit,
                                      count=count)
    
    def show_sent_reminders(self, REQUEST, **kw):
        """ wrapper around the TAL template show_sent_reminders_template.
        If there aren't any reminders or you're not logged in, return nothing.
        """
        if self.isLoggedIn():
            uid = self.getLoggedinUser().uid
            if self._getSentReminders(uid, count=True):
                return self.show_sent_reminders_template(self, REQUEST, **kw)
            else:
                return _(u"No reminders sent to you yet")

        return ""

    
    def show_logged_in(self):
        """ wrapper around TAL template show_logged_in_template.
        """
        if self.isLoggedIn():
            return self.show_logged_in_template(self, self.REQUEST)
        return ""
    
    def countTotalUsers(self):
        return self._countTotalUsers()
    
    def countTotalReminders(self):
        return self._countTotalReminders()
    
    def countTotalSentReminders(self):
        return self._countTotalSentReminders()
    
            
    def index_html(self, REQUEST, RESPONSE):
        """ wrapper around index_html_template """
        #REQUEST.set('LANGUAGE','sv')
        #print REQUEST['HTTP_ACCEPT_LANGUAGE']
        #REQUEST.environ['HTTP_ACCEPT_LANGUAGE'] ='sv'
        #print self._getRequestLanguages()
        
        if REQUEST.get('snoozed-by-url') and REQUEST.get('reminder-by-url'):
            debug("DID snoozed-by-url and reminder-by-url")
            # This happens if someone has reached the home page by
            # passing in a valid reminder and SNOOZE command.
            # It's quite likely then that the URL they're on is
            # http://ryf.com/_dcv351sr/r43/SNOOZE...2.days
            # The value of REQUEST.get('reminder-by-url') will then be
            # the reminder id that they snoozed.
            return self.http_redirect('snoozed', r=REQUEST.get('reminder-by-url'),
                                                 s=REQUEST.get('snoozed-by-url'))
        #elif REQUEST.get('login-by-url'):
        #    debug("DID login-by-url")
            # This is only true if someone has clicked on one of those
            # links with the passkey in an email, eg.
            # http://ryf.com/p-xfe523etg (or http://ryf.com/_xfe523etg)
            # We don't then want to continue to show that in the URL
            # so we redirect out to http://ryf.com/
            # since the user has already been logged in.
        #    url = PASSKEY_REGEX.sub('', REQUEST.URL)
        #    url = url.replace('index_html','')
        #    url = re.sub('\w(//)\w','/',url)
        #    return self.http_redirect(url, success=_("Logged in"))
        
        return self.index_html_template(self, REQUEST, RESPONSE)

    def _getRequestLanguages(self):
        """
        parse the request and return language list
        """

        if not hasattr(self, 'REQUEST'): return []
        
        # get browser accept languages
        browser_pref_langs = self.REQUEST.get('HTTP_ACCEPT_LANGUAGE', '')
        browser_pref_langs = browser_pref_langs.split(',')
        
        langs = []
        i = 0
        length = len(browser_pref_langs)
    
        # parse quality strings and build a tuple
        # like ((float(quality), lang), (float(quality), lang))
        # which is sorted afterwards
        # if no quality string is given then the list order
        # is used as quality indicator
        for lang in browser_pref_langs:
            lang = lang.strip().lower().replace('_','-')
            if lang:
                l = lang.split(';', 2)
                quality = []
        
                if len(l) == 2:
                    try:
                        q = l[1]
                        if q.startswith('q='):
                            q = q.split('=', 2)[1]
                            quality = float(q)
                    except: pass
            
                if quality == []:
                    quality = float(length-i)
    
                language = l[0]
                if language in self._getSupportedLanguages():
                    # if allowed the add language
                    langs.append((quality, language))
                i = i + 1
        
        # sort and reverse it
        langs.sort()
        langs.reverse()
                    
        # filter quality string
        langs = map(lambda x: x[1], langs)
        
        return langs
    
    def _getSupportedLanguages(self):
        return ('en','sv')

    def sendPasskeyReminder(self, email, REQUEST=None):
        """ try to send out a reminder """
        users = self._findUserByEmail(email)
        if users:
            user = users[0]
            uid = user.uid

            count_reminders = self.countReminders(uid)
        
            next_reminders = []
            _on_date = None
            for reminder in self._getReminders(uid, order='next_date'):
                if _on_date is None: # first time
                    _on_date = reminder.next_date.strftime('%Y%m%d')
                    next_reminders.append(reminder)
                elif reminder.next_date.strftime('%Y%m%d') == _on_date:
                    # also on the same date
                    next_reminders.append(reminder)
                else: # subsequence
                    break

            # now next_reminders is a list of records, all with the same
            # next_date stuff
            if next_reminders:
                if next_reminders[0].age_days <= 31:
                    next_reminder_on = next_reminders[0].next_date_month_formatted
                else:
                    next_reminder_on = next_reminders[0].next_date_year_formatted
            else:
                next_reminder_on = None
                    
            names = []
            for reminder in next_reminders:
                if reminder.name and reminder.email:
                    names.append('%s (%s)' % (reminder.name, reminder.email))
                elif reminder.name:
                    names.append(reminder.name)
                elif reminder.email:
                    names.append(reminder.email)
                
            next_reminder_name = ', '.join(names)
        
            message = self.passkey_reminder(self, self.REQUEST,
                      passkey=user.passkey, count_reminders=count_reminders,
                      next_reminder_name=next_reminder_name,
                      next_reminder_on=next_reminder_on
                      )
                      
            self.sendEmailNG(message, user.email, self.getWebmasterFromfield(),
                             _(u"Secret passkey reminder from RememberYourFriends.com"),
                             debug=DEBUG)
            if REQUEST:
                return self.show_passkey_sent(self, REQUEST, passkey=user.passkey,
                                              email=email)
                            
        elif REQUEST:
            template = getattr(self, 'log-in')
            submiterrors = {'email':_("No user account found by that email. Sorry.")}
            if not self.ValidEmailAddress(email):
                submiterrors = {'email':_("Not a valid email address anyway.")}
            REQUEST.set('submiterrors', submiterrors)
            return template(self, REQUEST)
        else:
            raise SubmitError, "No user by that email"
        
    def mostCommonCountryOptions(self):
        """ return the most likely and common occurances """
        return allcountries.MOST_COMMON
    
    def allCountryOptions(self):
        """ return all countries """
        return allcountries.ALL_COUNTRIES
    
    def saveSettings(self, REQUEST):
        """ save settings on the logged in user. """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure=_(u"Not logged in"))
        uid = self.getLoggedinUser().uid
        
        Rget = REQUEST.get
        html_emails = niceboolean(Rget('html_emails'))
        first_name = Rget('first_name','').strip()
        last_name = Rget('last_name','').strip()
        sex = Rget('sex','').strip().lower()
        if sex == 'woman': sex = 'female'
        elif sex == 'man': sex = 'male'
        assert sex in ('','male','female'), "Bad sex!! :)"
        website = Rget('website','').strip()
        country = Rget('country','').strip()
        if country:
            assert country in self.allCountryOptions(), "Bad country!"
        birthday = int(Rget('birthday',0))     ; assert birthday >= 0
        birthmonth = int(Rget('birthmonth',0)) ; assert birthmonth >= 0
        birthyear = int(Rget('birthyear',0))   ; assert birthyear >= 0
        if birthday and birthmonth:
            if birthyear:
                fmt = str(birthyear) + '/%s/%s'
            else:
                fmt = '2005/%s/%s'
            dstr = fmt % (zfill(birthmonth, 2),zfill(birthday, 2))
            try:
                DateTime(dstr)
            except:
                raise SubmitError, "Invalid day and month combination"

        self._saveUserDetails(uid, html_emails=html_emails, 
          first_name=first_name, last_name=last_name, sex=sex, website=website,
          country=country, birthday=birthday, birthmonth=birthmonth, 
          birthyear=birthyear)
          
        return self.http_redirect('settings', success=_(u"Settings saved."))
    
    def getUserDetails(self, uid):
        """ return all the user details """
        return self._getUser(uid, True)
        
    
    
    ##
    ## Unsubscription
    ## 
    
    def sendUnsubscribeLink(self, REQUEST=None):
        """ send an email with the users latest unsubscribe_passkey.
        Only if the user is logged in.
        """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure=_(u"Not logged in"))
        user = self.getLoggedinUser()
        
        # XXX to prevent DoS attacks on this unsubcribe verification
        # email one could do a check on the users modify_date, making sure
        # it wasn't updated too recently, like 1 second ago.
        
        # generate the new unsubscribe_passkey
        unsubscribe_passkey = self._generateUnsubscribePasskey(user.uid)
        rooturl = self.getRootURL()
        url = "%s/u_%s" % (rooturl, unsubscribe_passkey)

        # compose the email
        body = _(u"To verify that you want to unsubscribe from RememberYourFriends.com follow this link:\n")
        body += url
        body += "\n\n--\n%s" % self.getSignature()
        
        self.sendEmailNG(body, to=user.email, fr=self.getWebmasterFromfield(),
                       subject=_("Confirm unsubscription from RememberYourFriends.com"),
                       debug=DEBUG)
                       
        if REQUEST is not None:
            msg = _(u"A verification link has been sent to you")
            kw = dict(p=getRandomString(4), msg=msg, link_sent=True)
            return self.http_redirect('unsubscribe', **kw)
            
        
    def _generateUnsubscribePasskey(self, uid):
        passkey = Utils.nicepass(6, 4)
        while self._findByUnsubscribePasskey(passkey):
            passkey = Utils.nicepass(6, 4)
        self._updateUserUnsubscribePasskey(uid, passkey)
        return passkey
    
    def _unsubscribeUser(self, uid):
        """ seriously sad method, get rid of a user """
        try:
            print "UID", repr(uid)
            user = self._getUser(uid)
        except IndexError:
            raise IndexError, "Not user with uid=%r" % uid
        user_email = user.email
        LOG(self.__class__.__name__, WARNING, 
            "User %s has unsubscribed" % user_email)
            
        # Make sure the user isn't logged in or anything
        self.Logout(redirect=False)
        
        # remove all records of this user
        self._deleteAllReminders(uid)
        self._deleteUser(uid)
        

    ##
    ## Invitation of users
    ##
    
    def getFriendsEmailAddresses(self):
        """ return a list of all the email address of all reminders a user has """
        reminders = self.getReminders(only_with_email=True)
        return self.uniqify([x.email for x in reminders 
                                     if self.ValidEmailAddress(x.email)])
    
    def getFriendsEmailAddressesJSArray(self, variablename='emails'):
        """ same as getFriendsEmailAddresses() but returned as a formatted piece
        of Javascript code. """
        js = 'var %s=new Array(%s);'
        emails_fmt = ["'%s'"%x for x in self.getFriendsEmailAddresses()]
        return js % (variablename, ','.join(emails_fmt))
    
    def getDefaultInviteText(self, name=None):
        """ return the default text in the textarea for an invite """
        text ="""Hi %s,
    
I'm sending an invite for you to use RememberYourFriends.com to remember me :)
If you accept this invite (by clicking the link below) you can set up an account too with me being your first reminder.

<invite link will be placed here>
Note: clicking the link doesn't immediately sign you up.

--
"""
        if name is None:
            name = 'friend'
        else:
            name = name.strip()
        text = text % name
        return text.strip() + '\n' + self.getSignature()
        
        
    def sendInvite(self, email, text, periodicity, htmlformatted=False, name='', 
                   REQUEST=None):
        """ send an invite """
        if not self.isLoggedIn():
            return self.http_redirect(self.getRootURL(), 
                                      failure=_(u"Not logged in"),
                                      came_from=self.getRootURL()+'/send-invite')

        you = self.getLoggedinUser()
        
        # validate 
        submiterrors = {}
        
        email = email.strip()
        if email.find('<') > -1 and email.find('>') > -1 and email.find('"') > -1:
            name, email = self._parseAndSplitToAddress(email)
        
        if not name:
            for reminder in self._findRemindersByEmail(uid=you.uid, email=email):
                if reminder.name:
                    name = reminder.name
            
        if not self.ValidEmailAddress(email):
            submiterrors['email'] = _(u"Invalid email address")
        elif self._findUserByEmail(email):
            submiterrors['email'] = _(u"Already signed up")
        else:
            # check that an invite wasn't sent too recently
            prev_invites = self._findSentInvitationByEmail(you.uid, email)
            for prev_invite in prev_invites:
                if prev_invite.age_days < 1:
                    submiterrors['email'] = _(u"Invite sent less than a day ago")
                    break
            
            
        text = text.strip()
        # check that it contains some stuff
        
        _regex1 = re.compile(re.escape('RememberYourFriends.com'), re.I)
        _regex2 = re.compile(re.escape('<invite link will be placed here>'), re.I)
        
        if not text:
            submiterrors['text'] = _("Text was empty")
            if REQUEST:
                REQUEST.set('text', self.getDefaultInviteText())
                
        elif not _regex1.findall(text):
            submiterrors['text'] = _("Doesn't contain RememberYourFriends.com")
        elif not _regex2.findall(text):
            submiterrors['text'] = _("Doesn't contain '<invite link will be placed here>'")
            
        if not self._validatePeriodicity(periodicity):
            raise SubmitError, "Invalid periodicity %s" % periodicity
        
        if submiterrors and REQUEST:
            REQUEST.set('submiterrors', submiterrors)
            template = getattr(self, 'send-invite')
            return template(self, REQUEST, submiterrors=submiterrors)
        elif submiterrors:
            raise SubmitError, submiterrors      

        html_email = niceboolean(htmlformatted)
        # go ahead and send the invite
        siid = self._addSentInvitation(you.uid, email, name, periodicity,
                                       html_email)
        accept_link = self.getRootURL()+'/si%s' % siid
        
        msg = text.replace('<invite link will be placed here>', accept_link)
        
        
        html_msg = msg
        # Now, prepare the email
        if html_email:
            html_msg = html_msg.replace(accept_link,
              '<a href="%s">Click to accept invitation</a>' % accept_link)
            html_msg = newline_to_br(html_msg)
            
        send_from = you.email
        if you.name:
            send_from = '"%s" <%s>' % (you.name, you.email)
            
        send_to = email
        if name:
            sent_to = '"%s" <%s>' % (name, email)
        
        subject = _("Inviting you to RememberYourFriends.com")
        
        # send it
        if html_email:
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = subject
            msgRoot['From'] = send_from
            msgRoot['To'] = send_to
            msgRoot.preamble = 'This is a multi-part message in MIME format.'
            
            # Encapsulate the plain and HTML versions of the message body in an
            # 'alternative' part, so message agents can decide which they want to display.
            msgAlternative = MIMEMultipart('alternative')
            msgRoot.attach(msgAlternative)
            
            msgText = MIMEText(msg)
            msgAlternative.attach(msgText)

            # We reference the image in the IMG SRC attribute by the ID we give it below
            msgText = MIMEText(html_msg, 'html')
            msgAlternative.attach(msgText)

            self.sendEmail(msgRoot.as_string(), to=send_to,
                           fr=send_from,
                           subject=subject,
                           #charset='ISO-8859-1', #subtype='html',
                           debug=DEBUG,
                           #swallowerrors=True
                           )
        else:
            self.sendEmail(msg, to=send_to, 
                           fr=send_from,
                           subject=subject,
                           debug=DEBUG,
                           #swallowerrors=True
                           )
                           
        # exit stage left
        if REQUEST:
            msg = _(u"Sent inviation to %s") % send_to
            self.http_redirect('sent-invites', msg=msg)
        else:
            return siid
        
    def getSentInvitations(self, order_by=None, reverse=False):
        """ return all the users sent invitations """
        return self._getSentInvitations(uid=self.getLoggedinUser().uid,
                      order_by=order_by, reverse=reverse)
                      
            
    def _invitableReminder(self, rid, uid=None):
        """ return true if this can be invited by you.
        That is true if the email is valid and the persons
        hasn't already signed up and if you haven't already 
        sent an invitation in the last 7 days.
        """
        reminder = self._getReminder(rid)
        email = reminder.email

        if not self.ValidEmailAddress(reminder.email):
            return False

        invites = self._findSentInvitationByEmail(uid, email)
        for invite in invites:
            if invite.age_days <= 7:
                return False
            
        return True
    
    ## 
    ## Birthday stuff
    ##
    
    def getUpcomingBirthdays(self, sort=False):
        """ return a users' all birthday's """
        user = self.getLoggedinUser()
        return self._getUpcomingBirthdays(user.uid, sort=sort)
    
    def birthday_input(self, rid):
        """ return the form for the HTML input for birthday """
        return '''<input name="dob" id="dob" value="" onfocus="openCalendar('dob')" />'''
    
    
    def getRandomBdayImage(self):
        """ return one of the many paths to the bday """
        alts = ['bday-1.gif', 'bday-2.gif', 'bday-3.gif', 
                'bday-4.gif', 'bday-5.gif', 'bday-6.gif']
        shuffle(alts)
        rooturl = self.getRoot().absolute_url_path()
        if rooturl == '/':
            return rooturl + alts[0]
        return rooturl + '/' + alts[0]
    

    def foo(self):
        """ sure """
        debug("foo()", steps=3)
        return str(DateTime())
    
    
            

templates = ('zpt/HeaderFooter',
             'zpt/ManagementHeaderFooter',
             {'f':'dtml/screen.css', 'optimize':'css'},
             'zpt/show-general-error',
             {'f':'zpt/index_html', 'n':'index_html_template', 
              'optimize':OPTIMIZE and 'xhtml'},
             'dtml/welcome_message',
             'dtml/passkey_reminder',
             'zpt/change-reminders',
             'zpt/add',
             'zpt/edit',
             'zpt/logged-out',
             'zpt/log-in',
             ('zpt/show_sent_reminders', 'show_sent_reminders_template'),
             ('zpt/show_logged_in', 'show_logged_in_template'),
             ('zpt/show_not_logged_in', 'show_not_logged_in_template'),
             'zpt/snoozed',
             'zpt/show_passkey_sent',
             'zpt/sent-reminders',
             'zpt/settings',
             'zpt/stats',
             'zpt/faq',
             'zpt/peter', 
             'zpt/unsubscribe',
             'zpt/unsubscribed',
             'zpt/send-invite',
             'zpt/sent-invites',
             'zpt/accept-invite',
             {'f':'dtml/home.js', 'optimize':OPTIMIZE and 'js'},
             'zpt/i-hate-spam',
             ('zpt/introspector/find_users', 'manage_find_users'),
             ('zpt/introspector/show_user', 'manage_show_user'),
             'dtml/calendar.css',
            )
            
addTemplates2Class(Homepage, templates)

from Products.FriedZopeBase.Zope import registerImages
_images = [x for x 
            in os.listdir(os.path.join(package_home(globals()), 'images'))
            if anyTrue(x.lower().endswith, ('.jpg','.png','.gif','.ico'))]
            
registerImages(Homepage, _images, globals(), rel_path='images')



security = ClassSecurityInfo()
security.declareProtected(VMS, 'manage_find_users')
security.declareProtected(VMS, 'manage_show_user')
security.declareProtected(VMS, 'introspector')
security.apply(Homepage)

setattr(Homepage, 'introspector', Homepage.manage_find_users)




InitializeClass(Homepage)


setattr(Homepage, 'UNICODE_ENCODING', UNICODE_ENCODING)

