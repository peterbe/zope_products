##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
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
                                
    
    
DEBUG = getEnvBool('DEBUG_RememberYourFriends', False)

# Meta types...
METATYPE_HOMEPAGE = "RememberYourFriends Homepage"

DB_CONNECTION_ID = getEnvStr('DB_CONNECTION_ID_RememberYourFriends',
                             'Psycopg_database_connection')

EMAIL_SIGNATURE = """
RememberYourFriends.com
A clever way of making sure you remember your old friends
""".strip()

UNICODE_ENCODING = 'latin1'


SESSIONKEY_LOGIN_UID = 'login_uid_ryf'
COOKIEKEY_AUTOLOGIN_UID = '__aluidryf'
AUTOLOGIN_EXPIRES_DAYS = 30

DEBUG_SQLCALLS = getEnvBool('DEBUG_SQLCALLS_RememberYourFriends', False)
PROFILE_SQLCALLS = getEnvBool('PROFILE_SQLCALLS_RememberYourFriends', False)

WEBMASTER_EMAIL = 'webmaster@rememberyourfriends.com'
WEBMASTER_NAME = 'RememberYourFriends.com'
DEVELOPER_EMAIL = 'peter@fry-it.com' 
DEVELOPER_NAME = 'Peter Bengtsson'

DEFAULT_HTML_EMAILS = True

OPTIMIZE = getEnvBool('OPTIMIZE_RememberYourFriends', True)

VMS = "View management screens"