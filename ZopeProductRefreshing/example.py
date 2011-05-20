#!/usr/bin/env python


#-- Start of configuration ----------------------------------------------------

libpath = "path/to/zopes/lib/python"
CTurl = "http://localhost:8080/Control_Panel/Products/MyProduct"
productpath = "path/to/zopes/Products/MyProduct"
dependencies = [] # names of other products

refresh_type = "clever" # or 'forced'
netrc_authenticator = "something"

#
# Now put in your ~/.netrc this:
# machine something
#      login qua
#      password secret
#

#-- End of configuration ------------------------------------------------------





import os, netrc, sys
import click_on_product_refresh

# start the refresihing
ask_for_password = 1
try:
    credentials = netrc.netrc()
    ret = credentials.authenticators(netrc_authenticator)
    if ret:
        uname, account, passw = ret
        ask_for_password = 0
except IOError, e:
    print >>sys.stderr, "missing .netrc file %s" %  str(e).split()[-1]

if ask_for_password:    
    uname = click_on_product_refresh.getuser()
    passw = click_on_product_refresh.getpass()
    
if libpath:
    sys.path.append(libpath)

click_on_product_refresh.start(CTurl, uname, passw, productpath, 
                               refresh_type=refresh_type,
                               dependencies=dependencies
                               )
