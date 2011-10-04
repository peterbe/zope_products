##############################################################################
#
# Photo for Zope
#
# Copyright (c) 2001 Logic Etc, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   Ron Bickers      rbickers@logicetc.com
#   Logic Etc, Inc.  http://www.logicetc.com/
#
##############################################################################

"""PhotoImage

This is used as a wrapper for Photo to provide a common interface
for both Zope Image objects and ExtImage objects.

"""

from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.Image import Image
import time

class PhotoImage(Image):
    """Interface to Zope Image."""

    security=ClassSecurityInfo()

    def __init__(self, id, title='', file='', content_type='', precondition='', path=''):
        PhotoImage.inheritedAttribute('__init__')(self, id, title, file, content_type, precondition)

    def _height(self):
        return self.height

    def _width(self):
        return self.width

    def _content_type(self):
        return self.content_type

    def _size(self):
        return self.size

    def _age(self):
        mtime = self.bobobase_modification_time().timeTime() / 60
        now = time.time() / 60
        return int(now - mtime)

    security.declareProtected('View', 'index_html')
    def index_html(self, REQUEST, RESPONSE):
        return PhotoImage.inheritedAttribute('index_html')(self, REQUEST, RESPONSE)

    def _data(self):
        return str(self.data)

    _IMdata = _data

    def _PILdata(self):
        return StringIO(str(self.data))

    def _newImage(self, id, file, path):
        return PhotoImage(id, '', file, self._content_type())

    def _isValid(self):
        return self.width and self.height and self.data and self.content_type

    security.declareProtected('Change Photo', 'manage_upload')
    def manage_upload(self, file, content_type):
        return PhotoImage.inheritedAttribute('manage_upload')(self, file)

InitializeClass(PhotoImage)
