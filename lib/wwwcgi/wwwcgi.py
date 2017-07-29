""" Minimal web server/cgi script for local use.

  If called with port number as a parameter, web server
  listening on that port will be launched which will serve
  files from the folder where it was started, serving
  index.html or files listing if just folder name (or nothing)
  supplied to the browser.

  If called with no parameter, with one string (non number) parameter,
  or more parameters it will launch an example/help cgi script
  (see runcgi()).
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


#=======================================================================

#================== CGI part =========================================
#debug = True
#debug = False

class cgibase:
    def __init__(self):
        self.title = ''
        self.debug = 0

    def printDic(self, dic, name=''):
        """ Prints content of a dictionary dic to stdout (created html page)
            in html format. """
        print name + '<ul>'
        for k in dic.keys():
            print '<li>' + str(k) + '=' + str(dic[k]) + '</li>'
        print '</ul>'

    def printList(self, l, name=''):
        """ Prints content of a list l to stdout (created html page) in html format. """
        print name + '<ul>'
        for a in l:
            print '<li>' + str(a) + '</li>'
        print '</ul>'


    def printListOfDictForm(self):
        """ Prints html form for editing of list of dicts. Each dict contains
            info about one field to be shown/edited. Keys of the dict:
                name - name of the field
                value - value of the field
                caption - label text to be rendered for the field in the form
                hint - hint for the field to be shown when mouse is over

            Special key "htmltemplate" can be present in the dict, then
            it is exepected a html page template to be rendered containing
            %(form)s formating
        """
        htmltemplate = '%(form)s'

        dic = self.form.getfirst('module', '')
        if not dic:
            dic = 'wwwcgi'
        m = __import__(dic)

        funcname = self.form.getfirst('function','update')
        g = getattr(m, funcname)

        ldic = []
        for k in self.form.keys():
            d = {}
            if False: #format == 'fs':
                d[k] = self.form[k] #FieldStorage or MiniFieldStorage object, or list of those
            else:
                o = self.form[k]

                d['name'] = o.name



                if isinstance(o, list):
                    d['value'] = delim.join([e.value for e in o])
                else:
                    d['value'] = o.value
            ldic.append(d)

        ld = g(ldic)

        lines = []
        lines.append('<form >')
        lines.append('<input type="hidden" name="action" value="edit" />')
        lines.append('<input type="hidden" name="module" value="%s" />' % dic)
        if funcname <> 'update':
            lines.append('<input type="hidden" name="function" value="%s" />' % funcname)
        lines.append('<table>')
        for d in ld:
            if d['name'] == 'htmltemplate':
                htmltemplate = d['value']
                continue

            lines.append('<tr>')
            lines.append('<td>%(name)s:</td><td><input name="%(name)s" value="%(value)s" /></td>' % d)
            lines.append('</tr>')
        lines.append('</table>')
        lines.append('<input type="submit" />')
        lines.append('</form>')

        form = '\n'.join(lines)

        html = htmltemplate % locals() # fill %(form)s
        print html

    def action(self):
        """ Returns value of request action parameter if any. """
        return self.form.getfirst('action', '')

    def shouldPrintPageHeadAndFoot(self):
        a = self.action()
        if a in ['call']:
            return False
        return True

    def printError(self, msg):
        """ Prints to stdout (created html page) error message """
        print 'ERROR: ' + msg


    def run_cmd(self, cmdline='', input=''):
        """ Runs cmdline (name of the application with parameters).
            If input specified, feeds it to the running application.

            Return text containing the following sections (specified on
            the beggining of line):
            OUTPUT=
            ERRORS=
            RESULT=

            output is list of text lines written by the appname to the
            standard output (None or [] if no output generated),

            errors is list of text lines written by the appname to the
            standard error output (None or [] if no errors generated by the
            application)

            result is the overall result code of the application (0 is OK)
            resultmsg is the message connected to the result.

        """

        result = 0
        resultmsg = ''
        output = None
        errors = None



        if not hasattr(os, 'popen3'):
            os.system(cmd)
            #os.spawnv(os.P_WAIT, run, [])
            return 'Command %s executed.' % cmd

        try:
            cin, cout, cer = os.popen3(cmdline, 'b')

            if input:
                cin.write(input)
            cin.close()

            output = cout.readlines()

            errors = cer.readlines()
            cer.close()
            r = cout.close()
            if r:
                result = r;
        except:
            if not result:
                result = -1

        l = []
        if output:
            l.append('OUTPUT=' + '\n'.join(output))
        if errors:
            l.append('ERRORS=' + '\n'.join(errors))
        l.append('RESULT=' + str(result))
        return '\n'.join(l)


    #==== print_XXX functions called as a response to action=XXX request ====
    #they should print response html page
    def print_run(self):
        """ Called when query parameter 'action'= 'run'
    'cmd' query parameter must then specify the command line to be
    executed.
        """
        cmd = self.form['cmd'].value
        print '<pre>'
        print self.run_cmd(cmd)
        print '</pre>'

    def print_call(self):
        """Called from printContent when action=call.

    Query parameters "module" and "function"
    must be specified. Then the given "module" will be imported
    and its function "function" will be called.

    The keyword parameters of the function will be constructed from
    the request variable names as the keys and their text values as the
    values.

    "format" query parameter can be specified with value "fs", then
    the function keyword parameters will be constructed from request
    variable names and CGI FieldStorage objects as the values.
    Values of the variables can then be obtained from .value attribute
    of the FieldStorage object. This is useful especially for uploaded
    files (name of the uploaded file is .filename attribute and the open
    file object is .file attribute). It is also useful, if more values
    for the same variable name is expected.

    If more value for the same variable is present and the string
    format is used, then the values will be returned in one string
    separated by a value of "delim" query parameter (',' is the default).
        """

        """if self.form.getfirst('help',''):
            print getattr(self, 'print_call').__doc__
            print
            return"""

        module = self.form.getfirst('module', '')
        if not module:
            print 'No "module" specified'
            return

        fn = self.form.getfirst('function','')
        if not fn:
            print 'No "function" specified'
            return

        format = self.form.getfirst('format','s') # can be also fs
        delim = self.form.getfirst('delim',',')

        func = getModuleFunc(module, fn)
        if not func:
            return


        d = {}
        for k in self.form.keys():
            if format == 'fs':
                d[k] = self.form[k] #FieldStorage or MiniFieldStorage object, or list of those
            else:
                o = self.form[k]
                if isinstance(o, list):
                    d[k] = delim.join([e.value for e in o])
                else:
                    d[k] = o.value

        res = func(**d)




    def print_test(self):
        print 'print_test executed'

    def printMenu(self):
        print ''

    def print_info(self):
        """ Print information - values of environmental variables """
        self.printForm()
        self.printDic(os.environ, 'ENVIRON')
        self.printList(sys.argv, 'ARGV')

    def print_exit(self):
        """ Terminate the wwwcgi server.

    Exit action causes termination of the wwwcgi server
    and also makes an attempt to close the browser window (using JavaScript). """

        print 'Server terminated'
        print '<script type="text/javascript">window.close()</script>'

    def print_edit(self):
        """ Return html form for editing variables

    The variables are specified in the list of dictionaries returned by
    the function "update" (or other function which name is specified by optional
    "function" query parameter) of module specified as the value of "module" query
    parameter. See wwwcgi variable for example of the fields definition list.
    The mandatory keywords are 'name', 'value', optional 'caption', 'hint'.
    """
        self.printListOfDictForm()
        if self.debug:
            self.print_info()
    #==== /print_XXX ====

    def url(self):
        return 'http://localhost%s/wwwcgi.py' % self.port()

    def port(self):
        return ':' + str(os.environ.get('SERVER_PORT',0))

    def printContentMenu(self):
        actions = [
            ('info', 'Info', self.url() + '?action=info'),
            ('run','Run command', '?action=run&cmd=dir%20/b'),
            ('edit', 'Edit Dict', self.url() + '?action=edit&module=wwwcgi&function=update'),
            ('exit','Exit', self.url() + '?action=exit'),
            ('call','Call Python module function', self.url() + '?action=call&module=wwwcgi&function=wwwcgi_function&param=ParamValue'),
        ]
        print '<ul>'
        for a, n, e in actions:
            print '<li>'
            print '%s <a href="%s?action=%s&help=1">Help</a>' % (n, self.url(), a)
            if e:
                print ' <a href=%s>Example</a>' % e
            print '</li>'

        print '</ul>'
        print

    def printBodyHead(self):
        pass

    def printContent(self):
        #if self.debug:
        #    self.run_cmd('xunzip xx')
        #    return

        a = self.action()
        if not a:
            self.printContentMenu()
        else:
            fnname = 'print_' + a
            fn = getattr(self, fnname, None)
            if fn:
                """ Calling print_XXX function, where XXX=a (i.e. name of the action)"""

                if self.form.getfirst('help',''):
                    #print '"run" action parameters: ...'
                    print '<h1>wwwcgi.cgibase.%s</h1>' % fnname
                    print '<p>'
                    print '<pre>'
                    print fn.__doc__
                    print '</pre>'
                    print '</p>'
                else:
                    fn()
                    #eval('self.%s()' % fnname)
            else:
                self.printError('Action %s does not have defined metod %s' % (a, fnname))

    def printBodyFoot(self):
        pass

    def printForm(self):
        print 'Form<ul>'
        for k in self.form.keys():
            print '<li>' + self.form[k].name + '=' + self.form[k].value + '</li>'
        print '</ul>'

        #user = form.getfirst("user", "").toupper()    # This way it's safe.
        """

        if not (form.has_key("name") and form.has_key("addr")):
            print "<H1>Error</H1>"
            print "Please fill in the name and addr fields."
            return
        print "<p>name:", form["name"].value
        print "<p>addr:", form["addr"].value


        value = form.getvalue("username", "")


        if isinstance(value, list):
            # Multiple username fields specified
            usernames = ",".join(value)
        else:
            # Single or no username field specified
            usernames = value


        fileitem = form["userfile"]
        if fileitem.file:
            # It's an uploaded file; count lines
            linecount = 0
            while 1:
                line = fileitem.file.readline()
                if not line: break
                linecount = linecount + 1

        #More compact common access to elements (of any type - single/multi):
        user = form.getfirst("user", "").toupper()    # This way it's safe.
        for item in form.getlist("item"):
            do_something(item)

        """
        return False

    def printPageHead(self):
        print "Content-Type: text/html"     # HTML is following
        print                               # blank line, end of headers
        if self.shouldPrintPageHeadAndFoot():
            print '<html><head><title>' + self.title + '</title>'
            self.printInTagHead()
            print '</head><body>'

    def printInTagHead(self):
        pass

    def printPageBody(self):
        self.printBodyHead()
        self.printContent()
        self.printBodyFoot()

    def printPageFoot(self):
        if self.shouldPrintPageHeadAndFoot():
            print '</body></html>'

    def begin(self):
        pass

    def end(self):
        pass

    def run(self):
        import cgi
        import cgitb
        cgitb.enable() # displays errors to browser
        #cgitb.enable(display=0, logdir="/tmp") #logs errors to file
        self.form = cgi.FieldStorage()
        self.debug = self.form.getfirst('debug', 0)
        self.begin()
        self.printPageHead()
        self.printPageBody()
        self.printPageFoot()
        self.end()


def runcgi():
    cgibase().run()

def isport(s):
    try:
        i = int(s)
    except:
        i = 0
    return i

def wwwcgi_function(**kw):
    """ Example of module function which can be called from web browser using:

http://localhost:8000/wwwcgi.py?action=call&module=wwwcgi&function=wwwcgi_function&param=ParameterValue

Such function can by defined in any python module and can contain just this
function, which has to print (using print commands and html tags) the html
page which will be returned to the browser. The kw parametr contains also
all parameters from the eventual submitted web form which you construct using
the print commands. See wwwcgi_app.py for more detailed example.
    """
    print '<br />'
    for k in kw:
        print '%s=%s<br />'% (k, kw[k])


if __name__ == '__main__':
    if (len(sys.argv) == 2) and (isport(sys.argv[1])):
        runwww(port=int(sys.argv[1]))
    else:
        runcgi()
