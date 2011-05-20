##
## ZTinyMCE
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

import os, re, sys
import inspect
import itertools
import zipfile
from cStringIO import StringIO
from Constants import DEBUG


def anyTrue(pred, seq):
    """ http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/212959 """
    return True in itertools.imap(pred,seq)


class ConfigurationError(Exception):
    pass


def debug(s, tabs=0, steps=(1,), f=False):
    if DEBUG or f:
        inspect_dbg = []
        if type(steps)==type(1):
            steps = range(1, steps+1)
        for i in steps:
            try:
                #caller_module = inspect.stack()[i][1]
                caller_method = inspect.stack()[i][3]
                caller_method_line = inspect.stack()[i][2]
            except IndexError:
                break
            inspect_dbg.append("%s:%s"%(caller_method, caller_method_line))
        out = "\t"*tabs + "%s (%s)"%(s, ", ".join(inspect_dbg))
        
        # XXX this needs attention. Consider implementing a ObserverProxy from
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/413701
        print out
        
        
_config_ok_name = re.compile('[\w_]+')
_config_ok_content = re.compile('^["\']?[^"\']+["\',]{1,2}$|true|true,|false|false,|^["\',]{2,3}$')
#_linesplit = re.compile(',\s')
def ValidConfiguration(configstring, be_angry=False):
    if not be_angry:
        try:
            ValidConfiguration(configstring, be_angry=True)
            return True
        except ConfigurationError:
            return False
        
    #parts = _linesplit.split(configstring)
    parts = configstring.splitlines()
    for part in parts:
        if not part:
            continue
        if part.strip().startswith('//'):
            continue
        if not len(part.split(':', 1)) == 2:
            raise ConfigurationError, "Line not split by ':' %r" % part
        name, content = [x.strip() for x in part.split(':', 1)]
        if name.startswith('//'):
            continue
        if not _config_ok_name.findall(name):
            raise ConfigurationError, "No name part in line %r" % part
        if not _config_ok_content.findall(content):
            print repr(content)
            raise ConfigurationError, "No content part in line %r" % part
        if not _config_ok_name.findall(name)[0] == name:
            raise ConfigurationError, "Name part appears invalid %r" % name
        if not _config_ok_content.findall(content)[0] == content:
            raise ConfigurationError, "Content part appears invalid %r" % content
        
        if name == 'mode':
            _ok_modes = ("textareas", "specific_textareas", "exact")
            if not content not in _ok_modes:
                raise ConfigurationError, "mode not %s" % ', '.join([repr(x) for x in _ok_modes])
            
        
    return True

def niceboolean(value):
    falseness = ('','no','off','false','none','0', 'f')
    return str(value).lower().strip() not in falseness


def extract( filename, dir ):
    """ Thank you very much! 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/465649
    """
    zf = zipfile.ZipFile( filename )

    # make base
    pushd = os.getcwd()
    if not os.path.isdir( dir ):
        os.mkdir( dir )
    os.chdir( dir )

    # extract files
    for fn in zf.namelist():
        fdir = os.path.dirname(fn)
        if fdir and not os.path.exists(fdir):
            os.makedirs(fdir)
        if fn.endswith('/'):
            continue
        try:
            out = open( fn, 'wb' )
            buffer = StringIO( zf.read( fn ))
            buflen = 2 ** 20
            datum = buffer.read( buflen )
            while datum:
                out.write( datum )
                datum = buffer.read( buflen )
            out.close()
        finally:
            pass #print fn
    os.chdir( pushd )
