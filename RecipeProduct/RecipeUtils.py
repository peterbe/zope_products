# python 
import string
import re
from random import shuffle
from math import floor

def replace_special_chars(text, simplify=1, html_encoding=0):
    """ Replace special characters with placeholder keys back and forth.
        The reason for doing this is that structured_text() doesn't support
        special characters such as едц.
    """
    reps = {'Aring':'Е',  'Auml':'Д', 'Ouml':'Ц',
            'aring':'е',  'auml':'д', 'ouml':'ц',
            'Egrave':'И', 'Eacute':'Й',
            'egrave':'и', 'eacute':'й',
            'Uuml':'Гњ',   'uuml':'Гј'}

    if simplify:
        for k, v in reps.items():
            if html_encoding:
                k='&%s;'%k
            else:
                k='__%s__'%k
            text = text.replace(v,k)
    else:
        for k, v in reps.items():
            k='__%s__'%k
            text = text.replace(k,v)
    return text
    

def _ShouldBeNone(result): return result is not None
def _ShouldNotBeNone(result): return result is None

tests = (
    # Thank you Bruce Eckels for these
  (re.compile("^[0-9a-zA-Z\.\-\_]+\@[0-9a-zA-Z\.\-]+$"), _ShouldNotBeNone, "Failed a"),
  (re.compile("^[^0-9a-zA-Z]|[^0-9a-zA-Z]$"), _ShouldBeNone, "Failed b"),
  (re.compile("([0-9a-zA-Z]{1})\@."), _ShouldNotBeNone, "Failed c"),
  (re.compile(".\@([0-9a-zA-Z]{1})"), _ShouldNotBeNone, "Failed d"),
  (re.compile(".\.\-.|.\-\..|.\.\..|.\-\-."), _ShouldBeNone, "Failed e"),
  (re.compile(".\.\_.|.\-\_.|.\_\..|.\_\-.|.\_\_."), _ShouldBeNone, "Failed f"),
  (re.compile(".\.([a-zA-Z]{2,3})$|.\.([a-zA-Z]{2,4})$"), _ShouldNotBeNone, "Failed g"),
)
def ValidEmailAddress(address, debug=None):
    for test in tests:
        if test[1](test[0].search(address)):
            if debug: return test[2]
            return 0
    return 1

def safeId(id, nospaces=0):
    """ Just make sure it contains no dodgy characters """
    id = _replace_special_chars(id)
    lowercase = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'
    specials = '_-.'
    allowed = lowercase + lowercase.upper() + digits + specials
    if not nospaces:
        allowed = ' ' + allowed
    n_id=[]
    allowed_list = list(allowed)
    for letter in list(id):
        if letter in allowed_list:
            n_id.append(letter)
    return ''.join(n_id)

def _replace_special_chars(id):
    """ be kind to make some replacements """
    d={'Д':'A', 'Е':'A', 'Ц':'O', 'е':'a', 'д':'a', 'ц':'o',
       'й':'e', 'и':'e', 'а':'a'}
    for bad, good in d.items():
        id = id.replace(bad, good)
    return id

def list_makesure(item):
    """ make sure item is list """
    if type(item) != type([]):
        return [item]
    else:
        return item

    
def getRandomString(length=10, loweronly=1, numbersonly=0):
    """ return a very random string """
    if numbersonly:
        l = list('0123456789')
    else:
        lowercase = 'abcdefghijklmnopqrstuvwxyz'+'0123456789'
        l = list(lowercase + lowercase.upper())
    shuffle(l)
    s = string.join(l,'')
    if len(s) < length:
        s = s + getRandomString(loweronly=1)
    s = s[:length]
    if loweronly:
        return s.lower()
    else:
        return s

    
def encodeEmailString(email, title=None):
    """ if encode_emaildisplay then use JavaScript to encode it """
    if title is None:
        title = email

    js_string = """document.write('<a href="mailto:%s">"""%email
    js_string += """%s</a>')"""%title
    hexed = _hex_string(js_string)
    js_script = """<script language="JavaScript">eval(unescape('"""
    js_script += hexed + """'))</script>"""
    return js_script

    
        
def _hex_string(oldstring):
    """ hexify a string """
    # Taken from http://www.happysnax.com.au/testemail.php
    # See Credits
    
    def _tohex(n):
        hs='0123456789ABCDEF'
        return hs[int(floor(n/16))]+hs[n%16]
    
    newstring=''
    length=len(oldstring)
    for i in range(length):
        newstring=newstring+'%'+_tohex(ord(oldstring[i]))
    return newstring