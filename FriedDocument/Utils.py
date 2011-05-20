import re


from htmlentitydefs import entitydefs

entitydefs_inverted = {}
for k,v in entitydefs.items():
    entitydefs_inverted[v] = k
    
# zope
try:
    from DocumentTemplate import sequence
    from Products.PythonScripts.standard import html_quote, newline_to_br, \
         structured_text, url_quote, url_quote_plus
except ImportError:
    pass # running from commandline, not Zope


from addhrefs import addhrefs


def AddParams2URL(url, params={}):
    """ return url and append params but be aware of existing params """
    p='?'
    if p in url:
        p = '&'
    url = url + p
    for key, value in params.items():
        url = url + '%s=%s&'%(key, url_quote(value))
    return url[:-1]


_badchars_regex = re.compile('|'.join(entitydefs.values()))
_been_fixed_regex = re.compile('&\w+;|&#[0-9]+;')
def html_entity_fixer(text, skipchars=[], extra_careful=1):

    # if extra_careful we don't attempt to do anything to
    # the string if it might have been converted already.
    if extra_careful and _been_fixed_regex.findall(text):
        return text

    if same_type(skipchars, 's'):
        skipchars = [skipchars]

    
    keyholder= {}
    for x in _badchars_regex.findall(text):
        if x not in skipchars:
            keyholder[x] = 1
    text = text.replace('&','&amp;')
    text = text.replace('\x80', '&#8364;')
    for each in keyholder.keys():
        if each == '&':
            continue

        better = entitydefs_inverted[each]
        if not better.startswith('&#'):
            better = '&%s;'%entitydefs_inverted[each]
        
        text = text.replace(each, better)
    return text
    

def uniqify(all):
    """ Convert ['a','b','a'] to ['a','b'] """
    u = []
    for each in all:
        if each not in u:
            u.append(each)
    return u


def moveUpListelement(element, xlist):
    """ move an element in a _mutable_ list up one position
    if possible. If the element is a list, then the function
    is self recursivly called for each subelement.
    """
    
    assert type(xlist)==type([]), "List to change not of list type "\
				  "(%r)"%type(xlist)
	
    if type(element)==type([]):
        for subelement in element:
            moveUpListelement(subelement, xlist)
	    
    if element==xlist[0]:
        pass
    elif element in xlist:
        i=xlist.index(element)
        xlist[i], xlist[i-1] = xlist[i-1], xlist[i]

def ShowFilesize(bytes):
    """ Return nice representation of size """
    if bytes < 1024:
        return "1 Kb"
    elif bytes > 1048576:
        mb_bytes = '%0.02f'%(bytes / 1048576.0)
        return "%s Mb"%mb_bytes
    else:
        return "%s Kb"%int(bytes / 1024)
    


def ShowDescription(text, display_format=''):
    """
    Display text, using harmless HTML
    """

    if display_format == 'structuredtext':
        #st=_replace_special_chars(text)
        st=text

        for k,v in {'<':'&lt;', '>':'&gt;',
                    '[':'|[|'}.items():
            st = st.replace(k,v)

        st = html_entity_fixer(st, skipchars=('"',))

        st = structured_text(st)
        

        for k,v in {'&amp;lt;':'&lt;', '&amp;gt;':'&gt;',
                    '|[|':'['}.items():
            st = st.replace(k,v)

        # BUG in structured_text in Zope 2.4.0
        # it appends these annoying tags.
        #for tag in ['<html>','<body>','</body>','</html>']:
        #    st = st.replace(tag, '')
        
        st = addhrefs(st)
        return st
    elif display_format == 'html':
        return text
    else:
        t = '<p>%s</p>'%html_quote(text)
        t = t.replace('&amp;lt;','&lt;').replace('&amp;gt;','&gt;')
        t = addhrefs(t)
        t = newline_to_br(t)
        return t

    
def same_type(one, two):
    """ use this because 'type' as variable can be used elsewhere """
    return type(one)==type(two)

    