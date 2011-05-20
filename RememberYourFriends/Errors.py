##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

##
## Errors
##

class _Exception(Exception):
    """ by subclassing Exception like this we can subsequently "proxy" 
    all of our custom exceptions below. 
    """
    pass

class SubmitError(_Exception):
    pass

class InvalidURLError(_Exception):
    pass


#
# Security related
#

class UnauthorizedSubmitError(_Exception):
    """ used when forms (an alike) are used without having matching authorisation.
    Note that this is different from Zope's ACL Unauthorized error.
    """
    pass

class MissingArgumentsError(_Exception):
    """ happens when you call a zsql method without passing the complete
    list of parameters; which is a source of problems.
    """
    pass

class ExcessArgumentsError(_Exception):
    """ happens when you call an zsql method with keywords arguments that
    the zsql method doesn't expect.
    """
    pass
