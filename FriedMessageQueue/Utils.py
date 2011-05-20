##
## FriedMessageQueue
## (c) Fry-IT, www.fry-it.com
## <peter@fry-it.com>
##

def safeId(someid, nospaces=False):
    """ Just make sure it contains no dodgy characters """
    lowercase = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'
    specials = '_-.'
    allowed = lowercase + lowercase.upper() + digits + specials
    if not nospaces:
        allowed = ' ' + allowed
    n_id=[]
    allowed_list = list(allowed)
    try:
        while someid[0] in list(specials):
            someid = someid[1:]
    except IndexError:
        return ''
    
    for letter in list(someid):
        if letter in allowed_list:
            n_id.append(letter)
    return ''.join(n_id)
    