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

"""Photo

Photo objects provide a way to manage various display sizes of an image.
They are very similar to Zope Image objects but generate and store
multiple copies of the image in different sizes.
"""

import sys, string
from OFS.Image import Image, cookId
from Acquisition import Implicit
from Globals import Persistent
from OFS.SimpleItem import Item
from OFS.PropertyManager import PropertyManager
from OFS.PropertySheets import PropertySheet
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile
from Products.PythonScripts.standard import html_quote
try:
    from webdav.WriteLockInterface import WriteLockInterface
    from webdav.Lockable import ResourceLockedError
except ImportError: pass
from cStringIO import StringIO
try: import PIL.Image
except ImportError: pass
import time

defaultdisplays = {'thumbnail': (128,128),
                   'xsmall': (200,200),
                   'small': (320,320),
                   'medium': (480,480),
                   'large': (768,768),
                   'xlarge': (1024,1024)
                  }


class Photo(Implicit, Persistent, PropertyManager, RoleManager, Item):
    """Photo object.

    Photo objects contain as properties a series of resized
    Zope Image objects according to the given display sizes.
    """

    try: __implements__ = (WriteLockInterface,)
    except NameError: pass

    meta_type = "Photo"

    _properties = (
        {'id':'title', 'type': 'string', 'mode': 'w'},
        )

    manage_options = (
        {'label': 'Edit', 'action': 'manage_editPhotoForm'},
        {'label': 'View', 'action': 'manage_viewPhoto'},
        {'label': 'Settings', 'action': 'manage_editSettingsForm'},
        {'label': 'Displays', 'action': 'manage_editDisplaysForm'},
        ) + PropertyManager.manage_options \
          + RoleManager.manage_options \
          + Item.manage_options

    security=ClassSecurityInfo()

    def __init__(self, id, title, file, content_type='', precondition='',
                 store='Image', engine='ImageMagick', quality=75, pregen=0, timeout=0):

        self.__version__ = '1.2.3'
        self.id = id
        self.title = title

        # Sheet to store photo settings.
        self.propertysheets.manage_addPropertySheet('photoconf', 'photoconf')
        photoconf = self.propertysheets.get('photoconf')
        photoconf.manage_addProperty('store', store, 'string')
        photoconf.manage_addProperty('engine', engine, 'string')
        photoconf.manage_addProperty('quality', quality, 'int')
        photoconf.manage_addProperty('pregen', pregen, 'boolean')
        photoconf.manage_addProperty('timeout', timeout, 'int')

        # Initialize with default hardcoded sizes.
        self._displays = defaultdisplays.copy()
        self._photos = {}

    #
    # Original photo attributes
    #

    security.declareProtected('Access contents information', 'height')
    def height(self):
        """Original photo height."""
        return self._original._height()

    security.declareProtected('Access contents information', 'width')
    def width(self):
        """Original photo width."""
        return self._original._width()

    security.declareProtected('Access contents information', 'size')
    def size(self):
        """Original photo size in bytes."""
        return self._original._size()

    security.declareProtected('Access contents information', 'content_type')
    def content_type(self):
        """Original photo content_type."""
        return self._original._content_type()

    #
    # Photo display methods
    #

    security.declareProtected('View', 'tag')
    def tag(self, display=None, height=None, width=None, cookie=0,
            alt=None, css_class=None, **kw):
        """Return HTML img tag."""

        # Get cookie if display is not specified.
        if display is None:
            display = self.REQUEST.cookies.get('display', None)

        # display may be set from a cookie.
        if display is not None and self._displays.has_key(display):
            if not self._isGenerated(display):
                # Generate photo on-the-fly
                self._makeDisplayPhoto(display, 1)
            image = self._photos[display]
            width, height = (image._width(), image._height())
            # Set cookie for chosen size
            if cookie:
                self.REQUEST.RESPONSE.setCookie('display', display, path="/")
        else:
            # TODO: Add support for on-the-fly resize?
            height = self._original._height()
            width = self._original._width()
            
        if display:
            result = '<img src="%s?display=%s"' % (self.absolute_url(), display)
        else:
            result = '<img src="%s"' % (self.absolute_url())

        if alt is None:
            alt = getattr(self, 'title', '')
        if alt == '':
            alt = self.getId()
        result = '%s alt="%s"' % (result, html_quote(alt))

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if not 'border' in map(string.lower, kw.keys()):
            result = '%s border="0"' % (result)

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in kw.keys():
            value = kw.get(key)
            result = '%s %s="%s"' % (result, key, value)

        result = '%s />' % (result)

        return result

    security.declareProtected('View', 'exttag')
    def exttag(self, prefix, display=None, height=None, width=None, cookie=0,
               alt=None, css_class=None, **kw):
        """Return HTML img tag for serving outside Zope."""

        # Get cookie if display is not specified.
        if display is None:
            display = self.REQUEST.cookies.get('display', None)

        # display may be set from a cookie.
        if display is not None and self._displays.has_key(display):
            if not self._isGenerated(display):
                # Generate photo on-the-fly
                self._makeDisplayPhoto(display, 1)
            image = self._photos[display]
            width, height = (image._width(), image._height())
            # Set cookie for chosen size
            if cookie:
                self.REQUEST.RESPONSE.setCookie('display', display, path="/")

        if prefix[-1] != '/':
            prefix = prefix + '/'

        if display:
            
            filename = self._photos[display].filename
        else:
            filename = self._original.filename

        if type(filename) == type([]):
            filename = prefix + string.join(filename, '/')
        else:
            filename = prefix + filename

        result = '<img src="%s"' % (filename)

        if alt is None:
            alt = getattr(self, 'title', '')
        if alt == '':
            alt = self.getId()
        result = '%s alt="%s"' % (result, html_quote(alt))

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if not 'border' in map(string.lower, kw.keys()):
            result = '%s border="0"' % (result)

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in kw.keys():
            value = kw.get(key)
            result = '%s %s="%s"' % (result, key, value)

        result = '%s />' % (result)

        return result

    def __str__(self):
        return self.tag()

    security.declareProtected('Access contents information', 'displayIds')
    def displayIds(self, exclude=('thumbnail',)):
        """Return list of display Ids."""
        ids = self._displays.keys()
        # Exclude specified displays
        if exclude:
            for id in exclude:
                if id in ids:
                    ids.remove(id)
        # Sort by desired photo surface area
        ids.sort(lambda x,y,d=self._displays: cmp(d[x][0]*d[x][1], d[y][0]*d[y][1]))
        return ids

    security.declareProtected('Access contents information', 'displayLinks')
    def displayLinks(self, exclude=('thumbnail',)):
        """Return list of HTML <a> tags for displays."""
        links = []
        for display in self.displayIds(exclude):
            links.append('<a href="%s?display=%s">%s</a>' % (self.REQUEST['URL'], display, display))
        return links

    security.declareProtected('Access contents information', 'displayMap')
    def displayMap(self, exclude=None):
        """Return list of displays with size info."""
        displays = []
        for id in self.displayIds(exclude):
            if self._isGenerated(id):
                photo_width = self._photos[id]._width()
                photo_height = self._photos[id]._height()
                bytes = self._photos[id]._size()
                age = self._photos[id]._age()
            else:
                (photo_width, photo_height, bytes, age) = (None, None, None, None)
            displays.append({'id': id,
                             'width': self._displays[id][0],
                             'height': self._displays[id][1],
                             'photo_width': photo_width,
                             'photo_height': photo_height,
                             'bytes': bytes,
                             'age': age
                             })
        return displays

    security.declareProtected('View', 'index_html')
    def index_html(self, REQUEST, RESPONSE, display=None):
        """Return the image data."""

        # display may be set from a cookie (?)
        if display and self._displays.has_key(display):
            if not self._isGenerated(display):
                # Generate photo on-the-fly
                self._makeDisplayPhoto(display, 1)
            else:
                timeout = self.propertysheets.get('photoconf').getProperty('timeout')
                if timeout and self._photos[display]._age() > (timeout / 2):
                    self._expireDisplays((display,), timeout)
            # Return resized image
            return self._photos[display].index_html(REQUEST, RESPONSE)

        # Return original image
        return self._original.index_html(REQUEST, RESPONSE)

    security.declareProtected('Access contents information', 'nextPhoto')
    def nextPhoto(self):
        """Return next Photo in folder."""
        id = self.getId()
        photoIds = self.aq_parent.objectIds(['Photo'])
        photoIds.sort()
        if id == photoIds[-1]:
            return None
        return getattr(self.aq_parent, photoIds[photoIds.index(id)+1])

    security.declareProtected('Access contents information', 'prevPhoto')
    def prevPhoto(self):
        """Return previous Photo in folder."""
        id = self.getId()
        photoIds = self.aq_parent.objectIds(['Photo'])
        photoIds.sort()
        if id == photoIds[0]:
            return None
        return getattr(self.aq_parent, photoIds[photoIds.index(id)-1])

    security.declareProtected('View', 'get_size')
    def get_size(self):
        """Return size in bytes of original photo."""
        return self._original.get_size()

    #
    # Photo processing
    #

    def _resize(self, display, width, height, engine='ImageMagick', quality=75):
        """Resize and resample photo."""
        origimg = self._original
        newimg = StringIO()
        if engine == 'PIL':  # Use PIL
            img = PIL.Image.open(origimg._PILdata())
            fmt = img.format
            img = img.resize((width, height))
            img.save(newimg, fmt, quality=quality)
        elif engine == 'ImageMagick':  # Use ImageMagick
            if sys.platform == 'win32':
                from win32pipe import popen2
                imgin, imgout = popen2('convert -quality %s -geometry %sx%s - -'
                                       % (quality, width, height), 'b')
            else:
                from popen2 import popen2
                imgout, imgin = popen2('convert -quality %s -geometry %sx%s - -'
                                       % (quality, width, height))
            imgin.write(origimg._IMdata())
            imgin.close()
            newimg.write(imgout.read())
            imgout.close()

        newimg.seek(0)
        return newimg

    def _getDisplayData(self, display):
        """Return raw photo data for given display."""
        (width, height) = self._displays[display]
        if width == 0 and height == 0:
            width = self._original._width()
            height = self._original._height()
        (width, height) = self._getAspectRatioSize(width, height)
        engine = self.propertysheets.get('photoconf').getProperty('engine')
        quality = self.propertysheets.get('photoconf').getProperty('quality')
        return self._resize(display, width, height, engine, quality)
        
    def _getDisplayPhoto(self, display):
        """Return photo object for given display."""
        try:
            base, ext = string.split(self.id, '.')
            id = base+'_'+display+'.'+ext
        except ValueError:
            id = self.id+'_'+display
        return self._original._newImage(id, self._getDisplayData(display), self.absolute_url(1))

    def _makeDisplayPhoto(self, display, force=0):
        """Create given display."""
        if self._shouldGenerate(display) or force:
            photo = self._photos
            if photo.has_key(display):
                print photo[display]
                print dir(photo[display])
                print type(photo[display])
                print photo[display].meta_type
                photo[display].manage_upload(self._getDisplayData(display), self.content_type())
            else:
                photo[display] = self._getDisplayPhoto(display)
            self._photos = photo

    def _makeDisplayPhotos(self):
        """Create all displays."""
        for display in self._displays.keys():
            self._makeDisplayPhoto(display)
            
    def _getAspectRatioSize(self, width, height):
        """Return proportional dimensions within desired size."""
        img_width, img_height = (self.width(), self.height())
        if height > img_height * width / img_width:
            height = img_height * width / img_width
        else:
            width =  img_width * height / img_height
        return (width, height)

    def _validImage(self):
        """At least see if it *might* be valid."""
        return self._original._isValid()

    def _isGenerated(self, display):
        """Return whether display has been generated."""
        return self._photos.has_key(display)

    def _shouldGenerate(self, display):
        """Return whether display should be generated."""
        return (self._isGenerated(display) or
               self.propertysheets.get('photoconf').getProperty('pregen'))

    def _expireDisplays(self, exclude=[], timeout=None):
        """Remove displays that have expired."""

        if timeout is None:
            timeout = self.propertysheets.get('photoconf').getProperty('timeout')
        if not timeout:
            return
        photos = self._photos
        for d in self._photos.keys():
            if d in exclude:
                self._photos[d]._p_changed = 1
            elif self._photos[d]._age() > timeout:
                photos[d].manage_beforeDelete(None, None)  # ExtImage support
                del photos[d]
        self._photos = photos

    #
    # FTP/WebDAV support
    #

    security.declareProtected('Change Photo', 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests."""
        self.dav__init(REQUEST, RESPONSE)
        if hasattr(self, 'dav__simpleifhandler'):
            self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        file=REQUEST['BODYFILE']
        
        if hasattr(self, '_original'):
            # Updating existing Photo
            self._original.manage_upload(file, self.content_type())
            if self._validImage():
                self._makeDisplayPhotos()
        else:
            # Adding a new Photo.
            # At this point, the object is not yet in its final context.
            # Since ExtImage needs to know the URL of the new Photo object
            # so it can determine where to create new files, we store
            # the image data and let manage_afterAdd() generate the displays
            # once the Photo is in its final context.
            self._data = file.read()
            
        RESPONSE.setStatus(204)
        return RESPONSE

    security.declareProtected('FTP access', 'manage_FTPget', 'manage_FTPstat', 'manage_FTPlist')
    def manage_FTPget(self):
        """Handle GET requests."""
        return self._original._data()

    def manage_FTPstat(self, REQUEST):
        """Handle STAT requests."""
        return self._original.manage_FTPstat(REQUEST)

    def manage_FTPlist(self, REQUEST):
        """Handle LIST requests."""
        return self._original.manage_FTPlist(REQUEST)

    #
    # Management Interface
    #

    security.declareProtected('View management screens', 'manage_viewPhoto')
    manage_viewPhoto = DTMLFile('dtml/viewPhoto', globals())

    security.declareProtected('View management screens', 'manage_editPhotoForm')
    manage_editPhotoForm = DTMLFile('dtml/editPhotoForm', globals())

    security.declareProtected('Change Photo', 'manage_editPhoto')
    def manage_editPhoto(self, file='', REQUEST=None):
        """Changes Photo information."""
        if hasattr(self, 'wl_isLocked') and self.wl_isLocked():
            raise ResourceLockedError, "Photo is locked via WebDAV."
        self.manage_changeProperties(REQUEST)
        if file and file.filename:
            self._original.manage_upload(file, self.content_type())
            if self._validImage():
                self._makeDisplayPhotos()
        if REQUEST is not None:
            return self.manage_editPhotoForm(REQUEST,
                manage_tabs_message='Photo information updated.')

    security.declareProtected('View management screens', 'manage_editSettingsForm')
    manage_editSettingsForm = DTMLFile('dtml/editSettingsForm', globals())

    security.declareProtected('Manage properties', 'manage_editSettings')
    def manage_editSettings(self, REQUEST=None):
        """Edit photo settings."""
        photoconf = self.propertysheets.get('photoconf')
        photoconf.manage_editProperties(REQUEST)
        if REQUEST is not None:
            return self.manage_editSettingsForm(REQUEST,
        manage_tabs_message='Photo settings updated.')

    security.declareProtected('View management screens', 'manage_editDisplaysForm')
    manage_editDisplaysForm = DTMLFile('dtml/editDisplaysForm', globals())

    security.declareProtected('Manage properties', 'manage_editDisplays')
    def manage_editDisplays(self, displays, manage_editDisplays=None, REQUEST=None):
        """Edit displays."""
        d = self._displays
        p = self._photos
        for display in displays:
            if (d[display.id] != (display.width, display.height) or
                  manage_editDisplays == ' Regenerate All '):
                d[display.id] = (display.width, display.height)
                if self._shouldGenerate(display.id):
                    p[display.id].manage_beforeDelete(None, None)  # ExtImage support
                    p[display.id] = self._getDisplayPhoto(display.id)
        self._displays = d
        self._photos = p
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays changed.')

    security.declareProtected('Manage properties', 'manage_delDisplays')
    def manage_delDisplays(self, ids, REQUEST=None):
        """Delete displays."""
        d = self._displays
        p = self._photos
        for id in ids:
            try:
                del d[id]
                p[id].manage_beforeDelete(None, None)  # ExtImage support
                del p[id]
            except: pass
        self._displays = d
        self._photos = p
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays deleted.')

    security.declareProtected('Manage properties', 'manage_addDisplay')
    def manage_addDisplay(self, id, width, height, REQUEST=None):
        """Add display."""
        d = self._displays
        p = self._photos
        d[id] = (width, height)
        if self._shouldGenerate(id):
            p[id] = self._getDisplayPhoto(id)
        self._displays = d
        self._photos = p
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Display added.')

    security.declareProtected('Change Photo', 'manage_regenDisplays')
    def manage_regenDisplays(self, REQUEST=None):
        """Regenerate all displays."""
        self._makeDisplayPhotos()
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays regenerated.')

    security.declareProtected('Change Photo', 'manage_purgeDisplays')
    def manage_purgeDisplays(self, exclude=None, REQUEST=None):
        """Purge generated displays."""
        if exclude is None and REQUEST is not None:
            exclude = REQUEST.form.get('ids', [])
        self._expireDisplays(exclude or [], -1)
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Displays purged.')

    security.declareProtected('Change Photo', 'manage_cleanDisplays')
    def manage_cleanDisplays(self, exclude=None, REQUEST=None):
        """Purge all generated displays that have expired."""
        if exclude is None and REQUEST is not None:
            exclude = REQUEST.form.get('ids', [])
        self._expireDisplays(exclude or [])
        if REQUEST is not None:
            return self.manage_editDisplaysForm(REQUEST,
                manage_tabs_message='Expired displays purged.')

    #
    # ExtImage management support
    #

    def manage_afterClone(self, item):
        """Prepare photos for cloning."""
        self._original.manage_afterClone(item)
        for photo in self._photos.values():
            photo.manage_afterClone(item)

    def manage_afterAdd(self, item, container):
        """Handle pasting of new photos."""
        if not hasattr(self, '_original'):
            # Added Photo (vs. imported)
            # See note in PUT()
            store = self.propertysheets.get('photoconf').getProperty('store')
            if store == 'Image': from PhotoImage import PhotoImage
            elif store == 'ExtImage': from ExtPhotoImage import PhotoImage
            self._original = PhotoImage(self.id, self.title, path=self.absolute_url(1))
            self._original.manage_upload(StringIO(self._data), self.content_type())
            delattr(self, '_data')
            if self._validImage():
                self._makeDisplayPhotos()

        self._original.manage_afterAdd(item, container)
        if hasattr(self, '_photos'):
            for photo in self._photos.values():
                photo.manage_afterAdd(item, container)

    def manage_beforeDelete(self, item, container):
        """Delete (mark for undo) each photo file."""
        self._original.manage_beforeDelete(item, container)
        for photo in self._photos.values():
            photo.manage_beforeDelete(item, container)

#
# Factory methods
#

manage_addPhotoForm = DTMLFile('dtml/addPhotoForm', globals())

def manage_addPhoto(dispatcher, id, title, file,
                    content_type='', precondition='',
                    store='Image', engine='ImageMagick', quality=75,
                    timeout=0, pregen=0, REQUEST=None):
    """Add Photo object."""
    id = cookId(id, title, file)[0]
    dest = dispatcher.Destination()
    photo = Photo(id, title, '', content_type, precondition,
                  store, engine, quality, pregen, timeout)
    photo._data = file.read()
    dest._setObject(id, photo)
    # Images are generated at this point by manage_afterAdd()
    
    self = dest._getOb(id)
    # Init properties and displays from Photo Folder if present
    parent = self.aq_parent
    if parent.meta_type == 'Photo Folder':
        props = parent.propertysheets.get('photos')
        for propid, value in props.propertyItems():
            try: self.manage_addProperty(propid, value, props.getPropertyType(propid))
            except: pass
        self._displays = parent._displays.copy()

    if REQUEST is not None:
        try:    url=dispatcher.DestinationURL()
        except: url=REQUEST['URL1']
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
    return id

InitializeClass(Photo)
