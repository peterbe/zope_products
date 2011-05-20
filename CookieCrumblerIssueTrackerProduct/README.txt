CookieCrumblerIssueTrackerProduct
(c) Peter Bengtsson, mail@peterbe.com, Oct 2005
License: ZPL

CookieCrumblerIssueTrackerProduct is basically a CookieCrumbler
subclass design explictly for use in IssueTrackerProduct environments.
It defines some nicer login/logout pages in ZPT and gives an option to
have the loging to last for longer than one session a la Gmail, SF.net.

To install it, just unpack like any other product in Zope ie. in your
Products folder. For it to work you need to have:

 - CookieCrumbler (http://hathawaymix.org/Software/CookieCrumbler)
 
 - IssueTrackerProduct (http://www.issuetrackerproduct.com)
 
 - CheckoutableTemplates (http://www.issuetrackerproduct.com/Documentation#checkoutabletemplates)
 
Once you've restarted Zope, all you need to do is to go into the Zope
Management Interface (ZMI) and select 
"Cookie Crumbler (IssueTrackerProduct)" from the drop down in the top
right hand corner. 

If you want to change any of the templates, install
CheckoutableTemplates and visit
http://localhost:8080/cclogin/showCheckoutableTemplates


