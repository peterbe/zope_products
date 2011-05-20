##
## FriedCMS
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
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
                                

PROJECT_NAME = 'FriedCMS'
    
DEBUG = DEBUGMODE = getEnvBool('DEBUG_%s' % PROJECT_NAME, False)
OPTIMIZE = getEnvBool('OPTIMIZE_%s' % PROJECT_NAME, False)

SQLCALLS_LOGFILENAME = None
SQLPROFILING_LOGFILENAME = None
DEBUG_SQLCALLS = False
DB_CONNECTION_ID = getEnvStr('DB_CONNECTION_ID_%s' % PROJECT_NAME, 
                             'Psycopg_database_connection')
ID_ZCATALOG = 'HCatalog'

# Security related
VMS = "View management screens"
PERMISSION_MANAGE_CONTENT = "Manage Fried Content"
MANAGE_CONTENT_PERMISSIONS = PERMISSION_MANAGE_CONTENT # old name
PERMISSION_VIEW = 'View'
AUTHENTICATED_ROLE = 'Authenticated'

# Meta types...
METATYPE_HOMEPAGE = "%s Homepage" % PROJECT_NAME
METATYPE_NEWSCONTAINER = "%s NewsContainer" % PROJECT_NAME
METATYPE_NEWSITEM = "%s NewsItem" % PROJECT_NAME
METATYPE_FILESCONTAINER = "%s FilesContainer" % PROJECT_NAME
METATYPE_FILE = "%s File" % PROJECT_NAME
METATYPE_BLOGCONTAINER = "%s BlogContainer" % PROJECT_NAME
METATYPE_BLOGITEM = "%s BlogItem" % PROJECT_NAME
METATYPE_MODULE = "%s Module" % PROJECT_NAME
METATYPE_USER = "%s User" % PROJECT_NAME
METATYPE_USERFOLDER = "%s User Folder" % PROJECT_NAME
METATYPE_PAGE = "%s Page" % PROJECT_NAME
METATYPE_PAGECONTAINER = "%s PageContainer" % PROJECT_NAME
METATYPE_FAQCONTAINER= "%s FAQContainer" % PROJECT_NAME
METATYPE_FAQ = "%s FAQ" % PROJECT_NAME

PROCESS_ERROR_MESSAGES = getEnvBool('PROCESS_ERROR_MESSAGES_%s' % PROJECT_NAME, 1)

DEFAULT_WEBMASTER_EMAIL = ''
DEFAULT_WEBMASTER_NAME = ''
DEFAULT_DEVELOPER_EMAIL = 'peter@fry-it.com'
DEFAULT_DEVELOPER_NAME = 'Peter Bengtsson'


# Taken from IssueTrackerProduct
ICON_ASSOCIATIONS={'bat':'bat.gif',  'chm':'chm.gif',  'dll':'dll.gif',
                   'doc':'doc.gif',  'exe':'exe.gif',  'gz':'gz.gif',
                   'tgz':'gz.gif',   'mpeg':'mpg.gif', 'mpg':'mpg.gif',
                   'pdf':'pdf.gif',  'ppt':'ppt.gif',  'py':'py.gif',
                   'pyw':'py.gif',   'pyc':'py.gif',   'reg':'reg.gif',
                   'tar':'tar.gif',  'txt':'txt.gif',  'nfo':'txt.gif',
                   'xls':'xls.gif',  'xml':'xml.gif',  'zip':'zip.gif',
                   'wav':'mpg.gif',  'mp3':'music.gif','ini':'ini.gif',
                   'gif':'gif.gif',  'jpg':'gif.gif',  'jpeg':'gif.gif',
                   'png':'gif.gif',  'avi':'mpg.gif',  'js':'js.gif',
                   'pyo':'py.gif',   'html':'html.gif','htm':'html.gif',
                   'psd':'psd.gif',  'fla':'fla.gif',  'swf':'swf.gif',
                   'zexp':'zope.gif','tif':'gif.gif',  'csv':'xls.gif',
                   'pps':'pps.gif',  'm3u':'mp3.gif',  'shtml':'html.gif',
                   'rtf':'doc.gif',  'mov':'mov.gif',  'bmp':'gif.gif',
                   'java':'java.png','jar':'java.png', 'jsp':'java.png',
                   'log':'txt.gif',  'dtml':'dtml.gif','bz2':'gz.gif',
                   'sxc':'sxc.gif',  'ra':'ra.gif',    'sxd':'sxd.gif',
                   'zpt':'zpt.gif',  'pt':'zpt.gif',   'djvu':'djvu.gif',
                   'djv':'djvu.gif', 'ogg':'music.gif','wma':'music.gif',
                   }
