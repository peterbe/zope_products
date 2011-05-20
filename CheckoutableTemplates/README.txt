CheckoutableTemplates by Peter Bengtsson,
Fry-IT Ltd, 2003-2004.

This software is released under the ZPL license.

Credits to Dieter Maurer and his code that inspired me to
enable the 'showCheckoutableTemplates' page.
Credits to the MoinMoin project (http://sourceforge.net/projects/moin/)
for the inspiration and code used in diff.py


CheckoutableTemplates allows you to make exceptions
to DTMLFile and PageTemplateFile attributes of a Python product.
This is highly usable if you have an instance of a Python 
product class, and you want to change some little thing in one
of its templates.

In Zope, it is NOT possible to subclass an template attribute
from withing the ZMI. Having templates as attributes in a 
Python product class is useful because when you roll out a new 
version, it's easy to include your changes. It's also useful in 
that you can make the Zope object instance very simple.

The advantage about only having templates instanciated inside
the class instance in Zope is that you can make changes to the
look and feel of one and only one instance.

Suppose your Python product defines a template like this::

 class MyProduct(ObjectManager):
     meta_type = 'My Meta Type'
     def __init__(self, id, title=''):
         ...
	 
     show_page = DTMLFile('dtml/show_page', globals())
     edit_page = PageTemplateFile('zpt/edit_page', globals())
     
Then you can use these templates by visiting 
http://localhost:8080/myinstance/show_page

Suppose you're **not** the author of the Python product but have 
found a spelling misstake or an invalid HTML tag in show_page.dtml,
 or suppose you have two instance of the product; one 
called 'myinstance' and one called 'herinstance'. For the 'herinstance'
instance you want the show_page to look slightly different.
How do you fix that without editing the sourcecode of the Python
product? You simply can't!

Suppose instead that you have CheckoutableTemplates installed and
define your Python product like this::

 from Products.CheckoutableTemplates \
    import CTPageTemplateFile, CTDTMLFile
 
 class MyProduct(ObjectManager):
     meta_type = 'My Meta Type'
     def __init__(self, id, title=''):
         ...
	 
     show_page = CTDTMLFile('dtml/show_page', globals())
     edit_page = CTPageTemplateFile('zpt/edit_page', globals())
     
Then, visit http://localhost:8080/myinstance/showCheckoutableTemplates
and you'll see a list of templates that you can make exceptions
on. When you use that interface to check out a template, an object
is created called show_page.dtml and/or edit_page.zpt.
Their Id "protected", so you can't call it whatever you want. The only 
thing that links these template objects with your python product is
the Id.

If you have SilverCity (http://silvercity.sourceforge.net/) installed
code syntax will be shown more nicely. It is not a necessity.

Again, you visit http://localhost:8080/myinstance/show_page,
CheckoutableTemplates makes a check if there is an object called
'show_page.dtml'. If so, use that instead; if not, use the file system
template as normal.

If you have installed several Python products that use 
CheckoutableTemplates, then the showCheckoutableTemplates page will
list the templates of all Python products. To help you with this, the
Python product can define an attributes called 'this_package_home'
like this::

 from Globals import package_home

 from Products.CheckoutableTemplates \
    import CTPageTemplateFile, CTDTMLFile
 
 class MyProduct(ObjectManager):
     meta_type = 'My Meta Type'
     def __init__(self, id, title=''):
         ...
	 
     show_page = CTDTMLFile('dtml/show_page', globals())
     edit_page = CTPageTemplateFile('zpt/edit_page', globals())
     
     this_package_home = package_home(globals())

Generally you don't have to worry about this option.

Refreshing a Python product is something you don't have to be
worried about. When you refresh the Python product 
CheckoutableTemplates rechecks all template attributes but only
changes those which have changed.

Just because you have defined your template attributes with
CheckoutableTemplates doesn't mean that you have to use it. It's just
extremely useful IF you will need it at a later point. It also makes
it possible to edit your templates via the web if you for some reason
can't do it on the command line in emacs.

When you start Zope, CheckoutableTemplates keeps a record of 
all templates your Python product uses. It stores this in 
'<zoperoot>/var/CTConfig.dump' which is a pickle dump. 

If you have your zoperoot linked as a symbolic link, you'll 
have to set this as an environment variable in your start 
script::

 CT_HOME=/home/peterbe/zope261b2/var
 CT_SOFTWARE_HOME=/home/peterbe/zope261b2/lib/python
 export CT_HOME
 export CT_SOFTWARE_HOME

Set this appropriatly to how you have your Zope set up. I 
guess that if you do, you know enough about Zope and sys admin
to be able to see what needs to be done.
The best way to test your settings is that you use the 
showCheckoutableTemplates page.

It is not recommended for live environments,  but useful when 
debugging your python product, you can enable 'CT_CAN_WRITEBACK' 
which allows you to save a Zope object template back onto the file system.
Set this in your start script like this::

 export CT_CAN_WRITEBACK=1
 
To do this on Windows, in start.bat you write::

 SET CT_CAN_WRITEBACK=1
 
This product was developed to be used in a live environment, 
but comes with absolutely no warrenty. I advice that you 
familiarize yourself with CheckoutableTemplates before you
decide to enroll it in your best Python products.

All bug reports and suggestions are welcome to peter@fry-it.com.

The CTPageTemplateFile and CTDTMLFile also accepts a parameter called 
'optimize' which can (at the time of writing this) accept values
like 'CSS', 'HTML' or 'XHTML'. If any of these are set, the output
CSS/HTML/XHTML will be optimized but stripping out everything excessive 
such as excess whitespace and comments. The 'XHTML' optimizer is less
rough than the 'HTML' optimizer which strips unnecessary quotes. NOTE!
This only works if you have the slimmer.py module installed.
As an example, some CSS can be changed from::

 /* Header 1 */
 h1 {
     font-family: Verdana, Arial;
     color: #123456;
 }

To this::

 h1{font-family:Verdana,Arial;color:#123456;}

Of course it depends on how your HTML output looks like but
preliminary calculations have shown that you get on average a 10-20%
time gain average. I.e. the time to download the document plus the
time to optimize the output. 
Note: Always test your pages after you have switched on the optimization. 
Note2: Don't optimize twice. Use sparingly.::

 from Products.CheckoutableTemplates \
    import CTPageTemplateFile, CTDTMLFile
 
 class MyProduct(ObjectManager):
     meta_type = 'My Meta Type'
     def __init__(self, id, title=''):
         ...
	 
     show_page = CTDTMLFile('dtml/show_page', globals(),
                            optimize='XHTML')
     edit_page = CTPageTemplateFile('zpt/edit_page', globals(),
                                    optimize='HTML')
     styles_css = CTDTMLFile('dtml/show_page', globals(),
                             optimize='CSS')
			     
			     
			     
