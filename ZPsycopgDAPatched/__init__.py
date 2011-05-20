## Monkey patch for ZPsycopgDA where 'infinity' 
## is not supported.

from string import split, join, strip
try:
    import psycopg
    from psycopg import new_type, register_type, \
         DATETIME, TIME, DATE, INTERVAL, STRING
    do_patch = 1
except:
    do_patch = 0
    
from DateTime import DateTime


# Convert an ISO timestamp string from postgres to a DateTime (zope version)
# object.
def cast_DateTime_Better(str):
    if str:
        # this will split us into [date, time, GMT/AM/PM(if there)]
        dt = split(str, ' ')
        if len(dt) > 1:
            # we now should split out any timezone info
            dt[1] = split(dt[1], '-')[0]
            dt[1] = split(dt[1], '+')[0]
            s = split(join(dt[:2], ' '), '.')[0]
        else:
            s = dt[0]
            
        if s =='infinity':
            return 'infinity'
        elif s == '-infinity':
            return '-infinity'
        else:
            return DateTime(s)
    
    
# Convert an ISO date string from postgres to a DateTime(zope version)
# object.
def cast_Date_Better(str):
    if str:
        if str =='infinity':
            return 'infinity'
        elif str == '-infinity':
            return '-infinity'
        else:
            return DateTime(str)
        

from Products.ZPsycopgDA.DA import Connection, cast_Time, cast_Interval



def set_type_casts(self):
    "Make changes to psycopg default typecast list"
    if self.zdatetime:
        #use zope internal datetime routines
        ZDATETIME=new_type((1184,1114), "ZDATETIME", cast_DateTime_Better)
        ZDATE=new_type((1082,), "ZDATE", cast_Date_Better)
        ZTIME=new_type((1083,), "ZTIME", cast_Time)
        ZINTERVAL=new_type((1186,), "ZINTERVAL", cast_Interval)
        register_type(ZDATETIME)
        register_type(ZDATE)
        register_type(ZTIME)
        register_type(ZINTERVAL)
    else:
        #use the standard. WARN: order is important!
        register_type(DATETIME)
        register_type(DATE)
        register_type(TIME)
        register_type(INTERVAL)
    if getattr(self, "ustrings", 0) and self.encoding:
        USTRING = psycopg.new_type(psycopg.STRING.values, "USTRING",
        cast_String_factory(self.encoding))
        register_type(USTRING)
    else:
        register_type(STRING)
        
if do_patch:
    from zLOG import LOG, INFO
    LOG("ZPsycopgDAPatched", INFO, "ZPsycopgDA monkey patched!")
    Connection.set_type_casts = set_type_casts