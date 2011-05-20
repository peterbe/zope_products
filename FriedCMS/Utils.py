##
## Utils
## (c) Fry-IT, www.fry-it.com
## Peter Bengtsson <peter@fry-it.com>
##

import os, re, sys
from urlparse import urlsplit

def moveElementInList(somelist, element, direction):
    clist = somelist[:]
    d = str(direction).lower().strip()
    assert d in ('up','down'), "direction must be either 'up' or 'down'"
    assert element in clist, "Element not in list"
    if d  == 'up':
        current = clist.index(element)
        if current > 0:
            element_above = clist.pop(current-1)
            clist.insert(current, element_above)
    else:
        current = clist.index(element)
        if current < (len(clist)-1):
            clist.pop(current)
            clist.insert(current+1, element)

    return clist



valid_number_regex = re.compile('[^\d\(\)\+\ \-]')
def ValidPhoneNumber(number):
    if not number:
        return False
    elif valid_number_regex.findall(number):
        return False
    elif number.count('+') > 1:
        return False
    elif number.count('-') > 1:
        return False
    elif len(re.compile('\d').findall(number)) < 4:
        return False

    return True


def ValidURL(url):
    addressingScheme, networkLocation, urlPath, urlQuery, urlFrag = urlsplit(url)
    print urlPath, urlQuery, urlFrag
    return addressingScheme == 'http' and networkLocation