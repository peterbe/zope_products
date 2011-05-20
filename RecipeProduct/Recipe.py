# -*- coding: iso-8859-1 -*
# AttendanceProduct
#
# Peter Bengtsson <mail@peterbe.com>
# License: ZPL
#

__doc__=""""""
__version__='0.0.2'

# python
import string
from time import time

# Zope
from Globals import Persistent, InitializeClass, package_home #, DTMLFile
from Products.PythonScripts.standard import html_quote, url_quote_plus
from Products.PythonScripts.PythonScript import PythonScript
from OFS import SimpleItem, ObjectManager, Folder
from App.Common import rfc1123_date
from DocumentTemplate import sequence
from AccessControl import ClassSecurityInfo
from Products.ZCatalog.CatalogAwareness import CatalogAware
from zLOG import LOG, ERROR, INFO, PROBLEM, WARNING
from DateTime import DateTime
#from Products.Localizer import LocalDTMLFile, Gettext
from Globals import DTMLFile as LocalDTMLFile
#from Products.Localizer import Localizer

#_ = Gettext.translation(globals())
def _(*a, **kw):
    return a[0]
#N_ = Gettext.dummy
N_ = _


# Product
from RecipeConstants import *
import RecipeUtils


#### RECIPECOLLECTION ##################################

manage_addRecipeCollectionForm = LocalDTMLFile('dtml/addRecipeCollectionForm',
                                               globals())

def manage_addRecipeCollection(dispatcher, id, title='',
                               REQUEST=None):
    """ create """
    
    dest = dispatcher.Destination()
    
    collection = RecipeCollection(id, title)
    dest._setObject(id, collection)
    collection = dest._getOb(id)
    collection.DeployStandards()
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
    
            
class RecipeCollection(Folder.Folder, Persistent):
    """ class """
    
    meta_type = RECIPECOLLECTION_METATYPE
    
    _properties=({'id':'title',    'type':'string',  'mode':'w'},
                 {'id':'mastername','type':'string', 'mode':'w'},
                 {'id':'masteremail','type':'string','mode':'w'},
                 {'id':'difficultylevels','type':'lines','mode':'w'},
                 {'id':'categoryoptions','type':'lines','mode':'w'},
                 {'id':'notifymaster','type':'boolean','mode':'w'},
                 {'id':'hometitle','type':'string','mode':'w'},
                 )
                 
    security=ClassSecurityInfo()
    
    def __init__(self, id, title, 
                 mastername='',masteremail='',
                 hometitle='Home'):
        """ init """
        self.id = str(id)
        self.title = str(title)
        self.mastername = mastername
        self.masteremail = masteremail
        self.difficultylevels = []
        self.categoryoptions = []
        self.hometitle = hometitle
        

    def getHometitle(self):
        """ return hometitle """
        return self.hometitle
    
    def doCache(self, hours=10):
        """ set cache headers on this request """
        if hours > 0:
            response = self.REQUEST.RESPONSE
            #now = DateTime()
            #then = now+float(hours/24.0)
            #response.setHeader('Expires', then.rfc822())
            response.setHeader('Expires', rfc1123_date(time() + 3600*hours))
            response.setHeader('Cache-Control', 'public,max-age=%d' % int(3600*hours))
    
    
    def getCategoryOptions(self, what=None, selectablesonly=0):
        """ if 'what' is "bundled" return dict with keys (name, checked, unchecked)
            if 'what' is "checked" return checked image tabs
            if 'what' is "unchecked" return unchecked image tabs
            else return just the string 
        """
        options = self.categoryoptions
        checked = []
        if what is None:
            what = ''
        for line in options:
            line = line.split(':')
            if what.lower() == 'checked':
                checked.append(line[1])
            elif what.lower() == 'unchecked':
                checked.append(line[2])
            elif what.lower() in ['bundled']:
                d = {'name':line[0], 'checked':line[1], 'unchecked':line[2]}
                checked.append(d)
            elif selectablesonly:
                if len(line)==3:
                    checked.append(line[0])
            else:
                checked.append(line[0])
        return checked
                
    
    def getRoot(self):
        """ return root object """
        mtype = RECIPECOLLECTION_METATYPE
        if self.meta_type == mtype:
            r = self
        elif self.aq_parent.meta_type == mtype:
            r = self.aq_parent
        elif self.aq_parent.aq_parent.meta_type == mtype:
            r = self.aq_parent.aq_parent
        elif self.aq_parent.aq_parent.aq_parent.meta_type == mtype:
            r = self.aq_parent.aq_parent.aq_parent
        else:
            r = None
        
        return r  
    
    def DeployStandards(self):
        """ create some basic folders """
        root = self.getRoot()
        for f in ['newsletters','newsletterreceivers']:
            if not hasattr(root, f):
                root.manage_addFolder(f)
                
    def assureProperties(self):
        """ make sure all objects have all properties """
        # collection
        if not hasattr(self, 'hometitle'):
            self.hometitle = ''
        # authors
        
        # recipes
        for recipe in self.getRecipes(sort=0,
                                      filterunready=0):
            recipe.assureProperties()
            
        return "done %s"%DateTime()
            
            
    def getNewsletterRoot(self):
        """ return where the newsletters are """
        return self.getRoot().newsletters
    
    def getNewsletterReceiversRoot(self):
        """ return where the newsletterreceivers are """
        return self.getRoot().newsletterreceivers
    
    def getNewsletterReceivers(self):
        """ return newsletterreceiver objects """
        root = self.getNewsletterReceiversRoot()
        return root.objectValues(NEWSLETTERRECEIVER_METATYPE)
    
    def getRecipes(self, sort=1, filterunready=1,
                   authorids=None, filtercategory=None,
                   firstonly=None):
        """ get all recipe objects """
        all=[]
        root = self.getRoot()
        all.extend(root.objectValues(RECIPE_METATYPE))
        for author in self.getAuthors():
            all.extend(author.objectValues(RECIPE_METATYPE))

        
        if filterunready:
            all = self._filterUnready(all)
        if authorids is not None:
            if type(authorids)==type('s'):
                authorids = [authorids]
            all = self._filterAuthors(all, authorids)
            
        if filtercategory is not None:
            all = self._filterByCategory(all, filtercategory)
            
        # sort em
        if sort:
            by = ('datum',)
            all = sequence.sort(all, (by,))
            all.reverse()
            
        if firstonly is not None:
            # shorten list
            all = all[:firstonly]
        return all

    def _filterByCategory(self, recipes, category):
        """ look through all recipes to see for matching category """
        checked = []
        for recipe in recipes:
            if category in recipe.getCategories():
                checked.append(recipe)
        return checked
    
    def _filterAuthors(self, recipies, authorids):
        """ filter out all where author is not in authorids """
        checked = []
        for recipe in recipies:
            if recipe.getAuthor(only='id') in authorids:
                checked.append(recipe)
        return checked
    
    def _filterUnready(self, recipies):
        """ forget those not ready """
        checked = []
        for recipe in recipies:
            if recipe.isReady():
                checked.append(recipe)
        return checked
    
    def getAuthors(self):
        """ return author objects """
        return self.getRoot().objectValues(RECIPEAUTHOR_METATYPE)
    
    def notifyMaster(self):
        """ shall we notify the master of things """
        return getattr(self, 'notifymaster', NOTIFYMASTER)
    
    def sendEmail(self, m, t, f, s):
        """ actually send an email """
        mailhost = self.MailHost
        br = '\r\n'
        body = br.join(["From: %s"%f,"To: %s"%t,
                        "Subject: %s"%s, "",m])
        mailhost.send(body, t, f, s)
    
    def createNewsletterReceiverWeb(self, email, subscribe,
                                    REQUEST):
        """ see whether to subscribe or to unsubscribe """
        if subscribe:
            # check that it does not already exist
            found = None
            for receiver in self.getNewsletterReceivers():
                if receiver.getEmail().lower() == email.lower().strip():
                    found = receiver
                    
            
                    #raise "AlreadySubscribing",\
                          #"You are already subscribing"

            if found is None:
                self.createNewsletterReceiver(email, REQUEST=REQUEST)
            else:
                found.Subscribe()
                if REQUEST is not None:
                    url = self.getRoot().absolute_url()
                    url = url + "?newsletterreceiver=added"
                    REQUEST.RESPONSE.redirect(url)

        else:
            self.unsubscribeNewsletterReceiver(email, 
                                               REQUEST=REQUEST)
                
    def createNewsletterReceiver(self, email,
                                 REQUEST=None):
        """ create newsletterreceiver object """
        response = self.REQUEST.RESPONSE
        email = email.strip()
        if not RecipeUtils.ValidEmailAddress(email):
            raise "InvalidEmail", "Email address not valid"

        if self.notifyMaster():
            t = self.masteremail
            f = "%s <%s>"%(self.mastername, self.masteremail)
            s = "New newsletterreceiver added"
            m = s + " with email %s"%email
            self.sendEmail(m, t, f, s)
            
        self._createNewsletterReceiver(email)
        # save in a cookie that you have registered
        then = DateTime()+300
        then = then.rfc822()
        response.setCookie('RecipeNewsletterReceiver',
                           email, path='/', expires=then)
        
        if REQUEST is not None:
            url = self.getRoot().absolute_url()
            url = url + "?newsletterreceiver=added"
            
            response.redirect(url)

    def unsubscribeNewsletterReceiver(self, email, REQUEST=None):
        """ find the newsletterreceiver object and unsubscribe """
        response = self.REQUEST.RESPONSE
        email = email.lower().strip()
        unsubscribers = []
        for receiver in self.getNewsletterReceivers():
            if receiver.getEmail().lower() == email:
                receiver.Unsubscribe()
                break
            
        # loose cookie
        then = DateTime()-2
        then = then.rfc822()
        response.setCookie('RecipeNewsletterReceiver',
                           '', path='/', expires=then)
        
        if REQUEST is not None:
            url = self.getRoot().absolute_url()
            url = url + "?newsletterreceiver=removed"
            
            response.redirect(url)            
    
    
        
    def _createNewsletterReceiver(self, email):
        
        """ actually create the object """
        id = RecipeUtils.safeId(email.strip().lower())
        destination = self.getNewsletterReceiversRoot()
        receiver = NewsletterReceiver(id, email)
        destination._setObject(id, receiver)
        receiver = destination._getOb(id)
        
        return receiver

    def showText(self, text):
        """ format plain text a bit """
        t = text
        
        t = t.replace('\n','<br>')
        t = '<span class="showtext">%s</span>'%t
        return t
    
    def getBreadcrumbs(self):
        """ return a list if hyperlinks/text """
        objects = []

        for each in self.REQUEST.PARENTS:
            objects.append(each)
            if each.meta_type == RECIPECOLLECTION_METATYPE:
                break
        
        links = []
        objects.reverse()
        for object in objects:
            if object == objects[-1]:
                representation = self._getBreadcrumbRep(object, 1)
            else:
                representation = self._getBreadcrumbRep(object)
            links.append(representation)
        return links

    def _getBreadcrumbRep(self, o, onlytext=0):
        """ depending on what object it is, display it
        differently """
        a = o.absolute_url()
        if o.meta_type == RECIPECOLLECTION_METATYPE:
            t = self.getHometitle()
        elif o.meta_type == RECIPEAUTHOR_METATYPE:
            t = o.getFirstname()
        elif o.meta_type == RECIPE_METATYPE:
            t = o.getTitle()
            if len(t)>45:
                t = t[:45]+'...'
        else:
            t = o.title_or_id()
            
        if onlytext:
            return t
        else:
            return '<a href="%s">%s</a>'%(a, t)
           
    
    file = 'dtml/show_breadcrumbs'
    show_breadcrumbs = LocalDTMLFile(file, globals())
    
    def getChefpointURL(self):
        """ return what URL the chefpoint should have """
        mtype = self.meta_type
        baseurl = self.absolute_url()
        if mtype == 'Recipe':
            return baseurl+'/EditRecipe'
        elif mtype == 'Recipe Author':
            return baseurl+'/AuthorAdmin'
        elif mtype == 'Recipe Collection':
            return '?changeAuthor=1#changeauthor'
        elif mtype == 'Recipe Author':
            return baseurl + '/addRecipeHelpForm'
        else:
            return baseurl
        
    file = 'dtml/newslettersubscriptionform'
    newslettersubscriptionform = LocalDTMLFile(file, globals())
    
    file = 'dtml/addRecipeHelpForm'
    security.declareProtected(VMS, 'addRecipeHelpForm')
    addRecipeHelpForm = LocalDTMLFile(file, globals())

    file = 'dtml/chefpoint'
    chefpoint = LocalDTMLFile(file, globals())
    
    file = 'dtml/recipe_menu'
    recipe_menu = LocalDTMLFile(file, globals())

    file = 'dtml/show_categories'
    show_categories = LocalDTMLFile(file, globals())
    
    ## Wrap scripts 
    
    def encodeEmailString(self, email, title=None):
        """ wrap script """
        script = RecipeUtils.encodeEmailString
        return script(email, title)


    def RSS091(self, batchsize=None, withheaders=1):
        """ return RSS XML """
        request = self.REQUEST
        root = self.getRoot()
        header="""<?xml version="1.0"?><rss version="0.91">
        <channel>
        <title>%s</title>
        <link>%s</link>
        <description>%s</description>
        <language>en-uk</language>
        <copyright></copyright>
        <webMaster>%s</webMaster>\n"""%\
           (root.title, root.absolute_url(), root.title,
            self.masteremail)
        logosrc = request.SERVER_URL
        logosrc += '/misc_/RecipeProduct/smalllogo.gif'
        header=header+"""<image>
        <title>%s</title>
        <url>%s</url>
        <link>%s</link>
        <width>%s</width>
        <height>%s</height>
        <description>%s</description>
        </image>\n"""%(root.title, logosrc,
                       root.absolute_url(),
                       87, 78,
                       root.title)
        # manually set sortorder
        request.set('sortorder','date')
        request.set('reverse',1)
        xml=''
        if batchsize is None:
            batchsize = 5
        for recipe in self.getRecipes()[:batchsize]:
            title = recipe.getTitle()
            title = self._prepare_feed(title)
            description = recipe.getComment()
            if description == '':
                description = recipe.getIngredients()
            description = self._prepare_feed(description)

            xml=xml+"""\n\t<item>
            <title>%s</title>
            <description>%s</description>
            <link>%s</link>
            """%(title, description, recipe.absolute_url())

            author = recipe.getAuthor(only='object')
            
            author = "%s %s (%s)"%(author.getFirstname(),
                                   author.getLastname(),
                                   author.getEmail())
            author = self._prepare_feed(author)
            xml="%s\n<author>%s</author>\n"%(xml, author)
            xml=xml+"\n\t</item>"
            
        footer="""</channel>\n</rss>"""
        if withheaders:
            xml = header+xml+footer
            
        response = request.RESPONSE
        response.setHeader('Content-Type', 'text/xml')
        return xml
    
    def _prepare_feed(self, s):
        """ prepare the text for XML usage """
        _replace = RecipeUtils.replace_special_chars
        s = html_quote(s)
        s = s.replace('£','&#163;')
        s = _replace(s, html_encoding=1)
        s = s.replace('&','&amp;')
        return s
    
    ## For Q and As
    
    def getAllAnswers(self, filterid=None):
        """ return all Cooking Answer objects and possibly filter """
        checked = []
        for author in self.getAuthors():
            for answer in author.getAnswers():
                if filterid is None or \
                   filterid is not None and filterid == answer.id:
                    checked.append(answer)
        return checked
    
    def getAllQuestions(self, filterid=None, sort=None):
        """ return all Cooking Questions """
        checked = []
        for author in self.getAuthors():
            for question in author.getQuestions():
                if filterid is None or \
                   filterid is not None and filterid == question.id:
                    checked.append(question)
        
        if sort:
            if sort == 1:
                sort = 'publishdate'
            by = (sort,)
            checked = sequence.sort(checked, (by,))
            checked.reverse()
            
        return checked
    
    def has_question(self, id):
        """ check if question object with this id exists """
        for question in self.getAllQuestions():
            if question.id == id:
                return true
        return false
    
    file = 'dtml/QandAs'
    QandAs = LocalDTMLFile(file, globals())
    
    standard_html_header = LocalDTMLFile('dtml/standard_html_header', globals())
    standard_html_footer = LocalDTMLFile('dtml/standard_html_footer', globals())
    
    print_html_header = LocalDTMLFile('dtml/print_html_header', globals())
    print_html_footer = LocalDTMLFile('dtml/print_html_footer', globals())
    
    stylesheet_css = LocalDTMLFile('dtml/stylesheet.css', globals())
    print_css = LocalDTMLFile('dtml/print.css', globals())
    
    

setattr(RecipeCollection, 'rss.xml', RecipeCollection.RSS091)
setattr(RecipeCollection, 'stylesheet.css', RecipeCollection.stylesheet_css)
setattr(RecipeCollection, 'print.css', RecipeCollection.print_css)

InitializeClass(RecipeCollection)
    

#### RECIPEAUTHOR ######################################

file = 'dtml/addRecipeAuthorForm'
manage_addRecipeAuthorForm = LocalDTMLFile(file, globals())

def manage_addRecipeAuthor(dispatcher, firstname, lastname, email,
                           REQUEST=None):
    """ create """
    
    dest = dispatcher.Destination()
    
    id = firstname.lower().capitalize()
    if hasattr(dispatcher, id):
        id += lastname[0].upper()
    id = RecipeUtils.safeId(id)
    
    author = RecipeAuthor(id, '', firstname, lastname, email)
    dest._setObject(id, author)
    author = dest._getOb(id)
    
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(REQUEST.URL1+'/manage_workspace')
        
        
class RecipeAuthor(Folder.Folder, Persistent, RecipeCollection,
                   CatalogAware):
    """ class """

    meta_type = RECIPEAUTHOR_METATYPE
    icon = '%s/author.gif'%ICON_LOCATION
    
    _properties=({'id':'title',    'type':'string', 'mode':'w'},
                 {'id':'firstname','type':'string', 'mode':'w'},
                 {'id':'lastname', 'type':'string', 'mode':'w'},
                 {'id':'email',    'type':'string', 'mode':'w'},
                 {'id':'authorcomment',  'type':'utext',  'mode':'w'},
                 )
    
    security=ClassSecurityInfo()
    
    def __init__(self, id, title, firstname, lastname, email,
                 authorcomment=''):
        """ init """
        self.id = id
        self.title = title
        self.firstname = firstname.strip()
        self.lastname = lastname.strip()
        if not RecipeUtils.ValidEmailAddress(email.strip()):
            raise "InvalidEmail", "The email %s is invalid"%email
        self.email = email.strip()
        self.authorcomment = authorcomment.strip()
        
    def manage_afterAdd(self, REQUEST, RESPONSE):
        """ create a acl_user if necessary """
        base= getattr(self, 'aq_base', self)
        if not hasattr(base, 'acl_users'):
            base.manage_addUserFolder()
            
    
    def getTitle(self):
        """ special title """
        if self.title != '':
            return self.title
        else:
            return "%s %s"%(self.firstname, self.lastname)
       
    def title_or_id(self):
        """ special title """
        if self.getTitle()=='':
            return self.getId()
        else:
            return self.getTitle()
       
    def getFirstname(self):
        """ return firstname """
        return self.firstname
    
    def getLastname(self):
        """ return lastname """
        return self.lastname
    
    def getEmail(self):
        """ return email """
        return self.email
    
    def getComment(self):
        """ return comment if existant """
        return getattr(self, 'authorcomment','')
    
    def getMugshot(self):
        """ requires that there is a particular 
        image available """
        t = self.getTitle()
        if hasattr(self, 'mugshot.gif'):
            return getattr(self, 'mugshot.gif').tag(alt=t)
        elif hasattr(self, 'mugshot.jpg'):
            return getattr(self, 'mugshot.jpg').tag(alt=t)
        elif hasattr(self, 'mugshot.png'):
            return getattr(self, 'mugshot.png').tag(alt=t)
        else:
            i = '<img src="/misc_/RecipeProduct/anonymous.gif" '
            i += 'width="80" height="67" alt="%s">'%t
            return i
        
    def getAuthorRecipes(self, sort=1):
        """ return recipes here """
        all = self.objectValues(RECIPE_METATYPE)
        
        if sort:
            by = ('datum',)
            all = sequence.sort(all, (by,))
            all.reverse()
            
        return all
        
    def getAnswers(self):
        """ return all answer objects """
        return self.objectValues(COOKINGANSWER_METATYPE)
    
    def getQuestions(self, sort=None):
        """ return all question objects """
        all = self.objectValues(COOKINGQUESTION_METATYPE)
        if sort:
            if sort == 1:
                sort = 'publishdate'
            by = (sort,)
            all = sequence.sort(all, (by,))
            all.reverse()
        return all
    
    security.declareProtected(VMS, 'editAuthor')
    def editAuthor(self, firstname=None, lastname=None,
                   email=None, authorcomment=None,
                   REQUEST=None):
        """ edit details of author """
        if firstname is not None:
            self.firstname = firstname.strip()
        if lastname is not None:
            self.lastname = lastname.strip()
        if email is not None:
           if RecipeUtils.ValidEmailAddress(email.strip()):
               self.email = email.strip()
           else:
               raise "InvalidEmail", "Email address not valid"
        if authorcomment is not None:
            self.authorcomment = authorcomment.strip()

        if REQUEST is not None:
            tm = "Author Saved"
            return self.AuthorAdmin(REQUEST, tabs_message=tm)
    
    ##
    ## Templates
    ##
    	
    security.declareProtected(VMS, 'AuthorAdmin')
    AuthorAdmin = LocalDTMLFile('dtml/AuthorAdmin', globals())
    
    index_html = LocalDTMLFile('dtml/author_index', globals())
    

    
    
    def manage_addRecipe(self, id, title='', ingredients='',
                         instructions='', comment='', sendnewsletter=1,
                         GoToPhotos=0,
                         REQUEST=None):
        """ create """
        dest = self
        if id.strip() == '':
            id = RecipeUtils.safeId(title).lower().strip()
            id = id.replace(' ','-')[:20]
        if id[-1] in ['_','-']:
            id = id[:-1]
    
        recipe = Recipe(id, title, ingredients, instructions, comment)
        dest._setObject(id, recipe)
        recipe = dest._getOb(id)
        
        # create newsletter
        newslettertext = recipe.getNewsletterText()
    
        subject = ""
        subject = subject + title
        newsletter=recipe.createNewsletter(subject, newslettertext,
                                           send=0)
	recipe.addNewsletterId(newsletter.id)
        if sendnewsletter and recipe.isReady():
            newsletter.send()
            
    
        if REQUEST is not None:
            # whereto next?
            if GoToPhotos:
                url = recipe.absolute_url() +'/AdminRecipePhotos'
            else:
                url = REQUEST.URL1+'/manage_workspace'
            REQUEST.RESPONSE.redirect(url)
            
            
    security.declareProtected(VMS, 'manage_addCookingQuestion')
    def manage_addCookingQuestion(self, title, question, REQUEST=None):
        """ create Cooking Question object """
        id = str(int(DateTime()))
        if title.strip()+question.strip() == '':
            raise "EmptyTitleOrQuestion", "No question"
        
        publishdate = DateTime()
        question = CookingQuestion(id, title.strip(), question.strip(),
                                   publishdate)
        self._setObject(id, question)
        question = self._getOb(id)
        
        if REQUEST is not None:
            url = self.absolute_url()+'/AdminQandAs'
            tm = url_quote_plus("Matlagningsfråga inlagd")
            url += '?tabs_message=%s'%tm
            REQUEST.RESPONSE.redirect(url)
     
            
    security.declareProtected(VMS, 'manage_editCookingQuestion')
    def manage_editCookingQuestion(self, id, title, question, REQUEST=None):
        """ possibly change a cooking question object """
        if title.strip()+question.strip() == '':
            raise "EmptyTitleOrQuestion", "No question"

        questionobj = self.getAllQuestions(filterid=id)[0]
        
        questionobj.setTitle(title.strip())
        questionobj.setText(question.strip())
        
        if REQUEST is not None:
            url = self.absolute_url()+'/AdminQandAs'
            tm = url_quote_plus("Fråga redigerad")
            url += '?tabs_message=%s'%tm
            REQUEST.RESPONSE.redirect(url)
    
    def manage_delCookingQuestion(self, id, REQUEST=None):
        """ remove object """
        self.manage_delObjects([id])
        
        if REQUEST is not None:
            url = self.absolute_url()+'/AdminQandAs'
            tm = url_quote_plus("Fråga borttagen")
            url += '?tabs_message=%s'%tm
            REQUEST.RESPONSE.redirect(url)
            
    security.declareProtected(VMS, 'manage_addCookingAnswer')        
    def manage_addCookingAnswer(self, questionid, answer, REQUEST=None):
        """ create Cooking Answer object """
        id = str(int(DateTime()))
        if answer.strip() == '':
            raise "EmptyAnswer", "No answer"
        
        questionobj = self.getAllQuestions(questionid)
        if questionobj:
            questionobj = questionobj[0]
        else:
            raise "NoQuestion", "No question object with id %s"%questionid
        
        publishdate = DateTime()
        answerobj = CookingAnswer(id, questionid.strip(), answer.strip(),
                                 publishdate)
        self._setObject(id, answerobj)
        answerobj = self._getOb(id)
        
        # Notify owner of question about this answer
        author = questionobj.aq_parent
        To = author.getEmail()
        From = self.getEmail()
        if To != From: # not answering your own question
            Subject = "Svar på din fråga"
            br = '\n'
            Msg = "%s har svarat på din fråga med denna texten:"+br*2
            Msg += "  "+ answer.strip() + br*3
            Msg += "Gå och titta på frågan här:"+br+questionobj.absolute_url()
            Msg += br*2 + "Tack, %s"%self.getRoot().title_or_id() + br
            Msg += self.getRoot().absolute_url()
            
            try:
                self.sendEmail(Msg, To, From, Subject)
            except:
                # Possibly use LOG() here
                print "COULD NOT SEND EMAIL FROM %s TO %s"%(From, To)
                print " WITH SUBJECT: "+ Subject
                print " WITH MSG: "+ Msg
            
        if REQUEST is not None:
            url = self.absolute_url()+'/AdminQandAs'
            tm = url_quote_plus("Matlagningssvar på fråga inlagd")
            url += '?tabs_message=%s'%tm
            REQUEST.RESPONSE.redirect(url)
            
    security.declareProtected(VMS, 'AdminQandAs')
    file = 'dtml/AdminQandAs'
    AdminQandAs = LocalDTMLFile(file, globals())
    
    file = 'dtml/cooking_question_form'
    cooking_question_form = LocalDTMLFile(file, globals())
            
            
InitializeClass(RecipeAuthor)



#### RECIPE ############################################


class Recipe(Folder.Folder, Persistent, RecipeAuthor,
             CatalogAware):
    """ class """

    meta_type = RECIPE_METATYPE

    _properties=({'id':'title',       'type': 'string',  'mode':'w'},
                 {'id':'ingredients', 'type': 'utext','mode':'w'},
                 {'id':'instructions','type': 'utext','mode':'w'},
                 {'id':'difficultylevel','type':'selection','mode':'w',
                  'select_variable':'difficultylevels'},
                 {'id':'categories','type':'lines','mode':'w'},
                 {'id':'datum',       'type': 'date', 'mode':'w'},
                 {'id':'notifyauthor2comments','type': 'boolean', 'mode':'w'},
		 {'id':'newsletterid','type': 'string', 'mode':'w'},
		 
                 )

    security=ClassSecurityInfo()
                 
    def __init__(self, id, title='', 
                 ingredients='', instructions='',
                 comment='',
                 difficultylevel=None, categories=[],
                 datum=None, notifyauthor2comments=true,
		 newsletterid=None):
        """ init """
        self.id = str(id)
        self.title = str(title)
        self.ingredients = ingredients
        self.instructions = instructions
        self.comment = comment
        if datum is None:
            datum = DateTime()
        elif type(datum)==type('s'):
            datum = DateTime(datum)
        self.datum = datum
        self.difficultylevel = difficultylevel
        if type(categories)!= type([]):
            categories = [categories]
        self.categories = categories
        self.notifyauthor2comments=notifyauthor2comments
	if not newsletterid:
	    newsletterid = ''
        self.newsletterid = newsletterid
        

    def assureProperties(self):
        """ make sure object has all properties """
        for each in ['title','ingredients','comment',
                     'instructions','difficultylevel']:
            if not hasattr(self, each):
                #self.__dict__[each] = ''
                setattr(self, each, '')
         
        if not hasattr(self, 'datum'):
            self.datum = DateTime()
	if not hasattr(self, 'newsletterid'):
	    self.newsletterid = ''
        
        if not hasattr(self, 'notifyauthor2comments'):
            self.notifyauthor2comments = true
            
        for each in ['categories']:
            if not hasattr(self, each):
                setattr(self, each, [])
                #self.__dict__[each] = []
            elif type(getattr(self, each))==type('s'):
                #self.__dict__[each] = [getattr(self, each)]
                setattr(self, each, [getattr(self, each)])
             
        for comment in self.objectValues(RECIPECOMMENT_METATYPE):
            if not hasattr(comment, 'commentto'):
                #comment.__dict__['commentto'] = ''
                setattr(comment, 'commentto', '')
     
            
    def getTitle(self):
        """ return self.title """
        return self.title

    def getAuthor(self, only=None):
        """ return author """
        if only is None:
            only = ''
        else:
            only = only.lower().strip()
        
        if only =='firstname':
            return self.getFirstname()
        elif only == 'lastname':
            return self.getLastname()
        elif only == 'email':
            return self.getEmail()
        elif only == 'id':
            return self.aq_parent.getId()
        elif only == 'object':
            return self.aq_parent
        else:
            return '%s %s'%(self.getFirstname(), 
                            self.getLastname())
        
    
    def addNewsletterId(self, id):
	""" set the self.newsletterid """
	self.newsletterid = id
	
    def getNewsletterId(self):
	""" return self.newsletterid """
	return self.newsletterid
    
    def getNewsletter(self):
	""" return newsletter object or None """
	id = self.getNewsletterId()
	container = self.getRoot().getNewsletterRoot()
	return getattr(container, id, None)
    
    def isReady(self):
        """ check if all is ready """
        if self.getTitle()!='' and self.getIngredients()!='' \
           and self.getInstructions()!='' and len(self.getPhotos()) >0:
            return true
        else:
            return false
        
    def doNotifyAuthor2Comments(self):
        """ return notifyauthor2comments """
        return getattr(self, 'notifyauthor2comments', true)
    
    def getIngredients(self):
        """ return ingredients """
        return self.ingredients
    
    def getInstructions(self):
        """ return instructions """
        return self.instructions
    
    def getComment(self):
        """ return comment """
        return getattr(self, 'comment','')
    
    def getThumbnail(self):
        """ return photoobject """
        photos = self.getPhotos()
        # take the 1st
        if len(photos) ==0:
            return "<em>No thumbnail</em>"
        else:
            return photos[0].tag(display='thumbnail')
                                 
        
    def getPhotos(self):
        """ return photo objects """
        return self.objectValues('Photo')

    def getCategories(self):
        """ return categories """
        return self.categories

    
    def showDate(self):
        """ if there is a special format, use that """
        if hasattr(self, 'date_format'):
            date_format = self.date_format
        else:
            date_format = '%d %b %Y'
        
            return self.datum.strftime(date_format)
    
    def showHyperlinkedCategories(self, categories=None):
        """ make every hyperlink to ?check=%s and return HTML
        """
        if categories is None:
            categories = self.categories
        links=[]
        rooturl = self.getRoot().absolute_url()
        for category in categories:
            cat_url_quoted = url_quote_plus(category)
            cat_html_quoted = html_quote(category)
            a='<a href="%s?check=%s">%s</a>'%(rooturl, cat_url_quoted, 
                                              cat_html_quoted)
            links.append(a)
        return ', '.join(links)
            
    security.declareProtected(VMS, 'NoCommentsPlease')
    def NoCommentsPlease(self, REQUEST=None):
        """ set notifyauthor2comments to false """
        self.notifyauthor2comments = false
        if REQUEST is not None:
            tm = "No comments"
            return self.index_html(REQUEST, tabs_message=tm)
    
    security.declareProtected(VMS, 'CommentsPlease')
    def CommentsPlease(self, REQUEST=None):
        """ set notifyauthor2comments to true """
        self.notifyauthor2comments = true
        if REQUEST is not None:
            tm = "Comments on"
            return self.index_html(REQUEST, tabs_message=tm)
        
    def editRecipe(self, title=None, ingredients=None, 
                   instructions=None, difficultylevel=None,
                   comment=None, datum=None,
                   categories=None, 
                   REQUEST=None,
                   sendifpossible=1):
        """ edit details of recipe """
        wasready = self.isReady()
        if title is not None:
            self.title = title.strip()
            
        if ingredients is not None:
            self.ingredients = ingredients.strip()
        
        if instructions is not None:
            self.instructions = instructions.strip()
        
        if comment is not None:
            self.comment = comment.strip()
            
        if difficultylevel is not None:
            if difficultylevel in self.difficultylevels:
                self.difficultylevel = difficultylevel
                
        if categories is not None:
            if type(categories)==type('s'):
                categories = [categories]
            checked = []
            for category in categories:
                if category in self.getCategoryOptions():
                    checked.append(category)
            self.categories = checked
            
        
        if datum is not None:
            if type(datum)==type('s'):
                datum = DateTime(datum)
            if datum > DateTime():
                raise "FutureDate", "Recipe date can not be in future"
            self.datum = datum
            

        if sendifpossible:
            if not wasready and self.isReady():
                # yes, we send
		newsletter = self.getNewsletter()
		if not newsletter:
		    newslettertext = self.getNewsletterText()
                    subject = self.getTitle()
                    newsletter = self.createNewsletter(subject,
                                                       newslettertext,
						       send=0)
		# Now send this newsletter
		newsletter.send()
		
        if REQUEST is not None:
            tm = "Recipe Saved"
            return self.EditRecipe(REQUEST, tabs_message=tm)
           
    def ActionURL(self, url=None):
        """
        If URL is http://host/index_html
        I prefer to display it http://host
        Just a little Look&Feel thing
        """
        if url is None:
            url = self.REQUEST.URL

        URLsplitted = string.split(url,'/')
        if URLsplitted[-1] == 'index_html':
            return string.join(URLsplitted[:-1],'/')

        return url


    
    def getNewsletterText(self):
        """ prepare the text to send in a newsletter """
        roottitle = self.getRoot().title_or_id()
        br="\n"
        m="""Nytt recept på %s av %s %s"""%(roottitle,
                                            self.getAuthor(), br*2)
        m=self.getTitle() + br*2
        
        m="Kolla in receptet på: %s"%self.absolute_url()
        m = m + br*2 + self.getComment()
        return m
    
    security.declareProtected(VMS, 'addPhoto')
    def addPhoto(self, file, sendifpossible=0, REQUEST=None):
        """ create photo object """
        wasready = self.isReady()
        dest = self.manage_addProduct['Photo']
        
        
        dest.manage_addPhoto(id='', title=self.title_or_id(),
                             file=file,
                             content_type='', engine='PIL',
                             quality=85, pregen=1)
        
        
        if REQUEST is not None:
            response = self.REQUEST.RESPONSE
            url = self.absolute_url()
            url = url + "/AdminRecipePhotos"
            response.redirect(url)
            
    security.declareProtected(VMS, 'delPhoto')
    def delPhoto(self, id, REQUEST=None):
        """ remove photo object """
        dest = self
        dest.manage_delObjects([id])
        
        if REQUEST is not None:
            response = self.REQUEST.RESPONSE
            url = self.absolute_url()
            url = url + "/AdminRecipePhotos"
            response.redirect(url)
            
    ## Templates
    
    index_html = LocalDTMLFile('dtml/recipe_index', globals())
    recipe_print = LocalDTMLFile('dtml/recipe_print', globals())
    
    security.declareProtected(VMS, 'AdminRecipePhotos')
    AdminRecipePhotos = LocalDTMLFile('dtml/AdminRecipePhotos',
                                      globals())
    security.declareProtected(VMS, 'EditRecipe')
    EditRecipe = LocalDTMLFile('dtml/EditRecipe', globals())
    
    
    ## Newsletters
    
    def createNewsletter(self, title, text,
                         send=1, REQUEST=None):
        """ wrap _createNewsletter and send it """
        newsletter = self._createNewsletter(title, text)
        if send:
            newsletter.send()
        
        if REQUEST is not None:
            response = self.REQUEST.RESPONSE
            url = self.absolute_url()
            url = url + "?newsletter=created"
            response.redirect(url)
        else:
            return newsletter
            
            
    def _createNewsletter(self, title, text):
        """ create recipenewsletter object """
        if text.strip() == '':
            raise "InvalidText", "Newsletter can not be empty"
        id = DateTime().strftime('%Y-%m-%d_%H-%M')
        
        destination = self.getNewsletterRoot()
        newsletter = RecipeNewsletter(id, title, text)
        destination._setObject(id, newsletter)
        newsletter = destination._getOb(id)
        
        return newsletter
    
    ## Comments 
    
    def createComment(self, name, email, comment,
                      commentto=None,
                      REQUEST=None):
        """ create a recipe comment object and 
        set some cookies and some sessions possibly """
        raise NotImplementedError, "Comments currently disabled"
    
        name=name.strip()
        email=email.strip()
        comment=comment.strip()
        if comment == '':
            raise "NoComment", "Comment can not be empty"
        
        if comment.find('<a href=') > -1:
            raise "InvalidComment", "Comment not valid"

        if commentto is not None:
            if not commentto in self.objectIds(RECIPECOMMENT_METATYPE):
                raise "NoCommentTo", "No comment like that found, %s"%commentto
        
        # go ahead and create comment object
        tempid = str(int(DateTime()))+name
        id = RecipeUtils.safeId(tempid).lower().replace(' ','')
        id = id.strip()
        rcomment = RecipeComment(id, name, email, comment, commentto)
        self._setObject(id, rcomment)
        comment = self._getOb(id)
        
        # notify the author
        if self.doNotifyAuthor2Comments():
            self._notifyAuthorAboutComment(comment, butnot=email)
        
        # notify the author of the comment
        if commentto is not None:
            self._notifyCommentAuthorAboutComment(comment, butnot=email)
            
        if REQUEST is not None:
            request = self.REQUEST
            response = request.RESPONSE
            session = request.SESSION
            then = DateTime()+300
            then = then.rfc822()
            # remember name and email
            response.setCookie('RecipeCommentName',
                               name, path='/', expires=then)
            response.setCookie('RecipeCommentEmail',
                               email, path='/', expires=then)
            
            # remember sessionkey
            sessionkey = comment.getSessionKey()
            session.set('RecipeCommentSessionKey', sessionkey)
            
            url = self.absolute_url()
            url = url + "?recipe_comment=added"
            
            response.redirect(url)
            
    def _notifyCommentAuthorAboutComment(self, comment, butnot=None):
        """ Send a notification to the parent of this comment if one. """
        email_name_combos = {}
        email_commentto_combos = {}
        
        br = '\n'
        f = "%s <%s>"%(self.mastername, self.masteremail)
        subject = "Kommentar på kommentar på recept"
        
        if butnot is None:
            butnot = ''
            
        origcomment = comment
        while comment.isSubcomment():
            supcomment = getattr(self, comment.getCommentTo())
            email = supcomment.getEmail()
            if email != butnot and RecipeUtils.ValidEmailAddress(email):
                m = comment.getName()
                m += " har skrivit en kommentar under din kommentar på: "
                m += self.absolute_url() + "#%s"%comment.getId() + br
                m += "med följande text:" + br*2
                m += "  " + comment.getComment() + br*3
                m += "För att skriva en uppföljare, gå till:"+br
                m += self.absolute_url()+"?ct=%s&ye=%s&yn=%s"%(url_quote_plus(comment.getId()),
                                                               url_quote_plus(email),
                                                               url_quote_plus(supcomment.getName()))
                m += "#bottomform"
                m += br*3 + "Tack, %s"%self.getRoot().title_or_id() + br
                m += self.getRoot().absolute_url()
                
                self.sendEmail(m, email, f, subject)
                
            comment = supcomment
        

            
            
    def _notifyAuthorAboutComment(self, comment, butnot=None):
        """ send email to author of the recipe.
        The 'butnot' param is going to be the same as the 
        author if he posts a comment to his own recipe."""
        br="\n"
        t = self.getAuthor(only='email')
        if butnot is not None and t.lower() == butnot.lower().strip():
            return
        f = "%s <%s>"%(self.mastername, self.masteremail)
        title = self.getTitle().strip()
        subject = "Kommentar till ditt recept (%s)"%title
        m = comment.getName() + " (" + comment.getEmail() + ")"
        m += " har skrivit en kommentar på: "
        m += self.absolute_url() + " med följande text:"+br*2
        m += " %s"%comment.getComment()
        
        m += br*3
        m += "Inga fler kommentarer på detta recept" + br
        m += self.absolute_url()+'/NoCommentsPlease' + br*2
        m += "Ångra, jo vill ha kommentarer" + br
        m += self.absolute_url()+'/CommentsPlease' + br*2
        m += "Tack, %s"%self.getRoot().title_or_id() + br
        m += self.getRoot().absolute_url()
        
        self.sendEmail(m, t, f, subject)
        
    def changeComment(self, id, comment):
        """ change the comment if allowed """
        rcomment = self.getCommentById(id)
        session = self.REQUEST.SESSION
        usersessionkey = session.get('RecipeCommentSessionKey','')
        if usersessionkey == rcomment.getSessionKey():
            rcomment.setComment(comment.strip())
        else:
            raise "NotEditable", "You can not edit this comment"
        
        response = self.REQUEST.RESPONSE
        url = self.absolute_url()
        url = url + "?recipe_comment=edited"
        
        response.redirect(url)

    security.declareProtected(VMS, 'deleteComment')
    def deleteComment(self, commentids, REQUEST=None):
        """ delete a comment """
        if type(commentids)== type('s'):
            commentids=[commentids]
        self.manage_delObjects(commentids)
        if REQUEST is not None:
            url = self.absolute_url()
            url = "?recipecomment=deleted"
            REQUEST.RESPONSE.redirect(url)
            
    def getRecipeComments(self, filter='', sort=1, reverse=1):
        """ """
        objects = self.objectValues(RECIPECOMMENT_METATYPE)
        objects = self._filterOnCommentTo(objects, filter)
        if sort:
            objects = sequence.sort(objects, (('bobobase_modification_time',),))
            if reverse:
                objects.reverse()
        return objects
    
    def _filterOnCommentTo(self, objects, filter):
        """ all passing objects in 'objects' must have a commentto == 'filter' """
        checked = []
        for object in objects:
            if object.getCommentTo()==filter:
                checked.append(object)
        return checked
    
    def getCommentById(self, id):
        """ return by id """
        if hasattr(self, id):
            return getattr(self, id)
        raise "NoComment", "That comment does not exist"


    recipe_comment_form = LocalDTMLFile('dtml/recipe_comment_form',
                                   globals())
    show_recipe_comments = LocalDTMLFile('dtml/show_recipe_comments',
                                    globals())
				    
setattr(Recipe, 'print', Recipe.recipe_print)

InitializeClass(Recipe)        



#### RECIPECOMMENT #####################################


class RecipeComment(SimpleItem.SimpleItem, CatalogAware):
    """ class """
    
    meta_type = RECIPECOMMENT_METATYPE
    
    _properties=({'id':'name',        'type': 'string',  'mode':'w'},
                 {'id':'email',       'type': 'string',  'mode':'w'},
                 {'id':'comment',     'type': 'utext',   'mode':'w'},
                 )
    
    icon = '%s/comment.gif'%ICON_LOCATION
    
    security=ClassSecurityInfo()

    def __init__(self, id, name, email, comment, commentto=None):
        """ init """
        self.id = str(id)
        self.name = str(name).strip()
        self.email = str(email).strip()
        self.comment = str(comment).strip()
        if commentto is None:
            commentto = ''
        self.commentto = commentto.strip()
        
        self.sessionkey = RecipeUtils.getRandomString()
        
    def getSessionKey(self):
        """ return sessionkey """
        return self.sessionkey
    
    def showNameAndEmail(self):
        """ return name and email nicely """
        name = self.name
        email = self.email
        if name != '' and email != '':
            r=name+" "
            r=r+RecipeUtils.encodeEmailString(email, email)
            return r
        elif name != '':
            return name
        elif email != '':
            return RecipeUtils.encodeEmailString(email, email)
        else:
            return "<em>varken namn eller email</em>"
        

    def showComment(self):
        """ return comment """
        return self.getComment().replace('\n','<br>')
    
    def getName(self):
        """ return name """
        return self.name
    
    def showName(self):
        """ return name """
        return self.getName()
    
    def getEmail(self):
        """ return email """
        return self.email
    
    def showEmail(self):
        """ return email encoded """
        email = self.getEmail()
        return RecipeUtils.encodeEmailString(email, email)
    
    def getComment(self):
        """ return comment """
        return self.comment
    
    def setComment(self, comment):
        """ set the comment """
        if comment.strip() == '':
            raise "NoComment", "Comment can not be empty"
        self.comment = comment.strip()

    def isSubcomment(self):
        """ if commentto is not '' """
        return self.getCommentTo() != ''
    
    def getCommentTo(self):
        """ return commentto """
        return getattr(self, 'commentto', '')
    
InitializeClass(RecipeComment)


#### RECIPENEWSLETTER ##################################

class RecipeNewsletter(Folder.Folder, Persistent):
    """ class """
    
    meta_type = RECIPENEWSLETTER_METATYPE
    icon = '%s/newsletter.gif'%ICON_LOCATION
    
    _properties=({'id':'title',    'type':'string',  'mode':'w'},
                 {'id':'letter',   'type':'text',    'mode':'w'},
                 {'id':'sent',     'type':'boolean', 'mode':'w'},
                 {'id':'sent2listids','type':'lines','mode':'w'},
                 )
    
    security=ClassSecurityInfo()
    
    def __init__(self, id, title, letter, sent=0):
        """ init """
        self.id = str(id)
        self.title = str(title)
        self.letter = letter
        if sent:
            sent = true
        self.sent = sent
        self.sent2listids=[]
        
    def isSent(self):
        """ return if sent """
        return self.sent
    
    def send(self):
        """ find all receivers and send """
        receiversroot = self.getNewsletterReceiversRoot()
        mtype = NEWSLETTERRECEIVER_METATYPE
        receivers = receiversroot.objectValues(mtype)
        emails = []
        for receiver in receivers:
            if receiver.getEmail().lower() not in [x.lower() for x in emails]:
                if receiver.isActive():
                    emails.append(receiver.getEmail())
    
	LOG(self.__class__.__name__, INFO, "Sent %s to %s"%(str(self.id), str(emails)))
        subject = self.title
        mfrom = "%s <%s>"%(self.mastername, self.masteremail)
        mailhost = self.MailHost
	self.sent = true
        for email in emails:
            self.sendEmail(self.letter, email, mfrom, subject)
	    
	return "Newsletter sent"

    
    def saveReceiverObjects(self, receivers):
        """ we simply store the ids of the newsletterreceiver objects
        """
        addlist = []
        for receiver in receivers:
            addlist.append(receiver.getId())
        
        oldlist = self.sent2listids
        newlist = oldlist.append(addlist)
        newlist = self._filterduplicates(newlist)
        self.sent2listids = newlist
        
    def _filterduplicates(self, list):
        """ remove all duplicates """
        check = []
        for each in list:
            if each not in check:
                check.append(each)
        return check

InitializeClass(RecipeNewsletter)


#### NEWSLETTERRECEIVER ################################
            
class NewsletterReceiver(SimpleItem.SimpleItem, 
                         RecipeNewsletter):
    """ class """
    
    meta_type = NEWSLETTERRECEIVER_METATYPE
    
    _properties=({'id':'email',    'type': 'string',  'mode':'w'},
                 {'id':'active',   'type':'boolean', 'mode':'w'}
                 )
    
    icon = '%s/receiver.gif'%ICON_LOCATION
    security=ClassSecurityInfo()
    
    def __init__(self, id, email, active=1):
        """ init """
        self.id = str(id)
        if not RecipeUtils.ValidEmailAddress(email):
            raise "InvalidEmail", "The email %s is invalid"%email
        self.email = email.strip()
        self.active = active
        
    def Unsubscribe(self):
        """ set active to false """
        self.active = false
        
    def Subscribe(self):
        """ set active to true """
        self.active = true
        
    def isActive(self):
        """ return active """
        return self.active
    
    def getEmail(self):
        """ return email """
        return self.email
        
        
    
InitializeClass(NewsletterReceiver)



#### COOKINGQUESTION ###################################

class CookingQuestion(Folder.Folder, Persistent, RecipeAuthor,
                      CatalogAware):
    """ class """

    meta_type = COOKINGQUESTION_METATYPE

    _properties=({'id':'title',    'type': 'string',  'mode':'w'},
                 {'id':'question', 'type': 'utext','mode':'w'},
                 {'id':'publishdate','type':'date', 'mode':'w'},
                 )

    icon = '%s/qmark.gif'%ICON_LOCATION
    
    security=ClassSecurityInfo()
                 
    def __init__(self, id, title, question, publishdate):
        """ init """
        self.id = id
        self.title = title
        self.question = question
        self.publishdate = publishdate
        
    def getTitle(self):
        """ return title or a bit of the question """
        if self.title.strip() != '':
            return self.title
        else:
            title = self.question.strip()
            if len(title) > 35:
                title = title[:35]+'...'
            return title
        
    def getText(self):
        """ return question """
        return self.question
    
    def has_title(self):
        """ return if title is not empty """
        return self.title != ''
    
    def setTitle(self, title):
        """ set title """
        self.title = title
       
    def setText(self, question):
        self.question = question
    

    def getAuthor(self, only=None):
        """ return author """
        if only is None:
            only = ''
        else:
            only = only.lower().strip()
        
        if only =='firstname':
            return self.getFirstname()
        elif only == 'lastname':
            return self.getLastname()
        elif only == 'email':
            return self.getEmail()
        elif only == 'id':
            return self.aq_parent.getId()
        elif only == 'object':
            return self.aq_parent
        else:
            return '%s %s'%(self.getFirstname(), 
                            self.getLastname())
    def getAnswers(self):
        """ overload getAllAnswers with this id for filter """
        filter = self.id
        return self.getAllAnswers(filter)
    
    def manage_beforeDelete(self, REQUEST, RESPONSE=None):
        """ delete any answers """
        locations_and_ids = {}
        for answer in self.getAnswers():
            if answer.aq_parent in locations_and_ids.keys():
                locations_and_ids[answer].append(answer.id)
            else:
                locations_and_ids[answer] = [answer.id]
        for location, ids in locations_and_ids.items():
            location.manage_delObjects(ids)
        
    file = 'dtml/show_cooking_question'
    show_cooking_question = LocalDTMLFile(file, globals())
    
InitializeClass(CookingQuestion)



#### COOKINGANSWER #####################################

class CookingAnswer(Folder.Folder, Persistent, RecipeAuthor, 
                    CatalogAware):
    """ class """
    
    meta_type = COOKINGANSWER_METATYPE
    
    _properties=({'id':'answer',    'type':'utext',  'mode':'w'},
                 {'id':'questionid','type':'string', 'mode':''},
                 {'id':'publishdate','type':'date', 'mode':'w'},
                 )
    
    icon = '%s/emark.gif'%ICON_LOCATION
    
    security=ClassSecurityInfo()
    
    def __init__(self, id, questionid, answer, publishdate):
        """ init """
        self.id = id
        self.questionid = questionid
        self.answer = answer
        self.publishdate = publishdate
        
    def getText(self):
        """ return answer """
        return self.answer
       

InitializeClass(CookingAnswer)        
