##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys, random
from Globals import InitializeClass, package_home, DTMLFile
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo, getSecurityManager
from DateTime import DateTime
from slimmer import xhtml_slimmer

from Products.FriedZopeBase.TemplateAdder import addTemplates2Class as addTemplates2ClassRemote

from I18N import _

def addTemplates2Class(Class, templates, optimize=None):
    """ we do this so that we easy can send our own globals() """
    addTemplates2ClassRemote(Class, templates, optimize, globals_=globals())

#-----------------------------------------------------------------------------

class BirthdayWidgetBase:
    
    def showMonthName(self, m):
        return {
        1: _(u"January"),
        2: _(u"February"),
        3: _(u"March"),
        4: _(u"April"),
        5: _(u"May"),
        6: _(u"June"),
        7: _(u"July"),
        8: _(u"August"),
        9: _(u"September"),
        10: _(u"October"),
        11: _(u"November"),
        12: _(u"December")
        }[m]
        
    def getYourNameInput(self):
        default = str(_(u"Your name"))
        tmpl = '<input name="name" size="17" style="color:#ccc" value="%s" '\
               'onfocus="if(this.value==%r){this.value=\'\';this.style.color=\'black\'}" '\
               'onblur="if(this.value==\'\'){this.value=%r;this.style.color=\'#ccc\'}" />'
        return tmpl % (default, default, default)
               
        
    def decryptID(self, id):
        return int(id) / 739
    
    def encryptID(self, id):
        return int(id) * 739

    def sbw(self, id, REQUEST):
        """ same thing different name """
        return self.showBirthdayWidget(id, REQUEST)
    
    def showBirthdayWidget(self, id, REQUEST):
        """ return the javascript to ask people for a birthday """
        uid = self.decryptID(id)
        user = self.getUser(uid)
        
        #REQUEST.RESPONSE.setHeader('Content-Type','text/plain')
        REQUEST.RESPONSE.setHeader('Content-Type','text/javascript')
        
        html = self.birthdayform(self, REQUEST, user=user, id=id).strip()
        html = html.replace("'","\\'")
        #html = xhtml_slimmer(html)
        js = []
        for line in html.splitlines():
            js.append("document.write('%s');" % line)
        
        return '\n'.join(js)
        
    def getYourBirthdayWidgetHTMLCode(self):
        """ return the HTML they should paste into their website """
        user = self.getLoggedinUser()
        id = self.encryptID(user.uid)
        src = self.absolute_url() + '/id--%s/sbw' % id
        tmpl = '<script type="text/javascript" src="%s"></script>' % src
        return tmpl
    
        

    
templates = ('zpt/birthdaywidget/birthdayform',
             'zpt/birthdaywidget/your-birthday-widget',
            )
            
addTemplates2Class(BirthdayWidgetBase, templates)
        
if __name__=='__main__':
    b = BirthdayWidgetBase()
    
    for i in range(10000):
        x = b.encryptID(i)
        print i, x, b.decryptID(x); assert b.decryptID(x)==i
