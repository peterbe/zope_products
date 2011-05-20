##############################################################################
#
# Copyright (c) 2006 Fry-IT Ltd. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

# python
import re, sys, os, urllib


# Zope
from AccessControl import ClassSecurityInfo
from Globals import Persistent, InitializeClass, package_home, DTMLFile
from OFS import Folder, SimpleItem
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from Acquisition import aq_parent, aq_inner
from DateTime import DateTime

import Utils
from Constants import *

#----------------------------------------------------------------------------


manage_addFryingDocumentPanForm = DTMLFile('dtml/add_pan', globals())

def manage_addFryingDocumentPan(dispatcher, id='Document-Pan', REQUEST=None):
    """ create the object """
    dest = dispatcher.Destination()
    
    inst = DocumentPan(id)
    dest._setObject(id, inst)
    pan = dest._getOb(id)
    
    if REQUEST is not None:
        redirect = REQUEST.RESPONSE.redirect
        url = pan.absolute_url()+'/manage_workspace'
        params = {'manage_tabs_message':'Document Pan created'}
        url = Utils.AddParams2URL(url, params)
        redirect(url)
    else:
        return pan
    

#----------------------------------------------------------------------------


class DocumentPan(SimpleItem.SimpleItem):
    """ A simple object that makes it possible to talk to all FriedDocument
    objects in the current folder. With the FryingPan you can set properties
    on Fried Documents in a batched manner. """
    
    meta_type = PAN_META_TYPE

    manage_options = ({'label':'Document Pan', 'action':'manage_Pan_main'},)+\
                     (SimpleItem.SimpleItem.manage_options[0],)
    
    security = ClassSecurityInfo()
    def __init__(self, id='Document-Pan'):
        """ init """
        self.id = str(id)
        
    security.declareProtected(VMS, 'getDocumentPaths')
    def getDocumentPaths(self, sort=0, recursive=1, start_path='',
                         include_folderish=False,
                         only_meta_types=None):
        """ return a list of relative paths to all Fried Document objects """
        daddy = aq_parent(aq_inner(self))
        if daddy.meta_type == PAN_META_TYPE:
            daddy = aq_parent(aq_inner(daddy))
        
        if not start_path:
            start_dig_in = daddy
        else:
            # start_path must exist
            start_dig_in = daddy.restrictedTraverse(start_path)

        if only_meta_types is not None:
            if isinstance(only_meta_types, basestring):
                only_meta_types = [only_meta_types]
                
        paths = self._getDocumentPaths(start_dig_in, recursive, 
                        include_folderish=include_folderish,
                        only_meta_types=only_meta_types)
        if sort:
            paths.sort()
        return paths
    
    
    security.declareProtected(VMS, 'careful_isPrincipiaFolderish')
    def careful_isPrincipiaFolderish(self, obj):
        """ because we have seen problems with objectValues() returning
        LazyMap objects (non-Zope), it's not always possible to 
        check fot .isPrincipiaFolderish through templates. This wrapper
        function makes it possible. """
        return self._isPrincipiaFolderish(obj)
        
    def _isPrincipiaFolderish(self, obj):
        """ use .isPrincipiaFolderish but be more careful """
        try:
            return obj.isPrincipiaFolderish
        except AttributeError:
            return False

    
    def _getDocumentPaths(self, to_dig_in, recursive, include_folderish,
                          only_meta_types=None):
        """ return a list of relative paths to all Fried Document objects """
        paths = []

        pather = lambda folder, obj: '/'.join(folder.getPhysicalPath())+'/'+object.getId()
        for object in to_dig_in.objectValues():
            
            if object.meta_type == META_TYPE:
                paths.append(pather(to_dig_in, object))
                
            elif include_folderish and self._isPrincipiaFolderish(object):
                if only_meta_types is None or object.meta_type in only_meta_types:
                    paths.append(pather(to_dig_in, object))
            
            if self._isPrincipiaFolderish(object) and recursive:
                paths.extend(self._getDocumentPaths(object, recursive, include_folderish,
                                                    only_meta_types=only_meta_types))

        return paths

    
    security.declareProtected(VMS, 'getDocumentObjects')
    def getDocumentObjects(self, sort=0):
        """ return a list of object references """
        objects = []
        for path in self.getDocumentPaths(sort=sort):
            objects.append(self.unrestrictedTraverse(path))
        return objects
        
    security.declareProtected(VMS, 'calculateDocumentPath')
    def calculateDocumentPath(self, documenturl):
        """ return the path (relative to the pan parent """
        
        daddy = self.aq_parent
        if daddy.meta_type == PAN_META_TYPE:
            daddy = daddy.aq_parent
        
        return documenturl.replace(daddy.absolute_url(),'')
    
    #
    # Actions
    #
    
    def manage_cookAll(self, REQUEST=None):
        """ cook all templates """
        for object in self.getDocumentObjects():
            object._cook()
            
        if REQUEST is not None:
            return self.manage_Pan_main(self, REQUEST, 
                         manage_tabs_message="All documents cooked")

        
    def manage_updateAll(self, REQUEST=None, goto_after=None):
        """ update all templates """
        for object in self.getDocumentObjects():
            object.manage_Update()
            
        if REQUEST is not None:
            if goto_after:
                self.http_redirect(goto_after, 
                                   manage_tabs_message="All documents updated")
            else:
                return self.manage_Pan_main(self, REQUEST, 
                     manage_tabs_message="All documents updated")
        
        
    #
    # Batch jobs
    #
    
    def manage_setAllExpiryHeaders(self, applicable_paths, hours, 
                                   commonhours=None, common=False,
                                   batch=[],
                                   REQUEST=None):
        """ applicable_paths is a list of all paths that were as options in the list.
        By looping over this we'll be able to find stuff like 'hours' """
        checked_boxes = batch
        assert isinstance(checked_boxes, (list, tuple)), "Batch must be a list"
        
        path2object = {}
        for documentobject in self.getDocumentObjects():
            documentpath = self.calculateDocumentPath(documentobject.absolute_url())
            path2object[documentpath] = documentobject
            
        if common:
            try:
                commonhours = float(commonhours)
            except ValueError:
                raise ValueError, "The common hour set on all checked must be float"
        
        for i in range(len(applicable_paths)):
            path = applicable_paths[i]
            checked = path in batch
            #print path, checked, hours[i]
            hours_ = float(hours[i])
            if common:
                if checked:
                    obj = path2object[path]
                    if commonhours==0.0:
                        obj.manage_setExpiryOptions(commonhours, disable=True)
                    else:
                        obj.manage_setExpiryOptions(commonhours)
            else:
                obj = path2object[path]
                if hours_==0.0:
                    obj.manage_setExpiryOptions(hours_, disable=True)
                else:
                    obj.manage_setExpiryOptions(hours_)
            
        if REQUEST is not None:
            return self.manage_Pan_ExpiryHeaders(self, REQUEST, 
              manage_tabs_message="Expiry headers set")
    
    def manage_setAllCSSURLs(self, css_url, exception_paths=[],
                             REQUEST=None):
        """ set the CSSURL of many documents """
        css_url = css_url.strip()
        for documentobject in self.getDocumentObjects():
            documentpath = self.calculateDocumentPath(documentobject.absolute_url())
            if documentpath in exception_paths:
                continue
            # else
            documentobject.manage_setCSSURL(css_url)
            
            
        if REQUEST is not None:
            return self.manage_Pan_CSSURLs(self, REQUEST, 
              manage_tabs_message="CSS URLs set")
        
    #
    # Templates
    #
        
    security.declareProtected(VMS, 'manage_Pan_main')
    manage_Pan_main = DTMLFile('dtml/pan_main', globals())
    manage_Pan_main._setName('manage_Pan_main')
    
    security.declareProtected(VMS, 'manage_Pan_showall')
    manage_Pan_showall = DTMLFile('dtml/pan_show_all', globals())

    security.declareProtected(VMS, 'manage_Pan_CSSURLs')
    manage_Pan_CSSURLs = DTMLFile('dtml/pan_batch_cssurls', globals())

    security.declareProtected(VMS, 'manage_Pan_ExpiryHeaders')
    manage_Pan_ExpiryHeaders = DTMLFile('dtml/pan_expiry_headers', globals())
    
    security.declareProtected(VMS, 'manage_pan_header')
    manage_pan_header = DTMLFile('dtml/manage_pan_header', globals())
    
    security.declareProtected(VMS, 'manage_pan_footer')
    manage_pan_footer = DTMLFile('dtml/manage_pan_footer', globals())
    
    
    index_html = manage_Pan_main
        
        
InitializeClass(DocumentPan)