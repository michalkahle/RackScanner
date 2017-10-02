import os
import sys
import datetime

import urllib2_file # modifies urllib2.HTTPHandler and HTTPSHandler for uploading files
import urllib2
import urllib
import base64


# fill these in

#addfileurl='http://yourzopehost/some/dir/manage_addFile'
useragent="uploadfile.py/0.1"
#filename='test.jpg'
#filetitle='a nice test picture'


class MyUrlOpener(urllib.FancyURLopener):

    def prompt_user_passwd(self, host, realm):
        return (self.user, self.password)

    def __init__(self, *args, **kwargs):
        self.version = useragent
        self.user = kwargs.get('user','')
        self.password = kwargs.get('password','')
        urllib.FancyURLopener.__init__(self, *args)

class Uploader(object):
    def __init__(self, url, user='', password='', filebodyfield='file', okmsg='', errdir='', printmsgs=True, addauth=True):
        self.url = url
        self.user = user
        self.password = password
        self.filebodyfield = filebodyfield
        self.okmsg = okmsg
        self.errdir = errdir
        self.printmsgs = printmsgs
        self.addauth = addauth 
        #.. add authorization data (user,password) also to the POST data?
        #   if False only authorization header is created

        self.result = ''
        if not self.errdir:
            self.errdir = os.path.abspath(os.path.dirname(__file__))

        """ This junk does not work... just see setting auth to header in upload method
        #from ptyhon help for urllib2 - Examples
        #and from:
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/305288

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, self.url, self.user, self.password)
        auth_handler = urllib2.HTTPBasicAuthHandler(passman)
        #auth_handler.add_password('realm','host','username','password')
        opener = urllib2.build_opener(auth_handler)

        #opener can be used to open the url or installed to urllib2, so that
        #all subsequent urllib2.urlopen calls use this opener:
        urllib2.install_opener(opener)
        """

    def uploadOld(self, filename):
        # use authentication and set the user agent
        urllib._urlopener = MyUrlOpener(user=self.user, password=self.password)
        #urllib._urlopener.user = self.user
        #urllib._urlopener.password = self.password


        # read the contents of filename into filebody
        f = open(filename, 'rb')
        filebody = f.read()
        f.close

        # urlencode the id, title and file
        dic = {self.filebodyfield: filebody}
        dic['user_name'] = self.user
        dic['password'] = self.password

        params = urllib.urlencode(dic)

        # send the file to the server
        f=urllib.urlopen(self.url, params)
        print(f.read())


    def upload(self, filename):
        """Upload the file to the self.url.
        Return '' upon success otherwise the error message.
        """

        #build data to be useable with connection to urllib2_file module
        fd = open(filename, 'rb')
        data = {
            self.filebodyfield : fd,
            'import_type' : 'rack',
            'background' : 'on',
            'upload_all' : 'on'
        }

        if self.addauth:
            #put the user login info into post data, just for the case
            #the authentication header (see below) does not get to the django app
            data['user_name'] = self.user
            data['password'] = self.password
        print data
        req = urllib2.Request(self.url, data, {})

        #authentication header:
        base64string = base64.encodestring('%s:%s' % (self.user, self.password))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
        errmsg = ''
        buf = '' # response returned from the upload url
        try:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            u = urllib2.urlopen(req)
        except urllib2.HTTPError, errobj:
            errmsg = "HTTPError: %s. Uploading of %s to %s failed." % (errobj.code, filename, self.url)
        else:
            buf = u.read()
            if self.okmsg:
                if not (self.okmsg in buf):
                    fn = self.save_error_file(buf)
                    errmsg = "Error: Uploading of %s to %s failed. Text '%s' not present in the returned data (saved to %s)." % (filename, self.url, self.okmsg, fn)
            else:
                if buf.lower().count('error') > 0:
                    fn = self.save_error_file(buf)
                    errmsg = "Error: Uploading of %s to %s failed. Text 'error' present in the returned data (saved to %s)." % (filename, self.url, fn)
                    
        self.buf = buf
        self.errmsg = errmsg
        if errmsg:
            if self.printmsgs:
                print(sys.stderr, errmsg)
            self.result = errmsg + '\n' + buf
            return errmsg
        else:
            msg = "OK: File %s uploaded to %s." % (filename, self.url)
            if self.printmsgs:
                print(msg)
            self.result = msg + '\n' + buf
            return ''
        
    def save_error_file(self, buf):
        fn = 'uploadfile-%s.err' % datetime.datetime.now().isoformat()[:19].replace(':','-')
        if self.errdir:
            fn = os.path.join(self.errdir, fn)
        if not os.path.exists(self.errdir):
            os.mkdir(self.errdir)
        f = open(fn, 'w')
        f.write(buf)
        f.close()
        return fn
        

def uploadfile(fn, url, user='', password='', filebodyfield='file', okmsg='', errdir='', printmsgs=True, addauth=True):
    """Upload content of the file specified by the file name fn
to the server using http to given url.

If access to the url requires credentials, specify them in user and password.
The name the field holding the file data (which expects the server on the given url) 
can be specified in filebodyfield.

If okmsg specified, then the response from the url is checked for the presence of this message 
and the upload is considered successful only if the okmsg is present.

Responses from the url are written to the files into the folder errdir (only if okmsg specified).

Return '' upon success, error message upon failure.

see: http://www.zopelabs.com/cookbook/1029932854
    """
    u = Uploader(url=url, user=user, password=password, filebodyfield=filebodyfield, okmsg=okmsg, errdir=errdir, printmsgs=printmsgs, addauth=addauth)
    return u.upload(fn)



def getOpts():
    """ Create option parser object, load options from command line, creates options dict and args - command line parameter (dbdefs xml file name)"""
    import optparse
    opar = optparse.OptionParser(usage="""Usage: %prog [options] FILENAME URL
  Upload the file to given URL using http. Prints "OK" on stdout if uploaded ok,
  in the case of some error prints message containing "Error" on stderr.
""")
    opar.add_option('-u', '--user', default='', help='User name for access to the server')
    opar.add_option('-p', '--password', default='', help='User password for database access')
    opar.add_option('-b', '--filebodyfield', default='file', help='Name of the form field holding content of the file')
    opar.add_option('-o', '--okmsg', default='', help='Text which should appear in returned (html) page returned after upload.')
    opar.add_option('-e', '--errdir', default='', help='Directory into which write error messages (pages not containing okmsg).')

    #opar.add_option('-l', '--load', action="store_true", help="Load the data from the last dumpfile")
    #opar.add_option('-x', '--dbdef', help="File name of the XML database structure definition file")
    #opar.add_option('-d', '--delete', action="store_true", help="Delete source files created previously by makesrc")
    #opar.add_option('-O', '--uploadonly', action="store_true", help="Do not generate the sources, just upload them to the ftp site.")
    #opar.add_option('-e', '--expimpdir', default="data", help="Local directory where database data should be exported to/imported from")
    opt, args = opar.parse_args()
    return opar, opt, args



def main():
    #test with cmd line:
    #-u USERNAME -p PASSWORD -b thefile uploadfile.py http://localhost:8082/importfile
    #-u USERNAME -p PASSWORD -b thefile -o processed... C:\Screenings\AP-0001_fi.csv http://localhost:8082/importfile
    opar, opt, args = getOpts()
    if len(args) < 2:
        opar.print_help()
    else:
        uploadfile(args[0], args[1], user=opt.user, password=opt.password,
            filebodyfield=opt.filebodyfield, okmsg=opt.okmsg)

if __name__ == '__main__':
    main()