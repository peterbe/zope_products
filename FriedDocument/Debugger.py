##############################################################################
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

import sys
from cStringIO import StringIO
from pprint import pprint

from Products.PythonScripts.standard import html_quote

import Utils
from Constants import *


class BadInstanceError(Exception):
    pass
    
class DebuggerBase:
    """ A collection of debugger scripts and stuff that you can use inside the
    Fried Document class.
    """
    
    def pprint_texts(self, slot=None, ignore_versioning=False, REQUEST=None):
        """ return a string of info about all the _texts """
        show_only_slot = slot
        _texts = self._getTexts(ignore_versioning=ignore_versioning)
        
        # If for some reason the _texts is completely blank,
        # which can really only happen when in versioning.
        #if _texts == {} and self.inVersioning():
        #    self._initVersioningTexts()
        #    _texts = self._getTexts()
        #    print _texts
        
        
        # redirect stdout
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout
        
        if self.inVersioning():
            print "*** FRIED DOCUMENT IN VERSIONING ***"
            #print "*** consider using %s ***" % \
            #  self.REQUEST.URL.replace('pprint_texts','pprint_texts_versioning')
            
        slots = self.manage_getSlots()
        slots = Utils.uniqify(slots + _texts.keys()) 
        for slot in slots:
            if show_only_slot and slot != show_only_slot:
                continue
            
            revisions = _texts[slot]
            print "SLOT %s:\n" % slot
            if isinstance(revisions, dict):
                print "** OLD STYLE FRIED DOCUMENT (PLEASE UPDATE) **"
                mod_time = self.bobobase_modification_time()
                revisions['revision_timestamp'] = float(mod_time)-1
                revisions = [revisions]

            keys = ['format','raw','rendered','editable','wysiwyg']+revisions[0].keys()
            keys = Utils.uniqify(keys)
            if 'revision_timestamp' in keys:
                keys.remove('revision_timestamp')
            for revision in revisions:
                print "  Revision: %s" % revision['revision_timestamp']
                for key in keys:
                    value = revision[key]
                    if key in ('raw','rendered'):
                        if value and len(value) > 50:
                            size = len(value)
                            value = repr(value[:50])+"... [%s characters]" % size
                            
                        # if we send this as text/plain we don't need to html_quote 
                        # it.
                        if REQUEST:
                            value = str(value)
                        else:
                            value = html_quote(str(value))
                        
                    print "\t%s: %s" % (key, value)
                print ""
            
        out = new_stdout.getvalue()
        sys.stdout = old_stdout
        
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type','text/plain')
            
        return out
            
