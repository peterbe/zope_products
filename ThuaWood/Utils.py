##
## ThuaWood
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

import os, re, sys


def internationalizeID(s, encoding='latin-1'):
    y = unicode(s, encoding)
    replacements = (
      (u'a', (u'\xc3\xa0',u'\xc3\xa4',u'\xc3\xa2',u'\xc3\xa5')),
      (u'A', (u'\xc5',u'\xc4')),
      (u'c', (u'\xc3\xa7',)),
      (u'o', (u'\xc3\xf6',u'\xc3\xb3',u'\xc3\xb6')),
      (u'O', (u'\xc3\xd6',u'\xc3\x96')),
      (u'u', (u'\xfc',u'\xc3\xbc',u'\xc3\xba')),
      (u's', (u'\xdf',u'\xc3\x9f')),
      (u'U', (u'\xdc',)),
      (u'e', (u'\xc3\xa9',u'\xc3\xa8')),
      (u'i', (u'\xc3\xad',)),
      (u'n', (u'\xc3\xb1',)),
      
    )
    for better, bads in replacements:
        for bad in bads:
            y = y.replace(bad, better)
            
    return y.encode(encoding)
