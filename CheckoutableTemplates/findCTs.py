##
## CheckoutableTemplates,
## By Peter Bengtsson, mail@peterbe.com, www.peterbe.com
## Copyright 2003-2008
## License ZPL
##


__doc__="""extract which templates can be checked out"""
import os, StringIO, re

from Products.PythonScripts.standard import html_quote, newline_to_br
from ExtensionClass import Base
from AccessControl.SecurityInfo import ClassSecurityInfo

# Attempt to import fancy SilverCity formatting
try:
    from SilverCity import XML as SC_XML
    try:
        import SilverCity
        _SC_stylesheet_location = SilverCity.get_default_stylesheet_location()
        SC_stylesheet = open(_SC_stylesheet_location).read()
    except:
        SC_XML = None
except ImportError:
    SC_XML = None

from Constants import *
import CTFiles
from diff import diff

#-----------------------------------------------------------------------------


def sgmlDiff(a, b):
    out = []
    isjunk = lambda x: not not re.search("\s", x)
    d = difflib.SequenceMatcher(isjunk, a, b)
    for e in d.get_opcodes():
        if e[0] == "replace":
            out.append('<del class="diff modified">'+''.join(a[e[1]:e[2]]) + '</del><ins class="diff modified">'+''.join(b[e[3]:e[4]])+"</ins>")
        elif e[0] == "delete":
            out.append('<del class="diff">'+ ''.join(a[e[1]:e[2]]) + "</del>")
        elif e[0] == "insert":
            out.append('<ins class="diff">'+''.join(b[e[3]:e[4]]) + "</ins>")
        elif e[0] == "equal":
            out.append(''.join(b[e[3]:e[4]]))
        else: 
            raise "OpcodesError", "Unrecognized %r"%e[0]

    return "".join(out)

#-----------------------------------------------------------------------------

class CheckoutableTemplatesBase(Base):
    """ the purpose of this class is to
    use the XML config file to extract which templates that can be
    checked out in this instance.
    """

    _secInfo= ClassSecurityInfo()
    _secInfo.declarePublic('__getitem__','__len__','tpValues', 'tpId',
                            'getCTFiles')
    _secInfo.declarePrivate('View management screens','doCheckout',
                            'doWriteback','canWriteback', 'doRetract'
                            'showCheckoutableTemplates',
                            'hasCheckedout',
                            'hasFileitemFromIdentifier',
                            'getFileitemFromIdentifier',
                            )
    def __init__(self):
        """ no doc string """
        pass
    
    def getCTFiles(self, zope, filter=None):
        """ returns which templates are checkoutable.
        The 'filter' parameter can be used to:
            - None: no filtering
            - 'Deployed': those that have been deployed
            - 'Deployed here': like 'Deployed' but only 'here'.
            - 'Undeployed': those not yet deployed.
            - 'Undeployed here': like 'Undeployed' but only 'here'.
        """

        fileitems = []
        # read config file

        fileitems, finder = CTFiles._readAllConfigs()
        
        fileitems = self._appendMoreInfo2Items(fileitems)

        if zope is None:
            return fileitems
        
        if filter is not None:
            filter = filter.lower().replace(' ','').strip()
        
        checked = []
        if filter == 'deployed':
            # only those where objectid exists as zope object
            for fileitem in fileitems:
                if hasattr(zope, fileitem['objectid']):
                    checked.append(fileitem)
        elif filter == 'deployedhere':
            # only those where objectid exists here without
            # acquisition.
            base = getattr(zope, 'aq_base', zope)
            for fileitem in fileitems:
                if hasattr(base, fileitem['objectid']):
                    checked.append(fileitem)
        elif filter == 'undeployed':
            # only those where objectid does not exists 
            # as zope object.
            for fileitem in fileitems:
                if not hasattr(zope, fileitem['objectid']):
                    checked.append(fileitem)
        elif filter == 'undeployedhere':
            # only those where objectid does not exists 
            # here without acquisition.
            base = getattr(zope, 'aq_base', zope)
            for fileitem in fileitems:
                if not hasattr(base, fileitem['objectid']):
                    checked.append(fileitem)            
        else:
            checked = fileitems
            
        base = getattr(zope, 'aq_base', zope)
        # Inspect if 'base' has a this_package_home attribute,
        # and if so, filter 'checked' based on that.
        
        
        if hasattr(base, 'this_package_home'):
            req_basepath = base.this_package_home

            # Make note that we do this:
            zope.REQUEST.set('DebugFilterCTFilesPH',
                             req_basepath)
            doublechecked = []
            for item in checked:
                if item['basepath'].find(req_basepath) > -1:
                    doublechecked.append(item)
            checked = doublechecked
        

        return checked

    def _appendMoreInfo2Items(self, fileitems):
        " using the data we have create few more interesting things "
        newfileitems = []
        for fileitem in fileitems:
            newd = fileitem
            ikey = 'filetypeicon'
            if fileitem['filetype'].lower()=='dtml':
                
                newd[ikey] = '''<img src="/misc_/OFSP/dtmlmethod.gif"
                                    alt="DTML Method" border="0" />'''
                extension = '.dtml'
            elif fileitem['filetype'].lower()=='zpt':
                newd[ikey] = '''<img src="/misc_/PageTemplates/zpt.gif"
                                    alt="Page Template" border="0" />'''
                extension = '.zpt'
            else:
                # Unrecognized!!
                continue

            basepath = fileitem['basepath']
            basepath = basepath.replace('\\',os.sep).replace('/',os.sep)
            relpath = fileitem['relpath']
            relpath = relpath.replace('\\',os.sep).replace('/',os.sep)
            if not os.path.splitext(relpath)[1]:
                relpath = relpath + extension
            fullpath = os.path.join(basepath, relpath)
            newd['fullpath'] = fullpath

            
            relpath = fileitem['relpath']
            sep = relpath[max(relpath.rfind('\\'), relpath.rfind('/'))]

            objectidlist = [str(x) for x in  relpath.split(sep)]
            if len(objectidlist) == 1:
                objectid = objectidlist[0]
            else:
                objectid = '.'.join(objectidlist[1:])
                
            if os.path.splitext(objectid)[1] not in ('.dtml','.zpt'):
                objectid += extension
            newd['objectid'] = objectid

            # keep it
            newfileitems.append(newd)
        return newfileitems

    def hasCheckedout(self, zope, identifiers):
        """ return true if any identifier is already checked out """
        if type(identifiers)==type('s'):
            identifiers = [identifiers]
        base = getattr(zope, 'aq_base', zope)
        
        for identifier in identifiers:
            fileitem = self.getFileitemFromIdentifier(identifier)
            if hasattr(base, fileitem['objectid']):
                return 1
        return 0            
            
    def doCheckout(self, zope, identifiers):
        """ create template objects """
        objects_created=[]
        if type(identifiers)==type('s'):
            identifiers = [identifiers]
        
        for identifier in identifiers:
            fileitem = self.getFileitemFromIdentifier(identifier)
            id = fileitem['objectid']
            fr = open(fileitem['fullpath'], 'r')
            code = fr.read()
            fr.close()
            title = ''
            if fileitem['filetype'].lower()=='dtml':
                obj=self._createDTMLMethod(zope, id, code, title)
                objects_created.append(obj)
            elif fileitem['filetype'].lower()=='zpt':
                obj=self._createPageTemplate(zope, id, code, title)
                objects_created.append(obj)
            else:
                raise "UnrecognizedFiletype", fileitem['filetype']
            
        return objects_created
            
    def _createDTMLMethod(self, zope, id, code, title=''):
        """ create a DTML object in zope """
        with = zope.manage_addProduct['OFSP']
        with.addDTMLMethod(id, title)
        dtmlmethod = getattr(zope, id)
        dtmlmethod.manage_edit(code, title)
        return dtmlmethod
    
    def _createPageTemplate(self, zope, id, code, title=''):
        """ create a PageTemplate object in zope """
        with = zope.manage_addProduct['PageTemplates']
        with.manage_addPageTemplate(id, title, code)
        pagetemplate = getattr(zope, id)
        return pagetemplate
    
    def doRetract(self, zope, identifiers):
        """ delete some zope objects """
        if type(identifiers)==type('s'):
            identifiers = [identifiers]
        objectids= []
        for fileitem in self.getCTFiles(zope, 'deployed'):
            if fileitem['identifier'] in identifiers:
                objectids.append(fileitem['objectid'])
        objectids_copy = objectids[:]
        zope.manage_delObjects(objectids)
        return objectids_copy
        
                           
    def getSourcecode(self, identifier):
        " read file and return source code "
        fullpath = self.getFullpathFromIdentifier(identifier)
        if fullpath is None:
            return "NONE FOUND!!"
        fr = open(fullpath, 'r')
        code = fr.read()
        fr.close()
        return code


    def showSourcecode(self, identifier):
        """ return source code htmlified """
        code = self.getSourcecode(identifier)
        return self._niceSourceFormat(code)

    def _niceSourceFormat(self, code):
        if SC_XML is not None:
            generator = SC_XML.XMLHTMLGenerator()
            file = StringIO.StringIO()
            generator.generate_html(file, code)
            code = file.getvalue()
            file.close()
            del generator
            css = '<style type="text/css">%s</style>\n\n'%SC_stylesheet
            code = '<div class="code_default">%s</div>'%code
            return css + code
        
        else:
            code = html_quote(code)
            code = newline_to_br(code)
            code = code.replace('\t','&nbsp;'*4)
            return "<code>%s</code>"%code

        
    def showDifference(self, zope, identifier, objectid):
        """ return a nice formatted difference string """
        code_source = self.getSourcecode(identifier)
        object = getattr(zope, objectid)
        assert hasattr(object, 'absolute_url'), "%r not a ZODB object" % object
        code_object = object.document_src()
        #difference = diff(html_quote(code_source), html_quote(code_object))
        difference = diff(code_object, code_source)
        return difference # this is a HTML <table>
    
    def _niceDifference(self, difference):
        """ return a nice explaination of the difference """
        #difference = newline_to_br(difference)
        lines = difference.splitlines(1)
        lineitemer = lambda x, c: "%s&nbsp; %s"%(c, x)
        newlines = []
        for i in range(len(lines)):
            newlines.append(lines[i])

        difference = "<br />".join(newlines)
        difference = difference.replace("\t", "&nbsp;"*4)
        return '<div class="code_default">%s</div>'%difference



    def hasFileitemFromIdentifier(self, identifiers):
        """ search to see if this identifier exists """
        if type(identifiers)==type('s'):
            identifiers = [identifiers]
        for fileitem in self.getCTFiles(None):
            if fileitem['identifier'] in identifiers:
                return 1
        return 0
    
    def getFileitemFromIdentifier(self, identifier):
        """ search through all files and match identifier, 
        then return fileitem (dict) of the found one.
        """
        for fileitem in self.getCTFiles(None):
            if fileitem['identifier'] == identifier:
                return fileitem
        else:
            return None
        
    def getFullpathFromIdentifier(self, identifier):
        """ get the full path from an identifier """
        found = self.getFileitemFromIdentifier(identifier)
        if found is not None:
            fullpath = found['fullpath']
            if found['filetype'] == 'DTML' and os.path.splitext(fullpath)[1] != '.dtml':
                fullpath += '.dtml'
            elif found['filetype'] == 'ZPT' and os.path.splitext(fullpath)[1] not in ('.zpt','.pt'):
                fullpath += '.zpt'
            
            return fullpath
        else:
            return None
                

    def doWriteback(self, zope, identifiers, makebackupcopy=1):
        """ From the identifier, find the equivalent Zope object
        and use it's document_src to write to file """
        objects =[] # list of all object we manage to write back
        for identifier in identifiers:
            fileitem = self.getFileitemFromIdentifier(identifier)
            if fileitem is None:
                raise "InvalidIdentifier", "No file in config found with"\
                      "this identifier %s"%identifier
            else:
                fullpath = fileitem['fullpath']
                objectid = fileitem['objectid']

                # get it as Zope object
                object = getattr(zope, objectid)
                document_src = object.document_src()

                if makebackupcopy:
                    incr = 1
                    while os.path.isfile(fullpath + '.bak%s'%incr):
                        incr += 1
                    fullpath_backup = fullpath + '.bak%s'%incr

                    fbr = open(fullpath, 'r')
                    fbw = open(fullpath_backup, 'w')
                    fbw.write(fbr.read())
                    fbw.close()
                    fbr.close()

                # nice and simple write
                fw = open(fullpath, 'w')
                fw.write(document_src)
                fw.close()

                # remember that we wrote this back
                objects.append([object, identifier])
                
        return objects

    def canWriteback(self):
        """ true if CAN_WRITEBACK  """
        return CAN_WRITEBACK
            

CheckoutableTemplatesBase._secInfo.apply(CheckoutableTemplatesBase)
