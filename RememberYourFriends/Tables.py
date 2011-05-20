##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
from Acquisition import aq_parent, aq_inner

# Our friend...
#from Products.FriedZopeBase.Bases import HomepageBase
#from Products.FriedZopeBase import Utils as FriedUtils
#from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

# Product
from SQL import SQLUsers, SQLCommon, SQLReminders, SQLSentInvitations
from Constants import *
#import Utils


#------------------------------------------------------------------------------

tablename2seq = {
    'users': 'users_uid_seq',
    'user_details': 'user_details_duid_seq',
    'reminders': 'reminders_rid_seq',    
    'sent_invitations': 'sent_invitations_siid_seq',
    }

class Common(SQLCommon):

    def _getNextId(self, sequence_name):
        """ return the next id from the sequence or tablename """
        # if the sequence_name is a table name in fact, 
        # sort that out
        sequence_name = tablename2seq.get(sequence_name, sequence_name)
        return self.SQLGetNextId(sequence_name=sequence_name)[0].next_id
    
#------------------------------------------------------------------------------    

class SentInvitations(SQLSentInvitations):
    
    def _addSentInvitation(self, uid, email, name, periodicity, html_email):
        siid = self._getNextId('sent_invitations')
        sql_insert = self.SQLInsertInvitation
        sql_insert(siid=siid, uid=uid, email=email, name=name, 
                   periodicity=periodicity,
                   html_email=html_email)
        return siid
    
    def _getSentInvitations(self, uid, order_by=None, reverse=False):
        sql_select = self.SQLSelectSentInvitationsByUser
        return sql_select(uid=uid, order_by=order_by, reverse=reverse)
    
    def _findSentInvitationByEmail(self, uid, email):
        sql_select = self.SQLFindInvitationByEmail
        return sql_select(uid=uid, email=email)
    
    def _getSentInvitation(self, siid):
        sql_select = self.SQLSelectSentInvitation
        return sql_select(siid=siid)[0]
    
    def getSentInvitation(self, siid):
        return self._getSentInvitation(siid)
    
    def _setSentInvitationClicked(self, siid, clicked=True):
        sql_update = self.SQLUpdateSentInvitationClicked
        sql_update(siid=siid, clicked=clicked)
        

#------------------------------------------------------------------------------

class Users(SQLUsers, SentInvitations, Common):


    def _countTotalUsers(self):
        sql_select = self.SQLCountTotalUsers
        return sql_select()[0].count
    
    def hasUser(self, uid):
        """ check if the record exists """
        return len(self.SQLSelectUser(uid=uid)) > 0
    
    def _getUser(self, uid, full=False):
        if full:
            return self.SQLSelectUserFull(uid=uid)[0]
        else:
            return self.SQLSelectUser(uid=uid, debug__=1)[0]
        
    def getUser(self, uid, full=False):
        return self._getUser(uid, full=full)
    
    def _findUserByEmail(self, email):
        sql_select = self.SQLSelectUserByEmail
        return sql_select(email=email)
    
    def _findUserByPasskey(self, passkey):
        sql_select = self.SQLSelectUserByPasskey
        return sql_select(passkey=passkey)
    
    def _addUser(self, email, passkey='', name='', html_emails=False):
        uid = self._getNextId('users')
        sql_insert = self.SQLInsertUser
        sql_insert(uid=uid, email=email, passkey=passkey, name=name,
                   temporary_passkey='',
                   html_emails=html_emails)
        return uid

    def _updateUserPasskey(self, uid, passkey):
        sql_update = self.SQLUpdateUserPasskey
        sql_update(uid=uid, passkey=passkey)

    def _findByPasskey(self, passkey):
        return self.SQLFindUserByPasskey(passkey=passkey)

    
    def _updateUserUnsubscribePasskey(self, uid, passkey):
        sql_update = self.SQLUpdateUserUnsubscribePasskey
        sql_update(uid=uid, passkey=passkey)
        
    def _findByUnsubscribePasskey(self, passkey):
        return self.SQLFindUserByUnsubscribePasskey(passkey=passkey)
    
    def _updateLastLoginTime(self, uid):
        """ update the last_login_time """
        self.SQLUpdateLastLoginTime(uid=uid)

    def _saveUserDetails(self, uid, html_emails=False, **kw):
        """ save the details. Bare in mind that a user might not have
        a user_details record """
        sql_update = self.SQLUpdateUser
        sql_update(uid=uid, html_emails=html_emails)
        
        full_user = self._getUser(uid, True)
        if full_user.duid:
            duid = full_user.duid
        else:
            duid = self._getNextId('user_details')
            sql_insert = self.SQLInsertUserDetails
            sql_insert(duid=duid, uid=uid)
            
        sql_update = self.SQLUpdateUserDetails
        sql_update(duid=duid, **kw)

        
    def _deleteUser(self, uid):
        """ delete the user """
        for method in (self._deleteAllReminders,
                       self.SQLDeleteInvitations,
                       self.SQLDeleteUserDetails,
                       self.SQLDeleteUser
                       ):
            method(uid=uid)
        
    def _getUsers(self, order_by=None, reverse=False):
        """ return a lot about users """
        return self._findUsers(order_by=order_by, reverse=reverse)
    
    def _findUsers(self, uid=None, email='', passkey='', first_name='', last_name='',
                   order_by=None, reverse=False):
        """ return users with regular matching """
        sql_select = self.SQLFindUsers
        return sql_select(uid=uid, email=email, passkey=passkey, 
                          first_name=first_name, last_name=last_name,
                          order_by=order_by, reverse=reverse,
                          )
        

    

#------------------------------------------------------------------------------

class Reminders(SQLReminders):

    
    def _getBirthdays(self, t_minus_days=0):
        """ return all birthdays of all uids where the 
        birthday is == (today + t_minus_days)
        """
        sql_select = self.SQLSelectAllBirthdays
        return sql_select(days_offset=t_minus_days)
    
    def _getUpcomingBirthdays(self, uid, sort=False):
        sql_select = self.SQLSelectUpcomingBirthdays
        return sql_select(uid=uid, sort=sort)
    
    
    def _findRemindersByEmail(self, uid, email):
        sql_select = self.SQLFindRemindersByEmailByUser
        return sql_select(uid=uid, email=email)
    
    def _snoozeReminder(self, rid, interval):
        
        # by default the next_date is now reset
        reset_next_date = False
        # if the reminder has been snoozed before, 
        # (ie. snooze>0) the user probably just wants to snooze
        # it a bit more. If the reminder isn't already snoozed
        # (ie. snooze==0) then you will want to reset the next_date
        reminder = self._getReminder(rid)
        if reminder.snooze == 0:
            reset_next_date = True
        
        sql_update = self.SQLUpdateReminderSnooze
        
        sql_update(rid=rid, interval=interval, 
                   reset_next_date=reset_next_date)

    def _countTotalReminders(self):
        sql_select = self.SQLCountTotalReminders
        return sql_select()[0].count

    def _countTotalSentReminders(self):
        sql_select = self.SQLCountTotalSentReminders
        return sql_select()[0].count
    
    def _deleteReminder(self, rid):
        sql_delete = self.SQLDeleteReminder
        sql_delete(rid=rid)

    def _pauseReminder(self, rid):
        self._toggleReminderPause(rid, pause=True)
        
    def _resumeReminder(self, rid):
        self._toggleReminderPause(rid, pause=False)
        
    def _toggleReminderPause(self, rid, pause=None):
        if pause is None:
            reminder = self._getReminder(rid)
            pause = not reminder.paused
        sql_update = self.SQLUpdateReminderPaused
        sql_update(rid=rid, pause=pause)
        
    
    def _editReminder(self, rid, name, email, periodicity, 
                      birthday=None, birthmonth=None, birthyear=None):
        sql_update = self.SQLUpdateReminder
        sql_update(rid=rid,
                   name=name,
                   email=email,
                   periodicity=periodicity,
                   birthday=birthday,
                   birthmonth=birthmonth,
                   birthyear=birthyear)        
    
    
    def _getReminder(self, rid):
        return self.SQLSelectReminder(rid=rid)[0]
    
    def _addReminder(self, uid, name, email, periodicity,
                     birthday=None, birthmonth=None, birthyear=None):
        rid = self._getNextId('reminders')
        sql_insert = self.SQLInsertReminder
        sql_insert(rid=rid, uid=uid, 
                   name=name,
                   email=email,
                   periodicity=periodicity,
                   birthday=birthday,
                   birthmonth=birthmonth,
                   birthyear=birthyear)
        return rid
    
    def _countReminders(self, uid):
        return self.SQLCountUserReminders(uid=uid)[0].count
    
    
    def _getReminders(self, uid, order=None, reverse=False,
                      only_with_email=False,
                      include_invite_option=False):
        sql_select = self.SQLSelectUserReminders
        return sql_select(uid=uid, order=order, reverse=reverse,
                          only_with_email=only_with_email,
                          include_invite_option=include_invite_option)
    
    
    ##
    ## Figuring out who to send to
    ##

    def _getRemindersToSend(self, max_send, order=None):
        """ return the reminders that should be sent now """
        sql_select = self.SQLSelectRemindersToSend
        return sql_select(limit=max_send, order=order)
    
    def _getReminderlessUsers(self, order=None):
        """ return the users who don't have any reminders set up """
        sql_select = self.SQLSelectReminderlessUsers
        return sql_select(order=order)    
    
    def _resetReminder(self, rid):
        """ set the next_date to the next date and reset the snooze """
        sql_update = self.SQLResetReminder
        sql_update(rid=rid)
        
    ##
    ## Sent Reminders
    ##
    
    def _logSentReminder(self, rid):
        reminder = self._getReminder(rid)
        self.SQLInsertSentReminder(rid=rid, snoozed=reminder.snooze)
        
        
    def _deleteSentReminders(self, rid):
        sql_delete = self.SQLDeleteSentReminders
        sql_delete(rid=rid)        
    
    def _getSentReminders(self, uid, offset=0, limit=1000, count=False):
        if count:
            sql_select = self.SQLCountSentReminders
            return sql_select(uid=uid)[0].count
        else:
            sql_select = self.SQLSelectSentReminders
            return sql_select(uid=uid, offset=offset, limit=limit)
    
    def _getSentRemindersByReminder(self, rid, order=None, reverse=False, limit=None):
        sql_select = self.SQLSelectSentRemindersByReminder
        return sql_select(rid=rid, order=order, reverse=reverse, limit=limit)
    
    def _countSentRemindersByReminder(self, rid):
        sql_select = self.SQLCountSentRemindersByReminder
        return sql_select(rid=rid)[0].count
    
    
    ##
    ## Sent Reminders stat
    ##
    
    def _getMostRemindersSentStats(self, limit=None):
        sql_select = self.SQLSelectMostRemindersSentStats
        return sql_select(limit=limit)

    def _getFirstReminderSent(self):
        sql_select = self.SQLSelectExtremeSentReminder
        return sql_select(first=True)[0]
    
    def _getLastReminderSent(self):
        sql_select = self.SQLSelectExtremeSentReminder
        return sql_select(first=False)[0]
    
    ##
    ## Delete
    ##
    
    def _deleteAllReminders(self, uid):
        """ delete and destruct """
        sql_delete = self.SQLDeleteSentRemindersByUser
        sql_delete(uid=uid)
        
        sql_delete = self.SQLDeleteRemindersByUser
        sql_delete(uid=uid)
        
    

        