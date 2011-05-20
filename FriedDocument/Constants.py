def _getVariable(key, default):
    import os
    value = os.environ.get(key, default)
    try: value = not not int(value)
    except:
	if str(value).lower().strip() in ['yes','on']: value = 1
        elif str(value).lower().strip() in ['no','off']: value = 0
        else: value = default
    return value


DEBUG = _getVariable('DEBUG_FRIEDDOCUMENT', False) # shows some verbose dev data

META_TYPE = 'Fried Document'
PAN_META_TYPE = 'Fried Document Pan'


# Permissions
VMS = 'View management screens'
MANAGE_DOCUMENT = 'Manage Fried Document'


# Define how many revisions inside a slot that is too much.
# If a document slot exceeds this many revisions, the excess
# is dropped and lost. Keep the number high if you have plenty 
# of CPU and disk and don't mind huge .zexp files.
REVISIONS_MAXLENGTH = 50