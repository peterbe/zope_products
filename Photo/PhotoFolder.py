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

"""Photo Folder

Photo Folder objects help manage a group of Photo objects by providing
an interface for adding, removing, and modifying the properties and
display sizes of all contained photos, and by providing defaults for
newly created photos.
"""

from Globals import Persistent
from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import Item
from OFS.PropertyManager import PropertyManager
from OFS.FindSupport import FindSupport
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile
from Photo import Photo

defaultdisplays = {'thumbnail': (128,128),
                   'xsmall': (200,200),
                   'small': (320,320),
                   'medium': (480,480),
                   'large': (768,768),
                   'xlarge': (1024,1024)
                  }


class PhotoFolder(ObjectManager,
                  PropertyManager,
                  RoleManager,
                  Item,
                  FindSupport):
    """Photo Folder object implementation.

    Photo Folder objects are folders that can contain Photo objects
    and other supporting objects.  They provide properties to all
    Photos and other Photo Folders in them.  They also provide
    support methods for displaying Photos in an album-like manner.
    """

    meta_type = "Photo Folder"

    _properties = (
        {'id':'title', 'type': 'string', 'mode': 'w'},
        {'id':'image', 'type': 'selection', 'mode': 'wd', 'select_variable': 'image_select'},
        )

    manage_options = (
        {'label': 'Contents', 'action': 'manage_main'},
        {'label': 'Photo Properties', 'action': 'manage_editPhotoPropertiesForm'},
        {'label': 'Displays', 'action': 'manage_editDisplaysForm'},
        {'label': 'View', 'action': ''},
        ) + PropertyManager.manage_options \
          + RoleManager.manage_options \
          + Item.manage_options \
          + FindSupport.manage_options

    security=ClassSecurityInfo()

    def __init__(self, id, title, store='Image', engine='ImageMagick', quality=75,
                 pregen=0, timeout=0):

        self.__version__ = '1.2.3'
        self.id = id
        self.title = title
        self.image = ''

        # Sheet to store containing photo default settings.
        self.propertysheets.manage_addPropertySheet('photoconf', 'photoconf')
        photoconf = self.propertysheets.get('photoconf')
        photoconf.manage_addProperty('store', store, 'string')
        photoconf.manage_addProperty('engine', engine, 'string')
        photoconf.manage_addProperty('quality', quality, 'int')
        photoconf.manage_addProperty('pregen', pregen, 'boolean')
        photoconf.manage_addProperty('timeout', timeout, 'int')

        # Sheet to store containing photo properties.
        self.propertysheets.manage_addPropertySheet('photos', 'photos')

        # Initialize with default hardcoded sizes.
        self._displays = defaultdisplays.copy()

    #
    # Misc. Photo Folder Methods
    #

    security.declareProtected('Access contents information', 'photoIds')
    def photoIds(self):
        """Return list of Photos in this folder."""
        return self.objectIds(['Photo'])

    def image_select(self):
        return [''] + self.photoIds()

    security.declareProtected('Access contents information', 'numPhotos')
    def numPhotos(self):
        """Return number of Photos in folder tree."""
        photos = len(self.objectIds(['Photo']))
        for folder in self.objectValues(['Photo Folder']):
            photos = photos + folder.numPhotos()
        return photos

    security.declareProtected('Access contents information', 'nextPhotoFolder')
    def nextPhotoFolder(self):
        """Return next Photo Folder."""
        id = self.getId()
        folderIds = self.aq_parent.objectIds(['Photo Folder'])
        folderIds.sort()
        if id == folderIds[-1]:
            return None
        return getattr(self.aq_parent, folderIds[folderIds.index(id)+1])

    security.declareProtected('Access contents information', 'prevPhotoFolder')
    def prevPhotoFolder(self):
        """Return previous Photo Folder."""
        id = self.getId()
        folderIds = self.aq_parent.objectIds(['Photo Folder'])
        folderIds.sort()
        if id == folderIds[0]:
            return None
        return getattr(self.aq_parent, folderIds[folderIds.index(id)-1])

    security.declareProtected('Access contents information', 'displayIds')
    def displayIds(self, exclude=('thumbnail',)):
        """Return list of display Ids."""
        ids = self._displays.keys()
        # Exclude specified displays
        for id in exclude:
            if id in ids:
                ids.remove(id)
        # Sort by size in bytes
        ids.sort(lambda x,y,d=self._displays: cmp(d[x][0]*d[x][1], d[y][0]*d[y][1]))
        return ids

    security.declarePrivate('displayMap')
    def displayMap(self):
        """Return list of displays with size info."""
        displays = []
        for id in self.displayIds([]):
            displays.append({'id': id,
            'width': self._displays[id][0],
            'height': self._displays[id][1],
            })
        return displays

    #
    # Management Interface
    #

    security.declareProtected('Manage properties', 'manage_editPhotoPropertiesForm')
    manage_editPhotoPropertiesForm = DTMLFile('dtml/editPhotoPropertiesForm', globals())

    security.declareProtected('Manage properties', 'manage_editPhotoSettings')
    def manage_editPhotoSettings(self, REQUEST=None):
        """Edit photo settings."""
        photoconf = self.propertysheets.get('photoconf')
        photoconf.manage_editProperties(REQUEST)
        # Update contained Photo objects if requested
        if REQUEST.form.get('changeall', None):
            for photo in self.objectValues(['Photo']):
                REQUEST.set('store', photo.propertysheets.get('photoconf').getProperty('store'))
                photo.propertysheets.get('photoconf').manage_editProperties(REQUEST)
        if REQUEST is not None:
            return self.manage_editPhotoPropertiesForm(REQUEST,
                        manage_tabs_message='Default photo settings updated.')

    security.declareProtected('Manage properties', 'manage_editPhotoProperties')
    def manage_editPhotoProperties(self, REQUEST=None):
        """Edit photo properties."""
        photosheet = self.propertysheets.get('photos')
        photosheet.manage_editProperties(REQUEST)
        if REQUEST is not None:
            return self.manage_editPhotoPropertiesForm(REQUEST,
                        manage_tabs_message='Photo properties updated.')

    security.declareProtected('Manage properties', 'manage_delPhotoProperties')
    def manage_delPhotoProperties(self, ids, REQUEST=None):
        """Delete photo properties."""
        photosheet = self.propertysheets.get('photos')
        photosheet.manage_delProperties(ids)
        # Update contained Photo objects
        for photo in self.objectValues(['Photo']):
            try: photo.manage_delProperties(ids)
            except: pass
        if REQUEST is not None:
            return self.manage_editPhotoPropertiesForm(REQUEST,
                        manage_tabs_message='Photo properties deleted.')

    security.declareProtected('Manage properties', 'manage_addPhotoProperty')
    def manage_addPhotoProperty(self, id, value, type, REQUEST=None):
        """Add photo property."""
        photosheet = self.propertysheets.get('photos')
        photosheet.manage_addProperty(id, value, type)
        # Update contained Photo objects
        for photo in self.objectValues(['Photo']):
            try: photo.manage_addProperty(id, value, type)
            except: pass
        if REQUEST is not None:
            return self.manage_editPhotoPropertiesForm(REQUEST,
                        manage_tabs_message='Photo property added.')

    security.declareProtected('Manage properties', 'manage_editDisplaysForm')
    manage_editDisplaysForm = DTMLFile('dtml/editFolderDisplaysForm', globals())

    security.declareProtected('Manage properties', 'manage_editDisplays')
    def manage_editDisplays(self, displays, REQUEST=None):
        """Edit displays."""
        d = self._displays
        for display in displays:
            if d[display.id] != (display.width, display.height):
                d[display.id] = (display.width, display.height)
        self._displays = d
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays changed.')

    security.declareProtected('Manage properties', 'manage_delDisplays')
    def manage_delDisplays(self, ids, REQUEST=None):
        """Delete displays."""
        d = self._displays
        for id in ids:
            try: del d[id]
            except: pass
        self._displays = d
        # Update contained Photo objects
        for photo in self.objectValues(['Photo']):
            try: photo.manage_delDisplays(ids)
            except: pass
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays deleted.')

    security.declareProtected('Manage properties', 'manage_addDisplay')
    def manage_addDisplay(self, id, width, height, REQUEST=None):
        """Add display."""
        d = self._displays
        d[id] = (width, height)
        self._displays = d
        # Update contained Photo objects
        for photo in self.objectValues(['Photo']):
            try: photo.manage_addDisplay(id, width, height)
            except: pass
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Display added.')

    security.declareProtected('Manage properties', 'manage_regenDisplays')
    def manage_regenDisplays(self, REQUEST=None):
        """Regenerate all displays of contained photos."""
        for photo in self.objectValues(['Photo']):
            photo.manage_regenDisplays()
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays regenerated.')

    security.declareProtected('Manage properties', 'manage_purgeDisplays')
    def manage_purgeDisplays(self, exclude=None, REQUEST=None):
        """Purge all generated displays of contained photos."""
        if exclude is None and REQUEST is not None:
            exclude = REQUEST.form.get('ids', [])
        for photo in self.objectValues(['Photo']):
            photo.manage_purgeDisplays(exclude)
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays purged.')

    security.declareProtected('Manage properties', 'manage_cleanDisplays')
    def manage_cleanDisplays(self, exclude=None, REQUEST=None):
        """Purge all generated displays of contained photos that have expired."""
        if exclude is None and REQUEST is not None:
            exclude = REQUEST.form.get('ids', [])
        for photo in self.objectValues(['Photo']):
            photo.manage_cleanDisplays(exclude)
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Expired displays purged.')

    #
    # WebDAV/FTP support
    #

    def PUT_factory(self, name, typ, body):
        """Create Photo objects by default for image types."""
        if typ[:6] == 'image/':
            store = self.propertysheets.get('photoconf').getProperty('store')
            photo = Photo(name, '', '', store=store)

            # Init properties with defaults
            props = self.propertysheets.get('photos')
            for propid, value in props.propertyItems():
                try: photo.manage_addProperty(propid, value, props.getPropertyType(propid))
                except: pass

            # Init settings with defaults
            photoconf = self.propertysheets.get('photoconf')
            settings = {}
            for propid, value in photoconf.propertyItems():
                settings[propid] = value
            photo.propertysheets.get('photoconf').manage_changeProperties(settings)

            # Init displays with defaults
            photo._displays = self._displays.copy()
            return photo

        return None

#
# Factory methods
#

manage_addPhotoFolderForm = DTMLFile('dtml/addPhotoFolderForm', globals())

def manage_addPhotoFolder(dispatcher, id, title, store='Image',
                          engine='ImageMagick', quality=75, pregen=0, timeout=0,
                          createsamples=0, REQUEST=None):
    """Add Photo Folder object"""
    dest = dispatcher.Destination()
    dest._setObject(id, PhotoFolder(id, title, store, engine, quality, pregen, timeout))
    if createsamples:
        self = dest._getOb(id)
        sampleView = DTMLFile('dtml/sampleView', globals())
        self.manage_addDTMLMethod('view', '')
        self._getOb('view').manage_edit(sampleView, 'Sample View')
        sampleFolderView = DTMLFile('dtml/sampleFolderView', globals())
        self.manage_addDTMLMethod('index_html', '')
        self._getOb('index_html').manage_edit(sampleFolderView, 'Sample Folder View')

    if REQUEST is not None:
        try:    url=dispatcher.DestinationURL()
        except: url=REQUEST['URL1']
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
    return id

InitializeClass(PhotoFolder)
