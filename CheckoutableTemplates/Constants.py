# Suppose you have done:
# $ ln -s zope261b1 Zope-2.6.2b2-linux2-x86
# or some similar setup, then CLIENT_HOME becomes the latter but
# globals() will have the former.
# This hack makes sure that CT_HOME becomes like
# globals()
#
# To set this variable, edit you ./start script to have the following:
#
# CT_HOME=/home/zope/zope123/var
# export CT_HOME
#
# The same goes for the CT_SOFTWARE_HOME and you set it like this:
#
# CT_SOFTWARE_HOME=/home/zope/zope123/lib/python/Products
# export CT_SOFTWARE_HOME
#


import os

CT_HOME = os.environ.get('CT_HOME', CLIENT_HOME)
CT_SOFTWARE_HOME = os.environ.get('CT_SOFTWARE_HOME', SOFTWARE_HOME)
CT_INSTANCE_HOME = os.environ.get('CT_INSTANCE_HOME', INSTANCE_HOME)

def _getVariable(key, default):
    value = os.environ.get(key, default)
    try:
        value = not not int(value)
    except:
        if str(value).lower().strip() in ['yes','on']:
            value = 1
        elif str(value).lower().strip() in ['no','off']:
            value = 0
        else:
            value = default
    return value

DISABLE_CHECKOUTABLETEMPLATES = _getVariable('DISABLE_CHECKOUTABLETEMPLATES', 0)

# Allows to write back to file from showCheckoutableTemplate
CAN_WRITEBACK = _getVariable('CT_CAN_WRITEBACK', 0)

# Writes to Log() every time we store a template
DEBUG = _getVariable('CT_DEBUG',0)

# Attempts to optimize the output
OPTIMIZE = _getVariable('CT_OPTIMIZE',1)
    

CONFIGFILEPATH = os.path.join(CT_HOME, "CTConfig")
CONFIGFILEPATH = CONFIGFILEPATH + '.dump'


# It's good to have CLEAN_CHECK on if you have upgraded from
# an old CheckoutableTemplates and you might have old information
# in your pickled file in 'var/CTConfig.dump'
# If you switch CLEAN_CHECK off you might gain some speed but
# this should only be done once you know you've at least once
# deleted the CTConfig.dump file sometime before Zope started.
CLEAN_CHECK = _getVariable('CT_CLEAN_CHECK', 1)