""" Example web application using wwwcgi module.

    To create your application just make a copy of this
    file and rename it.
"""

import os
import sys

## Global parameters
#TCP/IP port for http communiction; default is 80
PORT = 80

#name of the function in this module used by wwwcgi to
#forward the keyword parameters to it
FUNCTION = 'main'

try:
    #name of this module
    MODULE = __name__
    if MODULE == '__main__':
        #if called this module directly from command line, try
        #to find get module name from it's file name
        MODULE = os.path.splitext(os.path.split(__file__)[1])[0]
except:
    MODULE = 'wwwcgi_app'

#base url to call this modules' function main
URL = 'http://localhost:%(PORT)s/?action=call&module=%(MODULE)s&function=%(FUNCTION)s' % globals()
##/ Global parameters


def main(**kw):
    """ This function is called from wwwcgi server using the above url URL

E.g.: http://localhost/wwwcgi.py?action=call&module=wwwcgi_app&function=main

All submitted parameters values are in kw parameter. To get their values use:

param = kw.get('paramName', 'defaultValue')

Change the content of the example html variable (i.e. the web page content 
forwareded through the server to the web browser) as you wish.
    """
    #assign value of global URL variable to local url variable
    url = URL
    
    title = 'Page title'
    

    html = """<html><title>%(title)s</title><body>

This goes to html page returned to the browser<br />

<a href="%(url)s&param=cmd1">command 1</a><br />

<a href="%(url)s&param=cmd2">command 2</a><br />
Paraters received by the main function:<br />
%(kw)s
</body></html>
""" % locals()
    
    print html


def start():
    try:
        from jjutl.wwwcgi import wwwcgi
    except ImportError:
        import wwwcgi
    path = os.path.split(wwwcgi.__file__)[0]   
    port = PORT
    url = URL

    os.system('start python %(path)s\wwwcgi.py %(port)s' % locals())
    os.system('start "wwwcgi" "%(url)s&param=START"' % locals())
        
if __name__ == '__main__':
    start()
