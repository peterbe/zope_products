"""Expenses ZopeTestCase
"""
from sets import Set
import cStringIO
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
    


from classes import TestBase

class TestHomepage(TestBase):
    
    def test_parseAndSplitToAddress(self):
        """ test _parseAndSplitToAddress """
        context = self.ryf
        
        name_input = 'Gwendal Paugam <gwendal.paugam@gmail.com>'
        expect_name = 'Gwendal Paugam'
        expect_email = 'gwendal.paugam@gmail.com'
        
        name, email = context._parseAndSplitToAddress(name_input)
        self.assertEquals(name, expect_name)
        self.assertEquals(email, expect_email)
        
        name_input = '"Gwendal Paugam" <gwendal.paugam@gmail.com>'
        expect_name = 'Gwendal Paugam'
        expect_email = 'gwendal.paugam@gmail.com'
        
        name, email = context._parseAndSplitToAddress(name_input)
        self.assertEquals(name, expect_name)
        self.assertEquals(email, expect_email)        
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestHomepage))
    return suite

if __name__ == '__main__':
    framework()

