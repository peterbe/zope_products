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

"""Photo and Photo Folder"""

__version__ = '1.2.3'

from Photo import Photo, manage_addPhotoForm, manage_addPhoto
from PhotoFolder import PhotoFolder, manage_addPhotoFolderForm, manage_addPhotoFolder

def initialize(registrar):
    registrar.registerClass(
        Photo,
        constructors = (manage_addPhotoForm, manage_addPhoto),
        icon = 'www/photo.gif'
    )
    registrar.registerClass(
        PhotoFolder,
        constructors = (manage_addPhotoFolderForm, manage_addPhotoFolder),
        icon = 'www/photofolder.gif'
    )
