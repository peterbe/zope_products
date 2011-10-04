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

"""Upgrade

These functions provides upgrade support for prior versions of Photo and
Photo Folder objects.
"""

from string import join

__version__ = '1.2.3'

def upgrade_PhotoFolder(self):
    """Upgrade prior Photo Folder objects."""

    # Already up to date?
    if hasattr(self, '__version__') and self.__version__ == __version__:
        return None
    
    # Upgrade 0.9.x/1.0.x/1.1.x to 1.2.0
    if not hasattr(self, '__version__'):

        self.__version__ = '1.2.0'
        
        engine = self.engine
        store = self.store
        sheet=self.propertysheets.get('default')
        vself = sheet.v_self()
        delattr(vself, 'engine')
        delattr(vself, 'store')
        pself=sheet.p_self()
        pself._properties=tuple(filter(lambda i, n='engine': i['id'] != n, pself._properties))
        pself._properties=tuple(filter(lambda i, n='store': i['id'] != n, pself._properties))
        
        self.propertysheets.manage_addPropertySheet('photoconf', 'photoconf')
        self.propertysheets.get('photoconf').manage_addProperty('store', store, 'string')
        self.propertysheets.get('photoconf').manage_addProperty('engine', engine, 'string')
        
    # Upgrade 1.2.0 to 1.2.1
    if self.__version__ < '1.2.1':
        self.__version__ = '1.2.1'
        self.propertysheets.get('photoconf').manage_addProperty('quality', 75, 'int')

    # Upgrade 1.2.1 to 1.2.2
    if self.__version__ < '1.2.2':
        self.__version__ = '1.2.2'
        self.propertysheets.get('photoconf').manage_addProperty('pregen', 0, 'boolean')
        self.propertysheets.get('photoconf').manage_addProperty('timeout', 0, 'int')
        
    # Upgrade 1.2.2 to 1.2.3
    if self.__version__ < '1.2.3':
        self.__version__ = '1.2.3'
        
def upgrade_Photo(self):
    """Upgrade prior Photo objects."""

    # Already up to date?
    if hasattr(self, '__version__') and self.__version__ == __version__:
        return None
    
    # Upgrade 0.9.x/1.0.x/1.1.x to 1.2.0
    if not hasattr(self, '__version__'):

        self.__version__ = '1.2.0'

        engine = self.engine
                
        # Dig for store since I didn't bother saving it before.
        if hasattr(self._original, 'rawsize'):
            store = 'ExtImage'
        else:
            store = 'Image'
        sheet=self.propertysheets.get('default')
        vself = sheet.v_self()
        delattr(vself, 'engine')
        pself=sheet.p_self()
        pself._properties=tuple(filter(lambda i, n='engine': i['id'] != n, pself._properties))
        
        self.propertysheets.manage_addPropertySheet('photoconf', 'photoconf')
        self.propertysheets.get('photoconf').manage_addProperty('engine', engine, 'string')
        self.propertysheets.get('photoconf').manage_addProperty('store', store, 'string')
	
    # Upgrade 1.2.0 to 1.2.1
    if self.__version__ < '1.2.1':
        self.__version__ = '1.2.1'
        self.propertysheets.get('photoconf').manage_addProperty('quality', 75, 'int')

    # Upgrade 1.2.1 to 1.2.2
    if self.__version__ < '1.2.2':
        self.__version__ = '1.2.2'
        self.propertysheets.get('photoconf').manage_addProperty('pregen', 0, 'boolean')
        self.propertysheets.get('photoconf').manage_addProperty('timeout', 0, 'int')

    # Upgrade 1.2.2 to 1.2.3
    if self.__version__ < '1.2.3':
        self.__version__ = '1.2.3'
        
        # Fix older, maybe broken upgrades
        if not self.propertysheets.get('photoconf').hasProperty('store'):
            if hasattr(self._original, 'rawsize'):
                store = 'ExtImage'
            else:
                store = 'Image'
            self.propertysheets.get('photoconf').manage_addProperty('store', store, 'string')
    
def upgrade(self, REQUEST=None):
    """Upgrade all Photo Folders and Photos in the tree."""

    output = '<p>The following objects were upgraded:</p>'
        
    folders = self.ZopeFind(self, obj_metatypes=['Photo Folder'], search_sub=1)
    for (id, folder) in folders:
        upgrade_PhotoFolder(folder)
        output = output + ('Photo Folder <tt>' + join(folder.getPhysicalPath(), '/') +
            '</tt><br>\n')
    
    photos = self.ZopeFind(self, obj_metatypes=['Photo'], search_sub=1)
    for (id, photo) in photos:
        upgrade_Photo(photo)
        output = output + ('Photo <tt>' + join(photo.getPhysicalPath(), '/') +
            '</tt><br>\n')
            
    if REQUEST is not None:
        return output

def version(self, REQUEST):
    """Show versions of all Photo Folders and Photos in the tree."""

    output = ''
    folders = self.ZopeFind(self, obj_metatypes=['Photo Folder'], search_sub=1)
    for (id, folder) in folders:
        output = output + ('Photo Folder <tt>' + join(folder.getPhysicalPath(), '/') +
            '</tt> - ' + getattr(folder, '__version__', 'None') + '<br>\n')
    
    photos = self.ZopeFind(self, obj_metatypes=['Photo'], search_sub=1)
    for (id, photo) in photos:
        output = output + ('Photo <tt>' + join(photo.getPhysicalPath(), '/') +
            '</tt> - ' + getattr(photo, '__version__', 'None') + '<br>\n')

    return output
