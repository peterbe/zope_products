##
## FriedMessageQueue
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##


# python
import os, re, sys
from sets import Set

# Zope
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime


# Our friend...
from Products.FriedZopeBase.Bases import HomepageBase, HomepageBTreeBase, SimpleItemBase
from Products.FriedZopeBase import Utils as FriedUtils
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

# Product
from Constants import *
import Utils

#-----------------------------------------------------------------------------
def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())
    
__version__=open(os.path.join(package_home(globals()), 'version.txt')).read().strip()

#-----------------------------------------------------------------------------



manage_addMessageQueueForm = DTMLFile('dtml/addMessageQueueForm', globals())

def manage_addMessageQueue(dispatcher, id, title='', REQUEST=None):
    """ create instance """
    
    dest = dispatcher.Destination()
        
    instance = MessageQueue(id, title)
    dest._setObject(id, instance)
    object = dest._getOb(id)
    #object.DeployStandards()
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
        
        
#-----------------------------------------------------------------------------

class MessageQueue(HomepageBase):
    """ MessageQueue of FriedMessageQueue """
    
    meta_type = METATYPE_MESSAGEQUEUE
    security = ClassSecurityInfo()
    
    _properties=({'id':'title',         'type':'string', 'mode':'w'},
                 {'id':'default_from_address','type':'string', 'mode':'w',
                  'label':'The email address used to send from when having to do a merge'},
                  )
                
    this_package_home = package_home(globals())
    manage_options = ({'label':'Documentation', 'action':'manage_Documentation'},) +\
                     HomepageBase.manage_options[0:]
    
    
    def __init__(self, id, title=''):
        """ init """
        self.id = id
        self.title = title
        self.default_from_address = DEFAULT_FROMADDRESS
        
        # This is where we store a list of message for each destination.
        # A destination is a string email address or even a list of email addresses;
        # in fact, it's anything that can be the To: field of an email. 
        self.messages_to = {}
        
        self._last_log = None
        self._last_sendall = None
        
        
        
    def getId(self):
        """ return id """
        return self.id
    
    def getTitle(self):
        """ return title """
        return self.title
    
    def _updateMessagesTo(self, messageids):
        """ clear some messageids """
        messages_to = self.messages_to
        new_messages_to = {}
        for k, ids in messages_to.items():
            ids = [x for x in ids if x not in messageids]
            if ids:
                new_messages_to[k] = ids
        self.messages_to = new_messages_to
        
    
    def getLastLog(self):
        """ return what the last message was """
        return self._last_log
    
    def getLastSendall(self):
        """ return when the last sendAll was called """
        return self._last_sendall
    
    def countAllMessages(self):
        """ return how many messages there are """
        return len(self.objectValues(METATYPE_MESSAGE))
    
    def countUniqueMessages(self):
        """ return how many messages there are if you group those that 
        will be sent to the same person the same way """
        return len(self.messages_to.keys())

    def sendEmail(self, msg, to, fr, subject,
                  mcc=None, mbcc=None, subtype='plain', charset='us-ascii',              
                  swallowerrors=False, debug=None,
                  construct_body=False # for legacy reasons
                  ):
        """ intercepting method that just creates a message queue message """
        genid = str(float(DateTime()))+Utils.safeId(to)
        genid = genid[:25]
        while hasattr(self, genid):
            genid = str(float(DateTime()))+Utils.safeId(to)
            genid = genid[:25]
        
        assert isinstance(to, basestring), "'to' parameter must be string (not %r)" % to
        if not to:
            raise "BadRequest", "Can't send email with blank to header"
        
        inst = Message(genid, msg, to, fr, subject,
                  mcc, mbcc, subtype, charset,              
                  swallowerrors, debug,
                  construct_body)
        self._setObject(genid, inst)
        
        messages_to = self.messages_to
        hashed = self._hashMessageData(to, debug=debug, swallowerrors=swallowerrors, 
                                       subtype=subtype, charset=charset,
                                       mcc=mcc, mbcc=mbcc)
        
        if messages_to.has_key(hashed):
            messages_to[hashed].append(genid)
        else:
            messages_to[hashed] = [genid]
            
        # putting a message on queue always succeeds
        return True
    
    def _hashMessageData(self, to, **kw):
        """ create a simplied string that represents all the values in *a. """
        ss = lambda s: s.strip().lower()
        s = [ss(to)]
        for k, v in kw.items():
            if v is None:
                v = 0
            try:
                v = str(int(v))
            except ValueError:
                v = ss(str(v))
            s.append('%s=%s'% (ss(k), v))
        return ':'.join(s)
    
    def _sendEmail(self, msg, to, fr, subject,
                  mcc=None, mbcc=None, subtype='plain', charset='us-ascii',              
                  swallowerrors=False, debug=None,
                  construct_body=False # for legacy reasons
                  ):
        """ actually send the email item right now """
        return HomepageBase.sendEmail(self, msg, to, fr, subject, mcc=mcc, 
                                    mbcc=mbcc, subtype=subtype, charset=charset,
                                    swallowerrors=swallowerrors, debug=debug,
                                    construct_body=construct_body)

    security.declarePublic('sendAll')
    def sendAll(self, onerror_stop=False):
        """ merge messages if need be in self.messages_to and finally send them """
        onerror_stop = FriedUtils.niceboolean(onerror_stop)
        
        out = []
        del_messageids = []
        for messageids in self.messages_to.values():
            if len(messageids) == 1:
                # easy, it's just a simple delayed message, no need to 
                # merge and send as digest
                o = getattr(self, messageids[0])
                try:
                    self._sendEmail(o.msg, o.to, o.fr, o.subject,
                                o.mcc, o.mbcc, o.subtype, o.charset,
                                o.swallowerrors, o.debug, o.construct_body)
                    out.append(o.to+'\n'+o.subject)
                except Exception, msg:
                    if onerror_stop:
                        raise Exception, msg
                    
                    
                del_messageids.append(messageids[0])
                
            else:
                # time to merge things!
                objects = [getattr(self, x) for x in messageids if hasattr(self, x)]
                del_messageids.extend([x.getId() for x in objects])
                
                # since self.messages_to was created with a hashing function that
                # makes sure the To: header is always unique we can take the 
                # To: header from any of the objects. 
                to = objects[0].to
                # the same goes for debug, swallowerrors, subtype, charset, mcc and mbcc
                debug = objects[0].debug
                swallowerrors = objects[0].swallowerrors
                subtype = objects[0].subtype
                charset = objects[0].charset
                mcc = objects[0].mcc
                mbcc = objects[0].mbcc
                construct_body = objects[0].construct_body
                
                subjects = [x.subject for x in objects]
                msgs = [x.msg for x in objects]
                froms = [x.fr for x in objects]
                froms_set = Set(froms)
                
                if len(froms_set) == 1: # all from addresses where the same
                    fr = froms[0]
                else:
                    fr = self.default_from_address
                    
                subject = "Digested %s messages" % len(subjects)
                msg = "The following email subjects were merged into one digested email:\n\n"
                for i in range(len(subjects)):
                    msg += "\t#%s: %s\n\n" % (i+1, subjects[i])
                    msg += msgs[i].rstrip() + '\n'
                    msg += '\n' + '_'*78 + '\n'
                
                # we've now made many messages into 1. Send it
                try:
                    self._sendEmail(msg, to, fr, subject,
                                mcc, mbcc, subtype, charset,
                                swallowerrors, debug, construct_body)
                    out.append(to+'\n'+subject)
                except Exception, msg:
                    if onerror_stop:
                        raise Exception, msg

        msg_out = '\n'.join(out)
        
        self._updateMessagesTo(del_messageids)
        
        self.manage_delObjects(del_messageids)
        
        self._last_log = msg_out
        self._last_sendall = DateTime()

        if msg_out:
            return msg_out
        else:
            return "nothing"
                

    
templates = (('dtml/Documentation', 'manage_Documentation'),
            )
addTemplates2Class(MessageQueue, templates)

                
InitializeClass(MessageQueue)
        
        
        
#-----------------------------------------------------------------------------

class Message(SimpleItemBase):
    """ a stored copy of an outbound email """
    
    meta_type = METATYPE_MESSAGE
    
    security = ClassSecurityInfo()
    
    icon = 'misc_/FriedMessageQueue/message_icon.gif'
    
    def __init__(self, id, msg, to, fr, subject,
                  mcc=None, mbcc=None, subtype='plain', charset='us-ascii',              
                  swallowerrors=False, debug=None,
                  construct_body=False # for legacy reasons
                  ):
        self.id = id
        self.title = to
        self.msg = msg
        self.to = to # very important
        self.fr = fr
        self.subject = subject
        self.mcc = mcc
        self.mbcc = mbcc
        self.subtype = subtype
        self.charset = charset
        self.swallowerrors = swallowerrors 
        self.debug = debug
        self.construct_body = construct_body
        
    def getId(self):
        """ return id """
        return self.id 
        
     
InitializeClass(Message)    