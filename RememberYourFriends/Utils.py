#-*- coding: iso-8859-1 -*
##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

import os, re, sys
import string
import random
import inspect
import itertools
from pprint import pprint

from Constants import *





def anyTrue(pred, seq):
    """ http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/212959 """
    return True in itertools.imap(pred,seq)


def nicepass(alpha=6,numeric=2):
    """
    returns a human-readble password (say rol86din instead of 
    a difficult to remember K8Yn9muL ) 
    """
    
    vowels = ['a','e','i','o','u']
    consonants = [a for a in string.ascii_lowercase if a not in vowels]
    digits = string.digits
    
    ####utility functions
    def a_part(slen):
        ret = ''
        for i in range(slen):			
            if i%2 ==0:
                randid = random.randint(0,20) #number of consonants
                ret += consonants[randid]
            else:
                randid = random.randint(0,4) #number of vowels
                ret += vowels[randid]
        return ret
    
    def n_part(slen):
        ret = ''
        for i in range(slen):
            randid = random.randint(0,9) #number of digits
            ret += digits[randid]
        return ret
        
    #### 	
    fpl = alpha/2		
    if alpha % 2 :
        fpl = int(alpha/2) + 1 					
    lpl = alpha - fpl	
    
    start = a_part(fpl)
    mid = n_part(numeric)
    end = a_part(lpl)
    
    return "%s%s%s" % (start,mid,end)

def ss(s):
    return s.lower().strip()

def sum(seq):
    return reduce(lambda x,y: x+y, seq)



##
## Debugging
##

def ObserverProxy(method_names):
    class Proxy:
        def __init__(self):
            self._observers = []
        def add_observer(self, observer):
            self._observers.append(observer)
        def remove_observer(self, observer):
            self._observers.remove(observer)

    def create_method_proxy(method_name):
        def method_proxy(self, *args, **kwargs):
            for observer in self._observers:
                getattr(observer, method_name)(*args, **kwargs)
        return method_proxy

    for method_name in method_names:
        setattr(Proxy, method_name, create_method_proxy(method_name))

    return Proxy()

debugobserver = ObserverProxy(["write", "close"])
debugobserver.add_observer(sys.stdout)
#debugobserver.add_observer(open('debug.log','a'))

def debug(s, tabs=0, steps=(1,), f=False, configdecider=DEBUG):
    if configdecider or f:
        inspect_dbg = []
        if type(steps)==type(1):
            steps = range(1, steps+1)
            
        pointer = 1
        zpt_fmt = '(ZPT)%s'
        while 1:
            try:
                current_position = inspect.stack()[pointer]
                caller_module = current_position[1]
                caller_method = current_position[3]
                caller_method_line = current_position[2]
                locals_ = current_position[0].f_locals
                globals_ =current_position[0].f_globals
                #print locals_.keys()
                if caller_method == 'render' and caller_module.endswith('Expressions.py'):
                    pointer += 1
                    continue
                    
                ec = locals_.get('econtext')
                if ec and hasattr(ec, 'position') and hasattr(ec, 'source_file'):
                    
                    caller_method = zpt_fmt % ec.source_file
                    caller_method_line, __ = ec.position
                    pointer += 13

                pointer += 1
            except IndexError:
                break
            combined = "%s:%s"%(caller_method, caller_method_line)
            if combined not in inspect_dbg:
                inspect_dbg.append(combined)
            if len(inspect_dbg) >= steps:
                break
            
        out = "\t"*tabs + "%s (%s)"%(s, ", ".join(inspect_dbg))
        
        print >>debugobserver, out
