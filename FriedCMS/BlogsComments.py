# -*- coding: iso-8859-1 -*-

##
## Blogs
## (c) Fry-IT, www.fry-it.com
## Lukasz Lakomy <lukasz@fry-it.com>
##

## python
import os, sys, imp
from datetime import datetime
from time import time, sleep
# This is required to run this tests alone
# Current path is appended to available modules
syspath = sys.path[0].replace('\\','/')
path = syspath.split("/")
zopepath = "/".join(path[:-1])
for mod in ('FriedZopeBase','FriedCMS'):
    if "Products.%s"%mod not in sys.modules.keys():
        imp.load_module("Products.%s"%mod, None, "%s/%s"%(zopepath,mod), ('','',5))   
    
## Zope       
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

try:
    from persistent.list import PersistentList
    from persistent.mapping import PersistentMapping
except ImportError:
    # old Zope
    def PersistentList():
        return []
    def PersistentMapping():
        return {}
## Our friend...
from Products.FriedZopeBase.TemplateAdder import addTemplates2Class
from Products.FriedZopeBase.Utils import unicodify

from Constants import MANAGE_CONTENT_PERMISSIONS, VMS

#-----------------------------------------------------------------------------
class CommentsStorage(SimpleItem):
    """
    Class which stores and manipulates comments. They can be
    added/deleted. Comments can have subcomments.
    """
    security = ClassSecurityInfo()
    _properties=({'id':'comments_available', 'type':'boolean', 'mode':'rw', 'label':'Enable comments for this object'},
                 {'id':'auto_approve', 'type':'boolean', 'mode':'rw','label':'Auto approve new comments'},
                 {'id':'email_notify', 'type':'boolean', 'mode':'rw','label':'Notify by email after each comment'},
                )
    comments_available = True
    auto_approve = True
    email_notify = True
    manage_options = ({'label':'Comments', 'action':'tabComments'},)
    
    def __init__(self):
        self._comments = PersistentList()
        
    security.declarePrivate('addComment')
    def addComment(self,title,body,path='',email='',website='',id=None):
        """
        Add new comment. Id parameter is used in tests, in applicaton
        it should be left to generate automatically. Comment structure:
         - date - creation date
         - id - unigue id
         - path - strig build with ids separated by '/' from root to this comment
         - visible - boolean flag
         - title - comment title
         - body - text of the comment
         - email - optional email address
         - website - optional website
         - comments - list of subcomments with the same structure as this
        """
        
        if self.isCommentingAvailable():
            comment = PersistentMapping()
            comment['date'] = datetime.now()
            if not id:
                comment['id'] = str(time())
            else:
                comment['id'] = id
            if path:
                comment['path'] = "%s/%s"%(path,comment['id'])
            else:
                comment['path'] = "%s"%(comment['id'])  
            comment['visible'] = False
            comment['title'] = unicodify(title)
            comment['body'] = unicodify(body)
            comment['email'] = email
            comment['website'] = website
            comment['comments'] = PersistentList()
            
            if not path:
                self._comments.append(comment)
            else:
                comments = self._getCommentsList(path)
                comments.append(comment)
            if self.auto_approve:
                self.approveComment(comment['path']) 
            self._sendNotificationEmailToWebmaster(comment)
            return comment['path']
        else:
            return False
           
    def _getCommentsList(self,path):
        """
        Return correct part of the structure where comment
        should be added. If path is empty return main list
        otherwise search for 
        """
        if not path:
            return self._comments
        else:
            parts = path.split("/")
            comments = self._comments
            for part in parts:
                for comment in comments:
                    if comment['id'] == part:
                        comments = comment['comments']
                        break
            return comments
        
    security.declarePrivate('getComment')
    def getComment(self,path):
        """
        Get comment for given path. If not found return None
        """
        parts = path.split("/")
        comments = self._comments
        result = None
        for part_index in range(len(parts)):
            for comment in comments:
                if comment['id'] == parts[part_index]:
                    if (part_index + 1) == len(parts): #end of path
                        result = comment
                        return result
                    else:
                        comments = comment['comments']
                        break
        return result
        
    security.declarePrivate('deleteComment')
    def deleteComment(self,path):
        """
        Delete comment and its subcomments.
        Return true if found and deleted, False - otherwise.
        """
        parts = path.split("/")
        parent_path = "/".join(parts[:-1])
        id = parts[-1]
        comments = self._getCommentsList(parent_path)
        for i in range(len(comments)):
            if comments[i]['id'] == id:
                self._sendDeleteEmailToAuthor(comments[i])
                del comments[i]                
                return True
        return False
        
    security.declarePrivate('approveComment')
    def approveComment(self,path):
        """
        Change visible key to True, which acts as approval
        in a simple workflow 
        """
        comment = self.getComment(path)
        if comment:
            comment['visible'] = True
            #send email to webmaster and parent comment author
            self._sendNotificationEmailToParent(comment)
            self._sendNotificationEmailToAuthor(comment)
            return True
        else:
            return False
        
    security.declarePrivate('rejectComment')
    def rejectComment(self,path):
        """
        Change visible key to False, which acts as reject
        in a simple workflow 
        """
        comment = self.getComment(path)
        if comment:
            comment['visible'] = False
            self._sendRejectEmailToAuthor(comment)
            return True
        else:
            return False
        
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'isCommentingAvailable')
    def isCommentingAvailable(self):
        """
        Check if we can add coemmnts to object
        """
        return self.comments_available
        
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'getFlatComments')
    def getFlatComments(self, path='', visible_only=False):
        """
        To use in templates when we cannot do recursion. It
        returns flat list of comments and intendation level.
        Arguments:
         - 'path' - We can also show all coments or part, started with path
         - 'visible_only' - if set only comments that have visible=True
           will be returned, if parend is hidden and its child are visible
           they wont be shown
        """
        def _getCommentsFromBranch(branch,level,result):
            for comment in branch:
                new_comment = {}
                new_comment.update(comment)
                del new_comment['comments']
                new_comment['level'] = level
                if visible_only and not new_comment['visible']:
                    pass
                else:
                    result.append(new_comment)
                    if len(comment['comments']):
                        _getCommentsFromBranch(comment['comments'],level+1,result)
                    
        result = []
        visible_only = bool(int(visible_only))
        if not hasattr(self,'_comments'):
            self._comments = PersistentList()
        if path:
            comments = self.getComment(path)['comments']
            level = len(path.split("/"))
        else:
            comments = self._comments
            level = 0
        _getCommentsFromBranch(comments,level,result)
        return result
        
    def _sendNotificationEmailToWebmaster(self, comment):
        """
        Send email to webmaster 
        """
        if hasattr(self,'_unittests'): # this is trick to avoid sending in testing
            return True
        if not self.email_notify:
            return True
        homesite = self.getRoot()
        webmaster_email = homesite.getWebmasterEmail()
        msg = self.mail_newCommentToWebmaster(url = "%s/editCommentsForm"%(self.absolute_url()),
                                              title = comment['title'])
        if webmaster_email:
            self.sendEmail(str(msg), fr=webmaster_email, to=webmaster_email,
                           subject='New comment added')
        return True

    def _sendNotificationEmailToParent(self, comment):
        """
        Send email to author of the parent comment
        """
        if hasattr(self,'_unittests'): # this is trick to avoid sending in testing
            return True
        if not self.email_notify:
            return True
        homesite = self.getRoot()
        webmaster_email = homesite.getWebmasterEmail()
        #check if this is a subcomment, and get parent email
        parts = comment['path'].split("/")
        if len(parts)>=2:
            parent_path = "/".join(parts[:-1])
            parent_comment = self.getComment(parent_path)
            parent_email = parent_comment['email']
            msg = self.mail_newCommentToParent(url = self.absolute_url(),
                                               parent_title = parent_comment['title'],
                                               title = comment['title'])
            if parent_email:
                self.sendEmail(str(msg), fr=webmaster_email, to=parent_email,
                               subject='New response added')
        return True

    def _sendRejectEmailToAuthor(self, comment):
        """
        Send email to author of comment that it was rejected
        """
        if hasattr(self,'_unittests'): # this is trick to avoid sending in testing
            return True
        if not self.email_notify:
            return True
        homesite = self.getRoot()
        webmaster_email = homesite.getWebmasterEmail()
        msg = self.mail_rejectCommentToAuthor(url = self.absolute_url(),
                                              title = comment['title'])
        if comment['email']:
            self.sendEmail(str(msg), fr=webmaster_email, to=comment['email'],
                           subject='Comment rejected')
        return True
    
    def _sendNotificationEmailToAuthor(self, comment):
        """
        Send email to author of comment that it was approved
        """
        if hasattr(self,'_unittests'): # this is trick to avoid sending in testing
            return True
        if not self.email_notify:
            return True
        homesite = self.getRoot()
        webmaster_email = homesite.getWebmasterEmail()
        msg = self.mail_approveCommentToAuthor(url = self.absolute_url(),
                                              title = comment['title'])
        if comment['email']:
            self.sendEmail(str(msg), fr=webmaster_email, to=comment['email'],
                           subject='Comment approved')
        return True
    
    def _sendDeleteEmailToAuthor(self, comment):
        """
        Send email to author of comment that it was deleted
        """
        if hasattr(self,'_unittests'): # this is trick to avoid sending in testing
            return True
        if not self.email_notify:
            return True
        homesite = self.getRoot()
        webmaster_email = homesite.getWebmasterEmail()
        msg = self.mail_deleteCommentToAuthor(url = self.absolute_url(),
                                              title = comment['title'])
        if comment['email']:
            self.sendEmail(str(msg), fr=webmaster_email, to=comment['email'],
                           subject='Comment deleted')
        return True
    
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'manage_addComment')
    def manage_addComment(self,title,body,comment_path='',email='',website='', 
                          ZMI=False, REQUEST=None):
        """
        """
        if not title:
            msg = 'Title is mandatory.'
        elif not body:
            msg = 'Text is mandatory.'
        elif email and not self.ValidEmailAddress(email):
            msg = 'Wrong email format.'
        else:
            if not hasattr(self,'_comments'):
                self._comments = PersistentList()
            status = self.addComment(title, body, path = comment_path, email = email, website = website)
            if status:
                msg = 'Comment added.'
            else:
                msg = 'Comment not added because comments are disabled.'
        if REQUEST:
            if ZMI:
                return self.tabComments(self,REQUEST,manage_tabs_message=msg)
            else:
                REQUEST['msg'] = msg
                return self.editCommentsForm(self,REQUEST)
        else:
            return msg
      
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'manage_getComment')
    def manage_getComment(self,comment_path):
        """
        Used in templates to getComment because we have to transform 
        PersistentMapping to dictionary
        """
        comment = self.getComment(comment_path)
        result = {}
        result.update(comment)
        return result
    
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'manage_deleteComment')
    def manage_deleteComment(self, delete_path, ZMI=False, REQUEST=None):
        """
        Used in templates to getComment because we have to transform 
        PersistentMapping to dictionary
        """
        result = self.deleteComment(delete_path)
        if result:
            msg = 'Comment deleted.'
        else:
            msg = 'Comment not deleted.'
        if REQUEST:
            if ZMI:
                return self.tabComments(self, REQUEST, manage_tabs_message=msg)
            else:
                REQUEST['msg'] = msg
                return self.editCommentsForm(self,REQUEST)
        else:
            return msg
            
    security.declareProtected(MANAGE_CONTENT_PERMISSIONS,'manage_changeVisibility')
    def manage_changeVisibility(self, change_path, visible, ZMI=False, REQUEST=None):
        """
        Method used in forms to change visibility
        """
        comment = self.getComment(change_path)
        ZMI = bool(int(ZMI))
        visible = bool(int(visible))
        if visible:
            self.approveComment(change_path)
            msg = 'Comment visible.'
        else:
            self.rejectComment(change_path)
            msg = 'Comment hidden.'
        if REQUEST:
            if ZMI:
                return self.tabComments(self,REQUEST,manage_tabs_message=msg)
            else:
                REQUEST['msg'] = msg
                return self.editCommentsForm(self,REQUEST)
        else:
            return msg
    
templates = ('zpt/tabComments',
             'zpt/editCommentsForm',
             'zpt/mail_newCommentToWebmaster',
             'zpt/mail_newCommentToParent',
             'zpt/mail_rejectCommentToAuthor',
             'zpt/mail_deleteCommentToAuthor',
             'zpt/mail_approveCommentToAuthor',
            )
addTemplates2Class(CommentsStorage, templates, globals_=globals())

security = ClassSecurityInfo()
security.declareProtected(VMS, 'tabComments')
security.declareProtected(MANAGE_CONTENT_PERMISSIONS, 'editCommentsForm')
security.declarePrivate('mail_newCommentToWebmaster')
security.declarePrivate('mail_newCommentToParent')
security.declarePrivate('mail_rejectCommentToAuthor')
security.declarePrivate('mail_deleteCommentToAuthor')
security.declarePrivate('mail_approveCommentToAuthor')
security.apply(CommentsStorage)


import unittest
import sys
class CommentsStorageTests(unittest.TestCase):
    """
    Test class for CommentsStorage class 
    """   
    
    def test_addComment1(self):
        """
        Add one comment
        """
        comments = CommentsStorage()
        comments.addComment('title1','body1',
                           path='',email='lukasz@fry-it.com')
        self.assertEqual(len(comments._comments),1)
        comment = comments._comments[0]
        self.assertEqual(comment['path'],comment['id'])
        self.assertEqual(comment['title'],'title1')
        self.assertEqual(comment['body'],'body1')
        self.assertEqual(comment['email'],'lukasz@fry-it.com')
        
    def test_addComment2(self):
        """
        Add many comments to root
        """
        comments = CommentsStorage()
        self.assertEqual(len(comments._comments),0)
        comments.addComment('title1','body1',path='',email='lukasz@fry-it.com')
        comments.addComment('title2','body2',path='',email='lukasz@fry-it.com')
        comments.addComment('title3','body3',path='',email='lukasz@fry-it.com')
        #for c in comments._comments: print c
        self.assertEqual(len(comments._comments),3)
        self.assertEqual(comments._comments[0]['title'],'title1')
        self.assertEqual(comments._comments[1]['title'],'title2')
        self.assertEqual(comments._comments[2]['title'],'title3')
        
    def test_addComment3(self):
        """
        Try add comment when you cant
        """
        comments = CommentsStorage()
        status = comments.addComment('title1','body1',path='',email='lukasz@fry-it.com')
        self.assertNotEqual(status,False)
        self.assertEqual(len(comments._comments),1)        
        
        comments.comments_available = False
        status = comments.addComment('title2','body2',path='',email='lukasz@fry-it.com')
        self.assertEqual(status,False)
        self.assertEqual(len(comments._comments),1)        
        
    def buildStructure(self):
        """
        Create a structure of comments:
          |
          +-comment1
          | |
          | +-comment11
          | |
          | +-comment12 
          | |  |
          | |  +- comment121
          | |
          | +-comment13
          |
          +-comment2
        This also checks _goToPath. Changing paths and ids for
        easier testing
        """
        comments = CommentsStorage()
        path1 = comments.addComment('comment1', '' , path='', id='comment1')
        comments.addComment('comment2','',path='', id='comment2')
        comments.addComment('comment11','',path=path1, id='comment11')
        path12 = comments.addComment('comment12', '', path=path1, id='comment12')
        comments.addComment('comment13', '', path=path1, id='comment13')
        comments.addComment('comment121', '', path=path12, id='comment121')
        return comments
    
    def test_addComment5(self):
        """
        Add comment when auto approve is on and off
        """
        comments = CommentsStorage()
        comments.auto_approve = True
        status = comments.addComment('title1','body1',path='')
        self.assertEqual(comments._comments[0]['visible'],True)
        
        comments.auto_approve = False
        status = comments.addComment('title2','body1',path='')
        self.assertEqual(comments._comments[0]['visible'],True)
        self.assertEqual(comments._comments[1]['visible'],False)
        
    def test_addComment4(self):
        """
        Test advanced structure
        """
        comments = self.buildStructure()
        self.assertEqual(len(comments._comments),2)
        self.assertEqual(len(comments._comments[0]['comments']),3)
        self.assertEqual(len(comments._comments[0]['comments'][1]['comments']),1)
        
        self.assertEqual(comments._comments[0]['title'],'comment1')
        self.assertEqual(comments._comments[1]['title'],'comment2')
        self.assertEqual(comments._comments[0]['comments'][0]['title'],'comment11')
        self.assertEqual(comments._comments[0]['comments'][1]['title'],'comment12')
        self.assertEqual(comments._comments[0]['comments'][2]['title'],'comment13')
        self.assertEqual(comments._comments[0]['comments'][1]['comments'][0]['title'],'comment121')

    def test_deleteComment1(self):
        """
        Delete comments in root
        """
        comments = CommentsStorage()
        path = comments.addComment('title1','body1',path='',email='lukasz@fry-it.com')
        self.assertEqual(len(comments._comments),1)
        comments.deleteComment(path)
        self.assertEqual(len(comments._comments),0)
        
    def test_deleteComment2(self):
        """
        Delete comments in root
        """
        comments = CommentsStorage()        
        path1 = comments.addComment('title1','body1',path='')
        sleep(0.001)
        path2 = comments.addComment('title2','body1',path='')
        sleep(0.001)
        path3 = comments.addComment('title3','body1',path='')
        
        comments.deleteComment(path2)
        self.assertEqual(len(comments._comments),2)
        self.assertEqual(comments._comments[0]['title'],'title1')
        self.assertEqual(comments._comments[1]['title'],'title3')
        comments.deleteComment(path1)
        self.assertEqual(len(comments._comments),1)
        self.assertEqual(comments._comments[0]['title'],'title3')
        comments.deleteComment(path3)
        self.assertEqual(len(comments._comments),0)
        
    def test_deleteComment3(self):
        """
        Delete non existent
        """
        comments = CommentsStorage()        
        path1 = comments.addComment('title1','body1',path='')
        status = comments.deleteComment(path1)
        self.assertEqual(status,True)
        status = comments.deleteComment(path1)
        self.assertEqual(status,False)
        
    def test_deleteComment4(self):
        """
        Test deleting in advanced structure
        """
        comments = self.buildStructure()
        comments.deleteComment('comment2')
        self.assertEqual(len(comments._comments),1)
        comments.deleteComment('comment1/comment13')
        self.assertEqual(len(comments._comments[0]['comments']),2)
        comments.deleteComment('comment1/comment12/comment121')
        self.assertEqual(len(comments._comments[0]['comments'][1]['comments']),0)
        comments.deleteComment('comment1')
        self.assertEqual(len(comments._comments),0)
        
    def test_getComment(self):
        """
        Test getting in advanced structure
        """
        comments = self.buildStructure()
        comment = comments.getComment('comment2')
        self.assertEqual(comment['title'],'comment2')
        comment = comments.getComment('comment1/comment13')
        self.assertEqual(comment['title'],'comment13')
        comment = comments.getComment('comment1/comment12/comment121')
        self.assertEqual(comment['title'],'comment121')
        comment = comments.getComment('comment1')
        self.assertEqual(comment['title'],'comment1')
        comment = comments.getComment('')
        self.assertEqual(comment,None)
        
    def test_approveComment(self):
        """
        Approve existing and not existing comment
        """
        comments = CommentsStorage()        
        path = comments.addComment('title1','body1',path='')
        status = comments.approveComment(path)
        self.assertEqual(status,True)
        self.assertEqual(comments._comments[0]['visible'],True)
        
        status = comments.approveComment('someid')
        self.assertEqual(status,False)
    
    def test_rejectComment(self):
        """
        Reject existing and not existing comment
        """
        comments = CommentsStorage()        
        path = comments.addComment('title1','body1',path='')
        status = comments.rejectComment(path)
        self.assertEqual(status,True)
        self.assertEqual(comments._comments[0]['visible'],False)
        
        status = comments.rejectComment('someid')
        self.assertEqual(status,False)
        
    def test_getFlatComments(self):
        """
        Test getting flat version of advanced structure
        """
        comments = self.buildStructure()
        result = comments.getFlatComments()
        self.assertEqual(len(result),6)
        self.assertEqual(result[0].has_key('level'),True)
        self.assertEqual(result[0].has_key('comments'),False)
        self.assertEqual(result[0]['title'],'comment1')
        self.assertEqual(result[0]['level'],0)
        self.assertEqual(result[1]['title'],'comment11')
        self.assertEqual(result[1]['level'],1)
        self.assertEqual(result[2]['title'],'comment12')
        self.assertEqual(result[2]['level'],1)
        self.assertEqual(result[3]['title'],'comment121')
        self.assertEqual(result[3]['level'],2)
     
    def test_getFlatComments2(self):
        """
        Test getting flat version of advanced structure
        with advanced visibility filtering
        """
        comments = self.buildStructure()
        comments.rejectComment('comment1/comment11')
        comments.rejectComment('comment1/comment12')
        comments.rejectComment('comment2')
        result = comments.getFlatComments(visible_only=False)
        self.assertEqual(len(result),6)
        result = comments.getFlatComments(visible_only=True)
        self.assertEqual(len(result),2)
        self.assertEqual(result[0]['title'],'comment1')
        self.assertEqual(result[1]['title'],'comment13')

if __name__ == '__main__':
    
    CommentsStorage._unittests = 1
    def test_suite():
        """
        Build test suite
        """  
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        return suite

    def main():
        """
        Run tests
        """  
        unittest.TextTestRunner().run( test_suite() )
    
    main()    