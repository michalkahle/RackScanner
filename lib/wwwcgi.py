""" Minimal web server/cgi script for local use.

  If called with port number as a parameter, web server
  listening on that port will be launched which will serve
  files from the folder where it was started, serving
  index.html or files listing if just folder name (or nothing)
  supplied to the browser.
"""
version = '0.2'

#==== module global variables, functions ===================================

#---- ... for cgi part ----------

# wwwcgi - example list of dict which can be supplied to printListOfDictForm for
#          creation of html form
#
# If you issue url request in the format
#
#   http://localhost:port/wwwcgi.py?action=edit&module=MODNAME
#
# (where MODNAME is in this case 'wwwcgi') then this list of dict structure
# will be requested from the module of the name MODNAME by calling a function
# MODNAME.update(ldic=None). Any outputed during the update() call will be rendered
# as html.
#
# Html form for editing of the fields specified in the returned list
# of dicts will be created and rendered.
#
# When the form is submitted, function MODNAME.update() (or any other function
# which name is specified in optional function query parameter) will be called so that
# the changed values can be stored somewhere. Any messages printed to stdout
# during the update() will be rendered. The set() should return 0 upon success.

wwwcgi = [
 {'name': 'firstfield', 'value':'value of the first field', 'caption':'Label for the 1st field', 'hint':'Hint for the 1st fild'},
 {'name': 'secondfield', 'value':'value of the second field', 'caption':'Second fld label'},
]

#def get():
#    print "returning wwwcgi.wwwcgi by wwwcgi.get()"
#    return wwwcgi

def update(awwwcgi=None):
    """
        This function is called by the server upon submission of the form. Then
        it functions as a "set" function.
        awwwcgi is a list of dict structure like wwwcgi (see above), with 'value's
        eventually modified in html <form>. Do with the new 'value's
        whatever you like.

        If the function is called without awwwcgi set, then it just functions
        as "get" function and returns wwwcgi list of dicts.

        Define similar function in any other python module (which can be imported)
        and use url to edit your list of dicts:

        http://localhost/wwwcgi.py?action=edit&module=YOURMODULE&function=YOURFUNCTION


    """
    if awwwcgi:
        print "setting wwwcgi by wwwcgi.update()"
        for d in wwwcgi:
            ad = fd_get(awwwcgi, d['name'])
            if d['value'] <> ad['value']:
                d['value'] = ad['value']
                print d['name'], 'changed', d['value'], '->', ad['value']


    return wwwcgi

def fd_get(ld, fn):
    """ Utility function to return a field dict definition for the field
        of given  name (fn) from the list of dicts (ld)
    """
    for d in ld:
        if d['name'] == fn:
            return d
    return None


def dic2ldic(dic):
    """ Utility function to convert regular dictionary to the list of dicts used
        by the above update function """
    l = []
    for k, v in dic.items():
        l.append({'name':k, 'value':v})

    return l

def dicUpdate(dic, ldic):
    """ Utility function to update regular dictionary dic with values returned
        in ldic structure from the server (updated by values submitted by
        the user in web browser). """
    for d in ldic:
        k = d['name']
        if dic.has_key(k):
            dic[k] = d['value']

#---- /... for cgi part -----------


def getModuleFunc(module, fn, doreload=None):
    """ Try to import module and get its function and return it. Return None if failed. """

    try:
        m = __import__(module, globals(), locals(), [fn])
        if doreload:
            reload(m)
    except:
        print 'Failed to import %s (%s, %s)' % ((module,) + sys.exc_info()[:2])
        return

    try:
        func = getattr(m, fn)
        return func
    except:
        print 'Module %s has no function %s (%s %s)' % ((module, fn) + sys.exc_info()[:2])
        return


#---- ... for server part ---------
#add to the cgiscripts names of the files which you want to run
#instead of showing their source code

cgiscripts = ['wwwcgi.py','sqlite.py']
#---- /... for server part --------

#==================================================================


#================ WWW server part =================================
import sys, os
if (' ' in sys.executable):
    #dirty fix; did not work with python placed in folder containing spaces in its name
    sys.executable = 'C:\\PROGRA~1\\PLONE2~1\\PYTHON\python.exe'


import BaseHTTPServer, CGIHTTPServer

Aborted = False
Restarting = False

class Server(BaseHTTPServer.HTTPServer):

    def serve_forever(self):
        """Handle one request at a time until doomsday or Aborted"""
        print 'wwwcgi HTTP server started at port %s' % self.server_port
        while True:
            self.handle_request()
            if Aborted or Restarting:
                break

class Handler(CGIHTTPServer.CGIHTTPRequestHandler):
    #cgi_directories.append('.')
    cgi_directories = ['']

    def checklocal(self):
        if self.client_address[0] <> '127.0.0.1':
            self.send_error(403, 'Only local host allowed')
            return False
        else:
            return True


    def send_head_loc(self):
        # copied from SimplteHTTPRequestHandler, the only difs are (see #MY):
        # - does not send error
        # - adds to index.htm* also wwwcgi.html if directory specified as a request path
        # - for scripts filenames in cgiscripts list return None

        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            for index in 'wwwcgi.html', "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        else:
            if os.path.split(path)[1] in cgiscripts:
                return None
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            #MY self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(os.fstat(f.fileno())[6]))
        self.end_headers()
        return f


    def info(self):
        global Aborted, Restarting
        if (self.path.find('action=exit') >= 0) and (self.path.find('help') < 0):
            Aborted = True
        if (self.path.find('action=restart') >= 0):
            Restarting = True #calling batch file should restart the wwwcgi.py server if errorlevel 1                        
        print 'client:' + self.client_address[0] + ' path=' + str(self.path)

    def do_POST(self):
        if self.checklocal():
            if not self.tryCallModule():
                f = self.send_head_loc()
                if f:
                    self.copyfile(f, self.wfile)
                    f.close()
                else:
                    CGIHTTPServer.CGIHTTPRequestHandler.do_POST(self)

            self.info()

    def do_GET(self):
        if self.checklocal():
            if not self.tryCallModule():
                f = self.send_head_loc()
                if f:
                    self.copyfile(f, self.wfile)
                    f.close()
                else:
                    CGIHTTPServer.CGIHTTPRequestHandler.do_GET(self)
            self.info()

    def tryCallModule(self):
        """ If URL contaion 'action=call' try to load python module and call its function
            so that cgi script does not have to be loaded from hard drive.
        """
        if self.path.find('action=call'):
            query = self.path.split('?')[-1].replace('+',' ')
            dic = {}
            for par in query.split('&'):
                kv = par.split('=', 1)
                if len(kv) == 2:
                    name, value = kv
                    if dic.has_key(name):
                        oldvalue = dic[name]
                        if isinstance(oldvalue, basestring):
                            dic[name] = [oldvalue, value]
                        else:
                            dic[name].append(value)
                    else:
                        dic[name] = value

            module = dic.get('module','')
            if not module:
                return False

            function = dic.get('function','')
            doreload = dic.get('reload', None) #if submitted this param, the python module will be reloaded by the server, useful during development
            func = getModuleFunc(module, function, doreload)
            if func:
                oo = sys.stdout
                try:
                    import StringIO
                    io = StringIO.StringIO()
                    sys.stdout = io

                    res = func(**dic)
                    
                    defaults = {'Content-Type':'text/html'}
                    if isinstance(res, dict):
                        defaults.update(res)

                    #path = self.translate_path(self.path)
                    #ctype = self.guess_type(path)
                    ctype = defaults['Content-Type'] #'text/html'
                    self.send_response(200)
                    self.send_header("Content-type", ctype)
                    self.send_header("Content-Length", str(io.len))
                    self.end_headers()
                    io.seek(0)
                    self.copyfile(io, self.wfile)
                finally:
                    sys.stdout = oo

                return True
            else:
                print 'getModuleFunc(%(module)s, %(function)s) Failed' % locals()
                return False
        else:
            return False

#http://feetup.org/blog/dev/python

def runwww(server_class=Server, handler_class=Handler, port=80):
    server_address = ('', port)
    #handler_class.cgi_directories = ['']
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()
    if Restarting:
        sys.exit(1)

if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except:
        port = 80
    runwww(port=port)
