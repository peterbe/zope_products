def _(s):
    return s

#from Products.PlacelessTranslationService.MessageID import MessageIDFactory
from zope.publisher.browser import BrowserLanguages
from zope.i18nmessageid import MessageIDFactory
_ = MessageIDFactory('ryf')

                                                        

class BrowserFormLanguages(BrowserLanguages):

    def getPreferredLanguages(self):
        langs = super(BrowserFormLanguages, self).getPreferredLanguages()
        form_lang = self.request.get("ZopeLanguage", None)
        if form_lang is not None:
            langs.insert(0, form_lang)
        return langs
