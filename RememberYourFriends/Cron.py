##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys, random
from traceback import print_exc
import cStringIO

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

from Products.PythonScripts.standard import newline_to_br
from Products.FriedZopeBase.Utils import niceboolean, unicodify

# Product
from Tables import Reminders
from I18N import _
from Constants import *
from Utils import debug


class CronBase(Reminders):
    
    def sendbirthdayreminders(self, verbose=False):
        """ send a birthday reminder if a birthday is today or 7 days away. """
        try:
            return self._sendbirthdayreminders(verbose)
        except:
            try:
                message = "Error on RememberYourFriends.com\n"
                message += "%s\n%s\n" % (sys.exc_type, sys.exc_value)
                out = cStringIO.StringIO()
                print_exc(file=out)
                message += out.getvalue()
                
                self.sendEmailNG(message, DEVELOPER_EMAIL, WEBMASTER_EMAIL,
                       "RememberYourFriends.com Error in cronjob (sendbirthdayreminders)!!",
                       debug=DEBUG)
            except:
                try:
                    err_log = self.error_log
                    err_log.raising(sys.exc_info())
                except:
                    pass

            raise        
        
    def _sendbirthdayreminders(self, verbose=False):
        
        seven_days_birthdays = self._getBirthdays(t_minus_days=7)
        today_birthdays = self._getBirthdays(t_minus_days=0)

        # lump them together per user
        user_birthdays = {}
        for birthday in list(seven_days_birthdays) + list(today_birthdays):
            uid = birthday.uid
            prev = user_birthdays.get(uid, [])
            prev.append(birthday)
            user_birthdays[uid] = prev
            
        count = 0
        for uid, birthdays in user_birthdays.items():
            self._sendUserBirthdayReminders(uid, birthdays)
            count += 1

        return "Sent %s birthday reminders" % count
        
    def _sendUserBirthdayReminders(self, uid, birthdays):
        """ create a merged message of the birthdays and send it """
        subject, msg, html_msg = self._mergeBirthdaysIntoMessage(birthdays, uid)
        # Send it!!
        user = self._getUser(uid)
        
        if user.html_emails:
            self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                   subject, msg, html_msg)
        else:
            self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                   subject, msg)

        
        
    def _mergeBirthdaysIntoMessage(self, birthdays, uid):
        """ put all birthday messages into one """
        all_lines = []
        all_html_lines = []
        all_best_names = []
        for birthday in birthdays:
            lines = [_("Don't forget, it's")]
            html_lines = lines[:]
            if birthday.name and birthday.email:
                best_name = birthday.name
                name = u"%s's" % birthday.name
                _html = u'<a href="mailto:%s"><strong>%s\'s</strong></a>'
                html_name = _html % (birthday.email, birthday.name)
            elif birthday.email:
                best_name = name = birthday.email
                _html = '<a href="mailto:%s"><strong>%s\'s</strong></a>'
                html_name = _html % (birthday.email, birthday.email)
            else:
                name = best_name = "%s's" % birthday.name
                best_name = birthday.name
                html_name = '<strong>%s\'s</strong>' % birthday.name
                
            if birthday.birthday_today:
                lines.append('\t%s birthday today!' % name)
                html_lines.append('&nbsp;'*4 + '%s birthday today!' % html_name)
            elif birthday.days_till == 1:
                lines.append('\t%s birthday in one day!' % name)
                html_lines.append('&nbsp;'*4 + '%s birthday in one day!' % html_name)
            else:
                lines.append('\t%s birthday in %s days!' % (name, birthday.days_till))
                html_lines.append('&nbsp;'*4 + '%s birthday in %s days!' % \
                                  (html_name, birthday.days_till))
                
            all_best_names.append(best_name)
            all_lines.append('\n'.join(lines))
            all_html_lines.append('\n'.join(html_lines)+'\n\n')
            
        rooturl = self.getRootURL()
        user = self._getUser(uid)
        plain_footer, html_footer = self._getSigntureWithOptout(rooturl, user.passkey)
        
        all_lines.append(plain_footer)
        all_html_lines.append(html_footer)
        
        msg = '\n\n'.join(all_lines)
        html_msg = '\n'.join(all_html_lines)
        html_msg = newline_to_br(html_msg)

        if len(all_best_names) == 1:
            subject = _("RememberYourFriends.com birthday reminder for") + \
              ' %s' % all_best_names[0]
        else:
            subject = _("RememberYourFriends.com birthday reminder ") + \
              DateTime().strftime('%d %B')
              
        return subject, msg, html_msg
        
    
    def sendnaggings(self, verbose=False):
        """ wrap the real workhorse _sendnaggings() with some solid
        error reporting.
        """
        try:
            return self._sendnaggings(verbose)
        except:
            try:
                message = "Error on RememberYourFriends.com\n"
                message += "%s\n%s\n" % (sys.exc_type, sys.exc_value)
                out = cStringIO.StringIO()
                print_exc(file=out)
                message += out.getvalue()
                
                self.sendEmailNG(message, DEVELOPER_EMAIL, WEBMASTER_EMAIL,
                       "RememberYourFriends.com Error in cronjob (sendnaggings)!!",
                       debug=DEBUG)
            except:
                try:
                    err_log = self.error_log
                    err_log.raising(sys.exc_info())
                except:
                    pass

            raise        
        
    def _sendnaggings(self, verbose=False):
        """ send out a reminder to those people who have signed up but haven't
        added any reminders.
        The 'max_send' parameter is ignored.
        """
        sent_to = []
        
        rooturl = self.getRootURL()
        reminderless_users = self._getReminderlessUsers()
        subject = _("Getting started with RememberYourFriends.com")
        for user in reminderless_users:
            html = bool(user.html_emails)
            lines = []
            html_lines = []
            add_date = user.add_date_formatted
            para1 = _("You signed up to RememberYourFriends.com on the")+\
                    " " + add_date + " " +\
                    _("but haven't set up any reminders yet.")
            lines.append(para1)
            html_lines.append(para1)
            
            add_reminders_url = '%s/_%s/add' % \
                                   (rooturl, user.passkey)
            html_lines.append(_('To add some, <a href="%s">go to the <b>Add a new reminder</b> page</a>') %\
                              add_reminders_url)
                              
            lines.append(_('To add some, go to the Add a new reminder page:')+\
                         '\n'+ add_reminders_url)
                             
            lines.append('\n')
            html_lines.append('\n')
            plain, html_ = self._getSigntureWithOptout(rooturl, user.passkey)
            html_lines.append(html_)
            lines.append(plain)
                
            msg = '\n\n'.join(lines)
            html_msg = '\n'.join(html_lines)
            html_msg = newline_to_br(html_msg)
            
            if html:
                self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                       subject, msg, html_msg)
            else:
                self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                       subject, msg)
                                       
            sent_to.append(user.email)
            
        if sent_to:
            return "Sent to %s" % ', '.join(sent_to)
        else:
            return "Didn't send to anyone"
        
    
    def sendreminders(self, max_send=100, verbose=False):
        """ the method to be hit by the cron job.
        Actually it's _sendreminders() which is doing the real job.
        This method is just a wrapper that will make sure all errors are
        logged fully."""
        try:
            return self._sendreminders(max_send, verbose)
        except:
            try:
                message = "Error on RememberYourFriends.com\n"
                message += "%s\n%s\n" % (sys.exc_type, sys.exc_value)
                out = cStringIO.StringIO()
                print_exc(file=out)
                message += out.getvalue()
                
                self.sendEmailNG(message, DEVELOPER_EMAIL, WEBMASTER_EMAIL,
                       "RememberYourFriends.com Error in cronjob!!",
                       debug=DEBUG)
                
            except:
                try:
                    err_log = self.error_log
                    err_log.raising(sys.exc_info())
                except:
                    pass

                
            raise

        
    def _sendreminders(self, max_send=100, verbose=False):
        """ the method to be hit by the cron job """
        verbose = niceboolean(verbose)
        max_send = int(max_send)
        msgs = []
        
        records = self._getRemindersToSend(max_send, order='uid')
        
        count = 0

        uid = None
        
        reminders = [] # group them in a list like this
        for record in records:
            if uid is None:
                reminders.append(record)
                uid = record.uid
            elif uid == record.uid:
                reminders.append(record)
            else:
                # different user
                self.sendUsersReminders(uid, reminders)
                count += len(reminders)
                
                uid = record.uid
                reminders = [record]
                
        if reminders:
            self.sendUsersReminders(uid, reminders)
            count += len(reminders)
            
        if verbose and count:
            msg = "Sent %s reminders\n" % count
            msg += '\n'.join(msgs)
            LOG("RememberYourFriends.Cron", INFO, msg)
            return msg
        
        else:
            return "Sent %s reminders" % count
            
            
    def sendUsersReminders(self, uid, reminders):
        """ 
                
            if reminder.name and reminder.email:
                name = "%s (%s)" % (reminder.name, reminder.email)
            elif reminder.email:
                name = reminder.email
            else:
                name = reminder.name
                
            if reminder.snooze:
                msgs.append("Need to send snoozed reminder to %s" % name)
            else:
                msgs.append("Need to send reminder to %s" % name)
        """
        if not reminders:
            return
        
        all_lines = []
        all_html_lines = []
        all_urls = {}
        all_names = []
        user = self._getUser(uid, True)
        
        # prepare the extra text that we'll throw into the email
        nag = html_nag = ''
        if random.randint(1,3)==1 and not (\
           user.first_name or \
           user.last_name):
            # ok, this time we'll nag about getting them to enter their name
            html_nag = _("You still haven't completed your full name.\n")
            settings_url = '%s/_%s/settings' % (self.getRootURL(), user.passkey)
            nag = html_nag + _('Follow this link to change your settings: %s') % settings_url
            html_nag += _('Do that on the <a href="%s">your settings page</a>.') % settings_url
            
        elif random.randint(1,3) == 1 and len(reminders) == 1 and \
          self._invitableReminder(reminders[0].rid, uid=uid):
            r = reminders[0]
            if r.name:
                name = r.name
            else:
                name = r.email
                
            name = unicodify(name, UNICODE_ENCODING)
            
                
            #LOG("RememberYourFriends.Cron", INFO, "name =%r" % name)
            html_nag = _(u"Do you want to invite %s to also use RememberYourFriends.com?") % name
            html_nag += ' '
            nag = html_nag
            invite_url = '%s/_%s/r%s/send-invite' % (self.getRootURL(), user.passkey, r.rid)
            nag += _('If so, click this link: %s') % invite_url
            html_nag += _('If so, go to the <a href="%s">Send invite page</a>') % invite_url
            
        elif random.randint(1,4) == 1:
            send_invite_url = '%s/_%s/send-invite' % (self.getRootURL(), user.passkey)
            html_nag = _(u"You can invite more friends to RememberYourFriends.com")
            nag = html_nag + ' ' + _('on this page: %s') % send_invite_url
            html_nag += ' ' + _('on the <a href="%s">Send invite page</a>.') % send_invite_url
            
        elif random.randint(1,3) == 1:
            add_reminders_url = '%s/_%s/add' % \
                                (self.getRootURL(), user.passkey)
            html_nag = _(u"To add more reminders of other friends or change your current reminders")
            nag = html_nag + ' '+ _("go to this page: %s") % add_reminders_url
            html_nag += ' ' + _('go to the <a href="%s">Add a new reminder page</a>.') % add_reminders_url
            
        

        rooturl = self.getRootURL()
        
        for reminder in reminders:
            if reminder.paused:
                self._resetReminder(reminder.rid)
                continue
            
            lines = [_("You are being reminded to remember:")]
            html_lines = lines[:]
            if reminder.name and reminder.email:
                best_name = reminder.name
                name = "%s, %s" % (reminder.name, reminder.email)
                _html = '<a href="mailto:%s"><strong>%s</strong></a>'
                html_name = _html % (reminder.email, reminder.name)
            elif reminder.email:
                best_name = name = reminder.email
                _html = '<a href="mailto:%s"><strong>%s</strong></a>'
                html_name = _html % (reminder.email, reminder.email)
            else:
                name = best_name = reminder.name
                html_name = '<strong>%s</strong>' % reminder.name
            name = unicodify(name, UNICODE_ENCODING)
            html_name = unicodify(html_name, UNICODE_ENCODING)
            lines.append('\t%s\n' % name)
            html_lines.append('&nbsp;'*4 + '%s\n' % html_name)
            all_names.append(name)
            
            count_sent_reminders = self._countSentRemindersByReminder(reminder.rid)
            
            if count_sent_reminders:
                rid = reminder.rid
                last_reminder = self._getSentRemindersByReminder(rid, limit=1,
                                                              order='add_date',
                                                              reverse=True)[0]
                if count_sent_reminders == 1:
                    msg = _("One reminder sent before.")
                else:
                    msg = _("%s reminders sent before.") % count_sent_reminders
                if last_reminder.snoozed:
                    msg +=  " " + _("It was snoozed %s days") % last_reminder.snoozed
                lines.append(msg)
                html_lines.append(msg)
            
            lines.append(_("Snooze options:"))
            html_snooze_msg = _("Snooze this:")
            urls = []
            
            _options = ('1 day', '2 days', '1 week','1 month')
            for e in _options:
                url = "%s/_%s/r%s/SNOOZE...%s" %(rooturl, user.passkey,
                                                  reminder.rid, e.replace(' ','.'))
                                                  
                all_urls[url] = e
                urls.append(url)
                
            html_snooze_msg += ' ' + ', '.join(urls)
            for url, label in all_urls.items():
                html_snooze_msg = html_snooze_msg.replace(url, 
                                    '<a href="%s">%s</a>' % (url, label))
            
            lines.extend(urls)
            html_lines.append(html_snooze_msg)
            
            best_name = unicodify(best_name, UNICODE_ENCODING)
            
            if reminder.birthday and reminder.birthmonth:
                LOG("RememberYourFriends.Cron", INFO, "best_name =%r" % best_name)
                _edit_msg = _(u"Change settings for %s") % best_name
                _edit_href = '%s/_%s/edit?rid=%s&amp;sbf=y' %\
                             (rooturl, user.passkey, reminder.rid)
            else:
                _edit_msg = _(u"Do you know %s's birthday?") % best_name
                _edit_href = '%s/_%s/edit?rid=%s' % (rooturl, user.passkey, reminder.rid)
                
            html_lines.append('<a href="%s" style="font-size:80%%">%s</a>' %\
                              (_edit_href, _edit_msg))


            all_lines.append('\n'.join(lines))
            LOG("RememberYourFriends.Cron", INFO, "html_lines =%s"%html_lines)
                        

            all_html_lines.append('\n'.join(html_lines)+'\n\n')
            
            # remember that we sent something on this reminder
            self._logSentReminder(reminder.rid)
            
            # move the next_date forward and reset the snooze
            self._resetReminder(reminder.rid)
            
        
        if nag:
            all_lines.append(nag+'\n')
        if html_nag:
            all_html_lines.append(html_nag+'\n')

        plain_footer, html_footer = self._getSigntureWithOptout(rooturl, user.passkey)
        all_lines.append(plain_footer)
        all_html_lines.append(html_footer)
        
        msg = '\n\n'.join(all_lines)
        html_msg = '\n'.join(all_html_lines)
        html_msg = newline_to_br(html_msg)

        subject = _("RememberYourFriends.com reminder: ") + DateTime().strftime('%d %B')

        # Send it!!
        user = self._getUser(uid)
        
        
        if user.html_emails:
            self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                   subject, msg, html_msg)
        else:
            self._sendEmailWrapped(user.email, self.getWebmasterFromfield(), 
                                   subject, msg)

                                   
    def _sendEmailWrapped(self, to, fr, subject, msg, html_msg=None):
        """ send the email as html+plain or just as plain """
        self.sendEmailNG(msg, to, fr, subject, html_msg=html_msg, debug=DEBUG)
        return
        if html_msg:
            
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = subject
            msgRoot['From'] = fr
            msgRoot['To'] = to
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

            self.sendEmail(msgRoot.as_string(), to=to,
                           fr=fr,
                           subject=subject,
                           #charset='ISO-8859-1', #subtype='html',
                           debug=DEBUG,
                           #swallowerrors=True
                           )
        else:
            self.sendEmail(msg, to=to, fr=fr,
                           subject=subject,
                           debug=DEBUG,
                           #swallowerrors=True
                           )
            

    def _getSigntureWithOptout(self, rooturl, passkey):
        """ return a tuple with the (plain, html) signature with the opt-out link in it. """

        unsubscribe_url = "%s/_%s/unsubscribe" %(rooturl, passkey)
        unsubscribe_link_start = _("To unsubscribe go to")
        unsubscribe_link = "%s %s" % (unsubscribe_link_start, unsubscribe_url)
        unsubscribe_link_html = '%s <a href="%s">the unsubscribe page</a>' \
                      % (unsubscribe_link_start, unsubscribe_url)
        
        plain = '--\n%s\n%s' % (self.getSignature(), unsubscribe_link)
        
        sig_wrapper = '<span style="font-size:0.9em;color:#666">--\n%s\n%s</span>'
        sig_url_wrapper = '<a href="%s" style="font-weight:bold">RememberYourFriends.com</a>'
        root_url_with_passkey = '%s/_%s' % (rooturl, passkey)
        signature = self.getSignature().replace('RememberYourFriends.com',
                                                sig_url_wrapper % root_url_with_passkey)
        
        html = sig_wrapper % (signature, unsubscribe_link_html)
        return plain, html
        
            
        
