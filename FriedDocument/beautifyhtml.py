#############################################################################
#
# Copyright (c) 2004-2006 Fry-IT Ltd. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from BeautifulSoup import BeautifulSoup

def beautifyhtml(htmltext, encoding):
    soup = BeautifulSoup(htmltext, fromEncoding=encoding)
    return soup.prettify(encoding=encoding).decode(encoding)
        