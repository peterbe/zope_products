Read more at
http://www.fry-it.com/oss/ZTinyMCE

ZTinyMCE is an adaptation of TinyMCE into Zope2.
You can read more about TinyMCE here:
http://tinymce.moxiecode.com/

Once installed it consists of two parts:
     
     * A TinyMCE instance
     
     * Several TinyMCE Configuration instances
     
The TinyMCE Configuration instances must be able to find at least
one TinyMCE instance. The configuration is basically just a piece 
of javascript code that starts the editor. 

You can enable GZIP encoding of all .js and .css files that are served.
To enable this, go to the Properties tab of the TinyMCE instance and
check the 'Use GZip compression' checkbox on.
The total amount of JS and CSS inside tinymce is 1.15Mb. The total of
all of those files gzipped is 0.32Mb (i.e. 3.6 times smaller).

To install ZTinyMCE in different languages see INSTALL.txt

ZTinyMCE was written by Peter Bengtsson of Fry-IT ltd. in 2006-2008