#!/usr/bin/env python

#
# Titlefinder
# A python module for finding the page title of a web page
#
# Peter Bengtsson, mail@peterbe.com
#
import re, os, sys
import httplib
import urllib2

title_tag_regex = re.compile('<title>(.*?)</title>', re.I)

def fetchTitle(url):
    """ open a URL and look at the resulting page for a title.
    return None if that title can't be fetched"""
    assert url.startswith('http://'), "URL doesn't start with http://"
    
    try:
        opened = urllib2.urlopen(url)
    except urllib2.HTTPError, msg:
        print >>sys.stderr, "HTTPError"
        print >>sys.stderr, str(msg)
        return None
    except urllib2.URLError, msg:
        print >>sys.stderr, "URLError"
        print >>sys.stderr, str(msg)
        return None
    except httplib.InvalidURL, msg:
        print >>sys.stderr, "InvalidURL"
        print >>sys.stderr, str(msg)
        return None
        
        
    
    
    
    contents = opened.read()
    titles = title_tag_regex.findall(contents)
    if titles:
        return titles[0]
    else:
        return ''
    
    
    
    
    
def _grr():
    print "USAGE:"
    print "python %s http://www.some.url.com/path" % __file__
    
    
def main():
    
    if not len(sys.argv)==2:
        _grr()
        return 10
    
    url = sys.argv[1]
    print fetchTitle(url)
    
    return 0
    

if __name__=='__main__':
    sys.exit(main())