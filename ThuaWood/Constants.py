##
## ThuaWood
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

import os

def getEnvBool(key, default):
    """ return an boolean from the environment variables """
    value = os.environ.get(key, default)
    try:
        value = not not int(value)
    except ValueError:
        if str(value).lower().strip() in ['yes','on','t','y']:
            value = 1
        elif str(value).lower().strip() in ['no','off','f','n']:
            value = 0
        else:
            value = default
    return value

def getEnvInt(key, default):
    """ return an integer from the environment variables """
    value = os.environ.get(key, default)
    try:
        return int(value)
    except ValueError:
        return default
    
def getEnvStr(key, default):
    """ return an integer from the environment variables """
    value = os.environ.get(key, default)
    try:
        return str(value)
    except ValueError:
        return default
                                
    
    
DEBUG = getEnvBool('DEBUG_ThuaWood', False)

# Meta types...
METATYPE_BUST = "ThuaWood Bust"
METATYPE_BUSTFOLDER = "ThuaWood Bust Folder"

METATYPE_GUESTBOOK = "ThuaWood Guestbook"
METATYPE_GUESTBOOK_ENTRY = "ThuaWood Guestbook Entry"


VMS = 'View management screens'