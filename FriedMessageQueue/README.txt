Fried Message Queue

 is a Zope product for piling up email messages so they can be sent in
a digested format. Since the Fried Message Queue is based on
FriedZopeBase it has it's own sendEmail() method which it uses to send
the digested emails. All you have to do from somewhere else is to send
all emails to the message queue instead of directly to sendEmail() (or
equivalent) and then let a cron job clear the message queue every now
and then. 