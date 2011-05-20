# -*- coding: iso-8859-1 -*
##
## unittest Document
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

import os, sys
from sets import Set
from pprint import pprint
from time import sleep
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Globals import SOFTWARE_HOME    
from Testing import ZopeTestCase
from Testing import makerequest
from Testing.ZopeTestCase.ZopeTestCase import user_name as test_user_name
from Testing.ZopeTestCase.ZopeTestCase import user_role as test_user_role

ZopeTestCase.installProduct('PageTemplates')
ZopeTestCase.installProduct('FriedZopeBase')
ZopeTestCase.installProduct('FriedDocument')
ZopeTestCase.installProduct('ZTinyMCE')

from Products.ZTinyMCE.default_configurations import default_configurations

#------------------------------------------------------------------------------
#
# Some constants
#
from Products.FriedDocument.Document import SubmitError
from Products.FriedDocument.Constants import MANAGE_DOCUMENT
#------------------------------------------------------------------------------

_home = os.path.dirname(__file__)

class TestDocumentCase(ZopeTestCase.ZopeTestCase):
    
    def afterSetUp(self):
        dispatcher = self.folder.manage_addProduct['PageTemplates']
        dispatcher.manage_addPageTemplate('HeaderFooter')
        pt = dispatcher.HeaderFooter
        pt.write(open(os.path.join(_home, 'example_header_footer.pt')).read())
        
        self.doc = self._createDocument('index_html', 'Title', 
                                   metalmacro='HeaderFooter',
                                   show_in_nav=1)
                                                                      
        # create a ZTinyMCE root
        dispatcher = self.folder.manage_addProduct['ZTinyMCE']
        dispatcher.manage_addZTinyMCE('TinyMCE')
        tinymce = dispatcher.TinyMCE
        
    def tearDown(self):
        pass
    
    def test_createDocument(self):
        """ test if its possible to create a document """
        # well, document is already created in afterSetUp()
        doc = self.folder.index_html
        assert doc.meta_type == 'Fried Document'
        # check that it was cooked
        assert hasattr(doc, 'index_html_template')

    def Xtest_createDocument_with_show_in_nav(self):
        """ test that it's possible to set the show_in_nav from start """
        # experiment with 'show_in_nav'
        show_in_nav = False
        doc = self._createDocument('test1','', metalmacro='HeaderFooter',
                                   show_in_nav=show_in_nav)
        assert doc.showInNav() == show_in_nav, \
         "Not possible to set show_in_nav to %s" % show_in_nav
        # Reverse the test
        show_in_nav = True
        doc = self._createDocument('test2','', metalmacro='HeaderFooter',
                                   show_in_nav=show_in_nav)
        assert doc.showInNav() == show_in_nav, \
         "Not possible to set show_in_nav to %s" % show_in_nav         
                   
        
    def Xtest_changeDocumentTitle(self):
        """ test that it's possible to change title """
        doc = self.folder.index_html
        
        # check the title
        assert doc.getTitle() == u'Title'
        assert isinstance(doc.getTitle(), unicode)
        doc.manage_changeDocumentTitle('Title2')
        assert doc.getTitle() == u'Title2'
        assert isinstance(doc.getTitle(), unicode)
        
    def Xtest_changeDocumentShowInNav(self):
        """ test that it's possible to change show_in_nav """
        doc = self.folder.index_html
        
        # Toogle the 'show_in_nav'
        before = doc.showInNav()
        doc.manage_changeDocumentTitle(doc.getTitle(),
                            use_show_in_nav=True,
                            show_in_nav=not before)
        assert (not doc.showInNav()) == before, "Not possible to change show_in_nav"

    def Xtest_strip_doctypehtml(self):
        """ test _strip_doctypehtml() which is part of PUT() """
        inp = '''Something
        <body>
        Result
        </body>
        Else
        '''
        doc = self.folder.index_html
        res = doc._strip_doctypehtml(inp)
        assert res.strip() == 'Result'
        
        # a failing piece of HTML
        inp = '''Something
        <body>
        Result
        Else
        '''
        doc = self.folder.index_html
        res = doc._strip_doctypehtml(inp)
        assert res.strip().split() == ['Result','Else'], res.strip().split()
        
        # With a more complicated piece of HTML
        inp = '''Something
        <BODY 
           onLoad="foo()"
           >
        Result
        </Body>
        Else
        '''
        doc = self.folder.index_html
        res = doc._strip_doctypehtml(inp)
        assert res.strip() == 'Result'
        
    def Xtest_getTitle(self):
        """ test getTitle and getTitle_ascii """
        doc = self.folder.index_html
        new_title = u'ÅngestmålRättviklördagen'
        doc.manage_changeDocumentTitle(new_title)
        assert doc.getTitle() == new_title
        assert doc.getTitle_ascii() == 'AngestmalRattviklordagen', doc.getTitle_ascii()
        
    def Xtest_embedDisplayInURL(self):
        """ test embedDisplayInURL() """
        doc = self.folder.index_html
        
        url, display_size = '/something/else/foo.jpg', 'small'
        expect = '/something/else/display-small/foo.jpg'
        assert doc.embedDisplayInURL(url, display_size) == expect,\
        doc.embedDisplayInURL(url, display_size)
        
        url, display_size = '/something/else/display-crap/foo.jpg', 'small'
        expect = '/something/else/display-small/foo.jpg'
        assert doc.embedDisplayInURL(url, display_size) == expect,\
        doc.embedDisplayInURL(url, display_size)
        
        url, display_size = 'foo.jpg', 'small'
        expect = 'display-small/foo.jpg'
        assert doc.embedDisplayInURL(url, display_size) == expect,\
        doc.embedDisplayInURL(url, display_size)        
        
        url, display_size = '/page/foo.jpg', None
        expect = url
        assert doc.embedDisplayInURL(url, display_size) == expect,\
        doc.embedDisplayInURL(url, display_size)                
        
        
    def Xtest_cached_expiryoption(self):
        """ test if it's possible to set the Expiry time and what happens if you 
        do that. """
        doc = self.folder.index_html
        
        doc.manage_setExpiryOptions(2)
        assert doc.getExpiryHours() == 2, doc.getExpiryHours()
        
        doc.manage_setExpiryOptions(2.2)
        assert doc.getExpiryHours() == 2.2, doc.getExpiryHours()
        
        self.assertRaises(SubmitError, doc.manage_setExpiryOptions, 99999999)
        
        doc.manage_setExpiryOptions(-123)
        assert doc.getExpiryHours() == 0, doc.getExpiryHours()
        
        doc.manage_setExpiryOptions(False)
        assert doc.getExpiryHours() == 0, doc.getExpiryHours()        

        doc.manage_setExpiryOptions(True)
        assert doc.getExpiryHours() == 1, doc.getExpiryHours()
        
        doc.manage_setExpiryOptions(None)
        assert doc.getExpiryHours() == 0, doc.getExpiryHours()
        
        doc.manage_setExpiryOptions("2.5")
        assert doc.getExpiryHours() == 2.5, doc.getExpiryHours()
        
        self.assertRaises(ValueError, doc.manage_setExpiryOptions, "!")
        
        # setting it should create a template called 'index_html_cached'
        # after you view it
        doc.manage_setExpiryOptions(1)
        assert not hasattr(doc, 'index_html_cached')
        doc.view(self.app.REQUEST)
        assert hasattr(doc, 'index_html_cached')
        # open the page template and look at the source code
        pt = doc.index_html_cached
        src = pt.document_src()
        assert src.find('doCache(1.0)') > -1
        
        # setting it to 0 and cooking should remove the 'index_html_cached'
        # template
        doc.manage_setExpiryOptions(False)
        doc._cook()
        assert not hasattr(doc, 'index_html_cached')
        
    def Xtest_writingToDocument(self):
        """ test if we can write content into specific slots
        and then render it and expect certain content.
        These tests are based on 'tests/example_header_footer.pt'
        """
        
        doc = self._createDocument('dummy', 'title', 'HeaderFooter')
        
        # before we make another change, do a little sleeping
        # so that the revision timestamp values don't get too
        # close to each other
        sleep(0.1)
        
        doc.manage_saveSlot('body','hello<br>doctor')
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('hello<br />doctor') > -1, viewed

        # make a change and then expect two revisions
        doc.manage_saveSlot('body','hello 2nd doctor')
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('hello<br />doctor') == -1, viewed
        assert viewed.find('hello 2nd doctor') > -1, viewed
        assert doc.hasRevisions('body')
        assert doc.countRevisionTimestamps('body') == 3, \
        doc.countRevisionTimestamps('body')
        
        timestamps = doc.getRevisionTimestamps('body')
        assert len(timestamps) == 3, len(timestamps)
        
        # all of these should be dicts with keys:
        #  'date' and 'timestamp'
        for timestamp in timestamps:
            assert isinstance(timestamp, dict), type(timestamp)
            assert timestamp.has_key('timestamp'), timestamp.keys()
            assert timestamp.has_key('date'), timestamp.keys()
        
        # desired timestamp is the middle one
        desired_timestamp = timestamps[1]['timestamp']
        doc.manage_reinstateRevision('body', desired_timestamp)
        # now the content should be back to 'hello<br />doctor'
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('hello<br />doctor') > -1, viewed
        
        
    def Xtest_versioning(self):
        """ test versioning.
        Enter versioning, make some changes and check what happens when 
        you view the page as anonymous or with the right permission.
        """
        doc = self._createDocument('dummy','title','HeaderFooter')
        doc.manage_saveSlot('body','Old content')
        # start versioning
        doc.manage_startVersioning()
        # manage_startVersioning() does two things, it sets
        # in_versioning to True and calls _initVersioningTexts()
        assert doc.in_versioning
        # After _initVersioningTexts(), the versioning bank should
        # now contain an almost identical copy of the last slot of
        # _texts.
        
        # every copied slot should only have 1 revision
        for slot, revisions in doc._getTexts().items():
            assert len(revisions) == 1, len(revisions)
            
        # make a change now that we're in versioning
        doc.manage_saveSlot('body','Much better')
        
        # this shouldn't update 'index_html_template'
        old_pt_src = doc.index_html_template.document_src()
        assert old_pt_src.find('Much better') == -1
        assert old_pt_src.find('Old content') > -1
        
        # but it should update 'index_html_versioning'
        new_pt_src = doc.index_html_versioning.document_src()
        assert new_pt_src.find('Much better') > -1
        assert new_pt_src.find('Old content') == -1
        
        # Anonymous users should see the old copy
        self.logout()
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('Old content') > -1
        assert viewed.find('Much better') == -1        
        
        # Return to being logged in as manager
        self.login(name=test_user_name)
        self.setPermissions(MANAGE_DOCUMENT, role=test_user_role)
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('Much better') > -1        
        assert viewed.find('Old content') == -1
        
        
    def test_versioningAndPublish_andStop(self):
        """ test versioning.
        (
        versioning on aka. 'auto-publish stopped'
        versioning off aka. 'auto-publish'
        )
        Enter versioning, make some changes and then publish
        """
        doc = self._createDocument('dummy','title','HeaderFooter')
        doc.manage_saveSlot('body','Old content')
        # start versioning
        doc.manage_startVersioning()
        # manage_startVersioning() does two things, it sets
        # in_versioning to True and calls _initVersioningTexts()
        assert doc.inVersioning()
        
        # make a change whilst in versioning
        doc.manage_saveSlot('body', 'New content')
        
        # test_versioning() already checks if the seperation is made
        # Now, when we publish these changes we should expect that be able
        # to view New content even if viewing the page anonymously.
        doc.manage_publishVersioning(versioning_off=True)
        
        # there shouldn't be a index_html_versioning template
        assert not hasattr(doc, 'index_html_versioning')
        
        # count the number of revisions which should now have gone up one
        assert doc.countRevisionTimestamps('body') == 3, \
        doc.countRevisionTimestamps('body')
        
        # viewing it as anonymous should return a page with the 'New content'
        self.logout()
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('New content') > -1
        assert viewed.find('Old content') == -1        
        
        
    def Xtest_versioningAndPublish_andContinue(self):
        """ test versioning.
        (
        versioning on aka. 'auto-publish stopped'
        versioning off aka. 'auto-publish'
        )
        Enter versioning, make some changes and then publish but continue to 
        be in versioning. 
        """
        doc = self._createDocument('dummy','title','HeaderFooter')
        doc.manage_saveSlot('body','Old content')
        # start versioning
        doc.manage_startVersioning()
        # manage_startVersioning() does two things, it sets
        # in_versioning to True and calls _initVersioningTexts()
        assert doc.inVersioning()
        
        # make a change whilst in versioning
        doc.manage_saveSlot('body', 'New content')
        
        # test_versioning() already checks if the seperation is made
        # Now, when we publish these changes we should expect that be able
        # to view New content even if viewing the page anonymously.
        doc.manage_publishVersioning()
        
        # there shouldn't be a index_html_versioning template
        assert hasattr(doc, 'index_html_versioning')
        
        # count the number of revisions which should now have gone up one
        # (nb: this is of the versioning version)
        assert doc.countRevisionTimestamps('body') == 2, \
        doc.countRevisionTimestamps('body')
        
        # viewing it as anonymous should return a page with the 'New content'
        self.logout()
        viewed = doc.view(self.app.REQUEST)
        assert viewed.find('New content') > -1
        assert viewed.find('Old content') == -1                
        

    def test_change_ztinymceconfiguration(self):
        """ add a ztinymceconfigurtion """
        doc = self._createDocument('dummy','title','HeaderFooter')
        tinymce_configs = doc.getTinyMCEConfigurations()
        assert not tinymce_configs, tinymce_configs
        
        # create a configuration
        config = self._createTinyMCEConfiguration('simple.conf')
        print doc.getTinyMCEConfiguration()
        
        
    def _createTinyMCEConfiguration(self, config_name=None, container=None):
        if container is None:
            container = self.folder
        
        configuration = ''
        for config in default_configurations:
            if not config_name:
                config_name = config['name']
                configuration = config['config']
                break
            elif config_name == config['name']:
                configuration = config['config']

        path = '/'.join(self.folder.getPhysicalPath())
        print "path", path
        print self.folder.objectValues()
        dispatcher = container.manage_addProduct['ZTinyMCE']
        dispatcher.manage_addZTinyConfiguration(config_name, 
                                                configuration=configuration,
                                                tinymce_instance_path=path,
                                                title=config_name.capitalize()
                                                )
        return getattr(dispatcher, config_name)
    
    def _createDocument(self, id, title, metalmacro, belike_path=None,
                        show_in_nav=False):
        dispatcher = self.folder.manage_addProduct['FriedDocument']
        dispatcher.manage_addFriedDocument(id, title, metalmacro=metalmacro,
                                           belike_path=belike_path,
                                           show_in_nav=show_in_nav)
        return getattr(dispatcher, id)
    
    def test_lazy_unicodify(self):
        """ test lazy_unicodify() """
        #XXX, Work harder!
    
        
    

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestDocumentCase))
    return suite

if __name__ == '__main__':
    framework()

    