import unittest
import sys, os
sys.path.insert(0, os.path.abspath('../'))

import Utils


GOOD_1 = '''
mode : "textareas",
theme : "simple"
'''

BAD_1 = '''
mode : "textareas",
theme : simple"
'''

BAD_2 = '''
mode : "textareas",
theme : simple",
'''

class ValidConfigurationTestCase(unittest.TestCase):
    
    def testBasicSimpleValid(self):
        config = GOOD_1
        self.assertTrue(Utils.ValidConfiguration(config), True)
        
    def testBasicSimpleInvalid(self):
        config = BAD_1
        self.assertTrue(not Utils.ValidConfiguration(config), True)
     
    def testInvalidCommaEnding(self):
        config = BAD_2
        self.assertTrue(not Utils.ValidConfiguration(config), True)
        
    def testValidationError(self):
        config = BAD_1
        self.assertRaises(Utils.ConfigurationError, Utils.ValidConfiguration, config, 
                          be_angry=True)

if __name__ == '__main__':
    unittest.main()        
    #print help(unittest.TestCase)
    