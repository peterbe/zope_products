=================
ZopeStatusChecker
=================


How it installs
===============

You simply put this product in the Products directory of any Zope 2
application and it will automatically make itself available at
http://localhost:8080/Control_Panel/Statuschecker

It will then return a text/plain result showing some output and you
can expect the HTTP result code to be '200 OK'


What it does
============

It will automatically find all Database connections in the ZODB and
will look for python scripts (Script (Python)) called 'status-check'
and run them.

So, to include your own test, create a Script (Python) anywhere inside
the zope (eg. inside your custom application or Plone site) called
'status-check' which returns something and doesn't raise an error. If
this script raise an error or return False it will be flagged as "NOT
OK" on the Statuscheck page. 


Options
=======
If you instead hit
http://localhost:8080/Control_Panel/Statuschecker?quiet=1 it will
either return "OK" or "NOT" (in text/plain) where "NOT" will be
returned if anything didn't go as planned.

In conjunction with ?quiet=1 you can also append simple_errors=1 which
will return very simple errors always suffixed after a simple NOT.
This is useful if you want to for example scan for the NOT but also
get a little error as well. 

If you hit
http://localhost:8080/Control_Panel/Statuschecker?always_refresh=1 it
will not use its internal cache and always re-traverse the ZODB.


How it works
============

It recursively scans the whole ZODB but only on every 10th hit. That
means that 9 times out of 10 it will re-run the previously found tests
again. Suppose your cron-job hits that Statuschecker every 5 minutes
and you add a new 'status-check' somewhere it will take 9*5min= 45min
until your new script will have certainly been included. 
