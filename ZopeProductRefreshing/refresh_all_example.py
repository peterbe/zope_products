#!/usr/bin/env python


#-- Start of configuration ----------------------------------------------------

#libpath="lib/python"
products = (
  dict(
    CTurl="http://localhost:9080/Control_Panel/Products/FriedZopeBase",
    productpath="Products/FriedZopeBase",
    dependencies = ["FriedDocument", "FriedCMS"]
  ),
  dict(
    CTurl="http://localhost:9080/Control_Panel/Products/FriedDocument",
    productpath="Products/FriedDocument",
  ),  
  dict(
    CTurl="http://localhost:9080/Control_Panel/Products/FriedCMS",
    productpath="Products/FriedCMS",
  ),  

)
   

refresh_type = "clever" # or 'forced'
netrc_authenticator = "zope"

#-- End of configuration ------------------------------------------------------

import click_on_product_refresh
click_on_product_refresh.cli(globals())
