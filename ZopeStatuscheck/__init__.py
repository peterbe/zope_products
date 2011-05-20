import Globals, OFS, os
from Statuschecker import Statuschecker

_prodname = __name__.split('.')[-1]

def createIcon(iconspec, _prefix, pid=_prodname):
    name = os.path.split(iconspec)[1]
    res = 'misc_/%s/%s' % (pid, name)
    icon = Globals.ImageFile(iconspec, _prefix)
    icon.__roles__=None
    if not hasattr(OFS.misc_.misc_, pid):
        setattr(OFS.misc_.misc_, pid, OFS.misc_.Misc_(pid, {}))
    getattr(OFS.misc_.misc_, pid)[name]=icon
    return res


def initialize(context):
    control_panel = context._ProductContext__app.Control_Panel
    
    scid = Statuschecker.id
    Statuschecker.icon = createIcon('www/icon_zopestatuschecker.gif', globals())
    sc = getattr(control_panel, scid, None)
    if sc is None:
        sc = Statuschecker()
        control_panel._setObject(scid, sc)
        z_sc = control_panel._getOb(scid)
        
    
    
