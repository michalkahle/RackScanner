import os
import sys
import stat
import time
import datetime
import codecs
import zipfile
import new
import math
import tempfile
import glob
import logging
import StringIO
import traceback
import calendar

try:
    import win32api
except ImportError:
    win32api = None

log = logging.getLogger('jipylib.utils')
logencoding = 'utf8'

#attrdict from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/361668
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        return self[name]
    
    def __setattr__(self, name, value):
        #if hasattr(self, name):
        #    self.__dict__[name] = value
        #else:
        self[name] = value

#see: http://wiki.python.org/moin/EscapingHtml
#&amp; must be the last in the list !!
_escapes = (('"', "&quot;"), ("'", "&apos;"), (">","&gt;"), ("<", "&lt;"), ("&", "&amp;"))

def htmlEscape(txt):
    """Convert xml/html markup text to html entities

    Can use also cgi.escape()
    """
    #return txt.replace('<','&lt;')
    for t, e in _escapes:
        txt = txt.replace(t, e)
    return txt
   
def htmlUnescape(txt):
    """ Convert html entities to text """
    for t, e in _escapes:
        txt = txt.replace(e, t)
    return txt

def isoDateTime2DateTime(dt):
    """ Convert string in ISO date time format to datetime object.

Does not check delimiters, just use the numbers.
    """
    #012345678901234567890
    #2007-01-12 23:00:11
    def toint(s):
        if s:
            return int(s)
        else:
            return 0

    year = toint(dt[0:4])
    month = toint(dt[5:7])
    day = toint(dt[8:10])
    hs = dt[11:13]
    hour = toint(dt[11:13])
    minute = toint(dt[14:16])
    second = toint(dt[17:19])
    d = datetime.datetime(year, month, day, hour, minute, second)
    return d


def dateTime2FileName(dt=None):
    """Converts date/time given in dt datetime object to the
string format YYYY-MM-DD_HH-MM-SS which can be used as a part of a file name."""
    if not dt:
        dt = datetime.datetime.now()
    fn = dt.isoformat()[:19].replace('T','_').replace(':','-')
    return fn

def fileName2DateTime(fn):
    """Converts string YYYY-MM-DD_HH-MM-SS (created by the dateTime2FileName
function) to datetime object"""
    return isoDateTime2DateTime(fn)



def zipFiles(zipFn, files, srcdir='', inzipdir=''):
    """Create zip archive named zipFn, compress into it files specified in files list.

       srcdir - subpath to be removed from the beggining of files file names

       inzipdir - path to be added at the beggining of the filenames stored to the
                zipFn
    """
    res = []
    z = zipfile.ZipFile(zipFn, 'w', zipfile.ZIP_DEFLATED)
    za = os.path.normcase(os.path.abspath(zipFn))
    srcdirlen = len(os.path.join(srcdir, 'x')) - 1 #find out how much of the path to strip from to filename for the zipfile
    for f in files: # add all files from src dir to the zip archive
        fa = os.path.normcase(os.path.abspath(f))
        if fa <> za:
            inZipFn = os.path.join(inzipdir, f[srcdirlen:])  #was os.path.split(f)[1]
            z.write(f, inZipFn)
            res.append(f)
    z.close()
    return res



def unzip(zipfn, todir):
    # tries to unzip files from zipfn to directory todir, returns tuple of lists
    # of file names:  (extracted, newer, err)
    # extracted is list of files really extracted,

    # newer is list of files
    #   which were not extracted because the files of the same name existed
    #   in the todir and their modification time was more recent than the one
    #   in the archive

    # err is list of files which could not be extracted due to some error

    try:
        os.makedirs(todir)
    except:
        pass
    res = []
    newer = []
    err = []
    z = zipfile.ZipFile(zipfn)
    try:
        l = z.infolist()
        for i in l:
            try:
                fn = os.path.join(todir, i.filename)
                dd, dn = os.path.split(fn)
                if not os.path.exists(dd):
                    os.makedirs(dd)
                if os.path.exists(fn):
                    if os.stat(fn).st_mtime > time.mktime(i.date_time + (0, 0, -1)):
                        s = 'Local file %s is newer than the file from backup, not changed.' % fn
                        log.error(s)
                        newer.append(fn)
                        continue
                try:
                    t = time.mktime(i.date_time + (0, 0, -1))
                except:
                    log.error('time.mktime failed. Ignored.' + fn)
                if fn[-1] in '/\\':
                    try:
                        os.makedirs(fn)
                    except:
                        pass
                    try:
                        os.utime(fn[:-1], (t, t))
                        log.info('os.utime for dir succeeded. ' + fn)
                    except:
                        log.error('os.utime failed. Ignored. ' + fn)
                else:
                    try:
                        if os.path.exists(fn):
                            omode = os.stat(fn).st_mode
                            modeChanged = (omode & stat.S_IWUSR) == 0
                            if modeChanged:
                                try:
                                    os.chmod(fn, omode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                                except:
                                    modeChanged = False
                                    log.error('Could not change mode to writable for %s.')
                        else:
                            modeChanged = False

                        f = open(fn, 'wb')
                        try:
                            f.write(z.read(i.filename))
                        finally:
                            f.close()
                        res.append(fn)
                        os.utime(fn, (t, t))

                        if modeChanged:
                            os.chmod(fn, omode)
                    except:
                        log.error('Could not write to file %s, skipped.' % fn)
                        err.append(fn)

            except:
                log.error('File failed: ' + i.filename)
    finally:
        z.close()

    return res, newer, err

def overwriteFile(filename, data, encoding=None):
    """Overiwrites the file of given pathname (fn) with the data, but creates
first a backup copy of the existing file with .bak extension.

If encoding <> None, then data are expected to be unicode and the encoding will
be used to encode the data written to the file.

    """
    base, ext = os.path.splitext(filename)
    bak = base + ext + '.bak'
    tmp = base + ext + '.tmp' # write to temporary file first
    if os.path.exists(tmp):
        #remove previously used temporary file
        os.remove(tmp)
    #write to the temporary file the new content
    f = codecs.open(tmp, 'w', encoding)
    try:
        f.write(data)
    finally:
        f.close()
    if os.path.exists(filename):
        if os.path.exists(bak):
            #remove previous version backup file
            os.remove(bak)
        #rename the file to be overwriten using backup file name
        os.rename(filename, bak)
    os.rename(tmp, filename)


def expandfn(fn, relfn=''):
    """ Try to expand file path fn (and locate the file) and return the expanded
    file name. If in Windows then in the windows short path format.

    The following folders are looked up in the given order:
        path of fn (if specified, can be relative to the current dir or relfn dir)
        path of relfn (if specified, i.e. existing file to which relative path is given; used instead of current dir)
        path of sys.argv[0]
        path of sys.argv[0]/..
        path of sys.argv[0]/../..



    """
    try:
        fp = os.path.split(sys.argv[0])[0]
        #os.path.abspath(__file__))[0]
    except:
        fp = ''

    path, base = os.path.split(fn)
    pathlist = [fp, fp + '/..', fp + '/../..']


    if relfn:
        relp, relb = os.path.split(relfn)
        if path:
            path = os.path.join(relp, path)
        else:
            path = relp
    else:
        path = os.path.split(os.path.abspath(fn))[0]


    if path:
        pathlist.insert(0, path)

    for p in pathlist:
        fn = p + '/' + base
        if os.path.exists(fn):
            return os.path.abspath(fn)

    #file not found, so return filename of the file to be created
    if relfn:
        #if it should be relative to some other file, take the relative's file path
        fn = os.path.join(path, base)
    else:
        fn = os.path.abspath(fp + '/' + base)
    
    if win32api:
        try:
            fn = win32api.GetShortPathName(fn)
        except:
            pass
    return fn

def findFileInParentFolders(fn, folder=''):
    """Try to locate file of given file name in specified folder and its
parent folders. If no folder given, current dir is used. Returns the
absolute file name if found, otherwise return '' """
    if not folder:
        folder = os.getcwd()

    while True:
        lastFolder = folder
        nfn = os.path.join(folder, fn)
        if os.path.exists(nfn):
            return nfn
        folder, x = os.path.split(folder)
        if folder == lastFolder:

            return ''
#http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/229472
#see also:
#  http://mail.python.org/pipermail/python-list/2006-January/364427.html
#  http://www.python.org/dev/peps/pep-0309/
#
def partial(func, *args):
    if not len(args):
        return func
    arg = args[0]
    curried = new.instancemethod(func, arg)
    return partial(curried, *args[1:])

"""pep solution - works also with keyword arguments (included in Python2.5 functools module):
class partial(object):

    def __init__(*args, **kw):
        self = args[0]
        self.fn, self.args, self.kw = (args[1], args[2:], kw)

    def __call__(self, *args, **kw):
        if kw and self.kw:
            d = self.kw.copy()
            d.update(kw)
        else:
            d = kw or self.kw
        return self.fn(*(self.args + args), **d)
"""

def frexp10(num, digits=None):
    """Return (mantissa, exponent) tuple in base 10 for number num.

See math.frexp for the same in base 2.
    """
    if not num:
        return 0, 0
    
    n = math.log10(num)
    f, e = math.modf(n) # 10**f * 10**e = num; f - fractinal part, e - integer exponent
    if digits is not None:
        return round(10**f, digits), int(e)
    else:
        return 10**f, int(e)

def frexp10str(num, digits=None):
    """Return tuple of string representations of (mantissa, exponent),
mantissa rounded (cat) to digits number of decimal digits."""
    if not num:
        return '0','0'
    m, e = frexp10(float(num), digits)
    if digits is not None:
        frm = '%.' + str(digits) + 'f'
        return frm % m, str(e)
    else:
        return str(m), str(e)

def tempDirCreate():
    """Create temporary folder, return its path"""
    tmpdir = tempfile.mkdtemp()
    return tmpdir

def tempDirDestroy(tmpdir):
    """Destroy temporary folder. Remove all files in it first. (not recursive yet)"""
    if not os.path.exists(tmpdir):
        return
    try:
        for f in glob.glob(tmpdir + '/*.*'):
            os.remove(f)
        os.rmdir(tmpdir)
    except:
        pass
        #raise Exception('tempFolderDestroy Error (%s, %s)' % sys.exc_info()[:2])
        #import shutil
        #shutil.rmtree(self.tmpdir)
        #os.rmdir(self.tmpdir) # dir must be empty for this call
        
def catchLogBegin(log, level=logging.INFO):
    """Start capturing log messages on given logger for given or higher log level to StringIO

Return handler which should be used as a parameter to catchLogEnd

Use catchLogEnd to end the captchering and get the log text.
    """
    h = logging.StreamHandler(StringIO.StringIO())
    h.setLevel(level)
    log.addHandler(h)
    return h

def catchLogEnd(log, handler):
    """End captchuring of log messages from given log by the handler.
    
handle is the object returned by catchLogBegin function. 

Return the log text. Caller should del(handler) if stored somewhere persistently.
    """
    log.removeHandler(handler)
    return handler.stream.getvalue()


def get_exc_info_short():
    a, b, tb = sys.exc_info()
    while 1:
        #find the innermost frame
        if not tb.tb_next:
            break
        tb = tb.tb_next
    frame = tb.tb_frame
    return "%s, %s. Frame %s in %s at line %s" % (a, b, frame.f_code.co_name, frame.f_code.co_filename, frame.f_lineno)
    
def get_exc_info():
    """Print the usual traceback information, followed by a listing of
    all the local variables in each frame.
    """

    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()

    exc_str = traceback.format_exc()
    exc_str += '\nLocals by frame, innermost last:'
    for frame in stack:
        exc_str += "\nFrame %s in %s at line %s" %(frame.f_code.co_name,frame.f_code.co_filename,frame.f_lineno)
        for key, value in frame.f_locals.items():
            exc_str += "\n\t%20s = " % key
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error we don't want.
            try:
                exc_str += str(value)
            except:
                exc_str += 'ERROR WHILE PRINTING VALUE'
    return exc_str.replace('<',' ').replace('>', ' ') # to be used in xml docs

def getModuleAttr(module_dotted_name, attr=None, log_missing=True):
    """Return attribute (function, class, variable, ...) of given module. Import the module if necessary.
    
    If not attr specified, it is expected to be the last part of the module_dotted_name.
    
    If logNone then log the missing module/attribute.
    """
    mod = module_dotted_name
    fun = attr
    if not fun:
        parts = mod.split('.')
        mod = '.'.join(parts[:-1])
        fun = parts[-1]
        
    try:
        md = __import__(mod, globals(), locals(), [fun]) #try to import the module
    except ImportError:
        if log_missing:
            log.warning('getModuleAttr: module %s not found.' % mod)
        return None

    if not hasattr(md, fun):
        if log_missing:
            log.warning('getModuleAttr: attribute %s not found in module %s' % (fun, mod))
        return None
    else:
        return getattr(md, fun)
    
def registerResource(path):
    """Parse path of the resource file in the format e.g. module1.submodule1/static/css/sheet.css
    /static/ substring must be present.
    Register static folder for module1.submodule1 under name 'module1.submodule1' and return tuple ('module1.submodule1', 'css/sheet.cs'),
    to be used e.g. for turbogears CSSLink or JSLink

    """
    from pkg_resources import resource_filename
    from turbogears.widgets import register_static_directory
    mod, p = path.split('/static/')
    static_dir = resource_filename(mod, 'static')
    register_static_directory(mod, static_dir)
    return str(mod), str(p)

def parseParams(param):
    """Parse string containing parameters in the format "paramname=paramvalue, paramname2=paramvalue2, ...". Return dict. 
    All keys/values are returned as strings.
    """
    res = {}
    if param:
        params = [p.strip() for p in param.split(',') if p.strip()]
        for p in params:
            n, v = p.split('=', 1)
            res[str(n)] = v
    return res

def parseBrowseParams(params):
    """Parse query string in the format: param1=value1&param2=value2& ...
    return dict = {'param1':'value1', 'param2':'value2'...}
    """
    dic = {}
    if params:
        nvs = params.split('&')
        for param in nvs:
            #name=value
            nv = param.split('=', 1)
            if len(nv) == 1:
                continue
            dic[nv[0]] = nv[1]
    return dic

def decMonth(date, cnt=1):
    """Return last date of the previous month"""
    cnt = abs(int(cnt))
    month = date.month
    year = date.year
    while cnt > 0:
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        cnt -= 1
        
    fdow, daysinmonth = calendar.monthrange(year, month)
    return datetime.date(year, month, daysinmonth)

def incMonth(date, cnt=1):
    """Incerement month of the date given as month parameter.
    Day is set to the last day of the month.
    If cnt = 0, just set the day to the last day of the month.
    """
    if cnt == 0:
        year = date.year
        month = date.month
    elif cnt > 0:
        year = date.year
        month = date.month
        while cnt > 0:
            month = month + 1
            if month > 12:
                month = 1
                year += 1
            cnt -= 1
    elif cnt < 0:
        return decMonth(date, -cnt)   
    fdow, daysinmonth = calendar.monthrange(year, month)
    return datetime.date(year, month, daysinmonth)


def getDateTimeObj(dt):
    """Return datetime.datetime object instance using dt info of any format"""
    if dt:
        if isinstance(dt, basestring):
            #expect isoformat or without any -,:, ,T ...
            #YYYYMMDDHHMMSS
            #01234567890123
            dt = dt.replace(' ','').replace('-','').replace(':','').replace('T','')
            dt = datetime.datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]), int(dt[8:10].zfill(2)), int(dt[10:12].zfill(2)), int(dt[12:14].zfill(2)))
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(dt.year, dt.month, dt.day)
            
    else:
        dt = None
    return dt

def getDateObj(date):
    """Return datetime.datetime instance. Convert from whatever format the date is.
    """
    if date:
        if isinstance(date, basestring):
            date = date.replace('-','')
            date = datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8]))
    else:
        date = None
    return date

def getTimeObj(time):
    """Return datetime.time instance. Convert from whatever format the time is.
    HH[:MM[:SS]], or HH[MM[SS]]
    """
    if time:
        if isinstance(time, basestring):
            time = time.replace(':','').ljust(6,'0')
            time = datetime.time(int(time[:2]), int(time[2:4]), int(time[4:6]))
    else:
        time = None
    return time
    
def getDateStr(date, length=10):
    if date:
        if isinstance(date, basestring):
            date = date[:length]
        else:
            date = date.isoformat()[:length]
    else:
        date = ''
    return date

def logmsg(msg):
    """Create string message from the parameter, ignore any possible unicode converting errors.
    Use for messages to be logged by log methods (debug, warning, error, info)
    """
    if isinstance(msg, unicode):
        msg = msg.encode(logencoding, 'ignore')
    else:
        msg = str(msg)
    return msg

def getSubDic(dic, keys):
    """Return a new dictionary object containing only values of keys from dic"""
    d = {}
    for k in keys:
        if dic.has_key(k):
            d[k] = dic[k]
    return d

def stripdelim(s, delim='"'):
    """Strip leading/ending quotes or any delimiter from the string, if found"""
    if s.startswith(delim):
        if s.endswith(delim):
            return s[1:-1]
        else:
            raise Exception('Missing ending delimiter in %s' % s) #return s[1:]
    else:
        #if s.endswith(delim)
        return s

def envreplace(s):
    """Replace any occurence of %XXX% with the value of XXX environmental variable
    if found. Otherwise leave as it was.
    """
    parts = s.split('%')
    newparts = []
    if len(parts) > 1:
        for i, part in enumerate(parts):
            if (i % 2 == 1):
                v = os.getenv(part)
                if v:
                    newparts.append(v)
                else:
                    newparts.append('%' + part + '%')
            else:
                newparts.append(part)
    else:
        newparts = parts

    return ''.join(newparts)
  
      
def openAnything(source):
    """URI, filename, or string --> stream

    #http://diveintopython.org/xml_processing/  toolbox.py

    This function lets you define parsers that take any input source
    (URL, pathname to local or network file, or actual data as a string)
    and deal with it in a uniform manner.  Returned object is guaranteed
    to have all the basic stdio read methods (read, readline, readlines).
    Just .close() the object when you're done with it.
    
    Examples:
    >>> from xml.dom import minidom
    >>> sock = openAnything("http://localhost/kant.xml")
    >>> doc = minidom.parse(sock)
    >>> sock.close()
    >>> sock = openAnything("c:\\inetpub\\wwwroot\\kant.xml")
    >>> doc = minidom.parse(sock)
    >>> sock.close()
    >>> sock = openAnything("<ref id='conjunction'><text>and</text><text>or</text></ref>")
    >>> doc = minidom.parse(sock)
    >>> sock.close()
    """
    if hasattr(source, "read"):
        return source

    if source == '-':
        import sys
        return sys.stdin

    # try to open with urllib (if source is http, ftp, or file URL)
    import urllib
    try:
        return urllib.urlopen(source)
    except (IOError, OSError):
        pass
    
    # try to open with native open function (if source is pathname)
    try:
        return open(source)
    except (IOError, OSError):
        pass
    
    # treat source as string
    import StringIO
    return StringIO.StringIO(str(source)) 

def file_get_contents(fn):
    """php like function to return content of the file/url specified. 
    If no file/url found or error occurred during attempt to read it, return the fn itself.
    """
    f = openAnything(fn)
    data = f.read()
    f.close()
    return data

def file_put_contents(fn, data, mode='wb', encoding='utf-8'):
    """php like function to write content to the file
    
    Try to add number to filename and retry if attempt to open it fails.
    """
    cnt = 0
    retry_count = 5 # retry this number of times
    ofn = fn
    if isinstance(data, unicode):
        data = data.encode(encoding)
    while cnt <= retry_count:
        try:
            f = open(fn, mode)
            f.write(data)
            f.close()
            break
        except:
            cnt += 1
            path, base_ext = os.path.split(ofn)
            base, ext = os.path.splitext(base_ext)
            fn = os.path.join(path, base + ('(%s)' % cnt) + ext)
            

def sort_files(files, stat_names=['st_mtime'], reverse=False):
    """Sort given list of file names by the file properties obtained from os.stat.
    
    Evailable stat names:
    
    st_mode ... protection bits
    st_ino  ... inode number
    st_dev  ... device
    st_nlink... numbef or hard links
    st_uid  ... user id of owner
    st_gid  ... group id of owner
    st_size ... size of the file in bytes
    st_atime... time of most recent access
    st_mtime... time of most recent content modification; use time.localtime() to get tuple 
                (yyyy, m(1-12), d(1-31), h(0-23), m(0-59), s(0-59), weekday(0-6, 0 is Mo), julian day(1-366), DST(-1,0,1))
    st_ctime... time of the file creation (windows), time of the most recent metadata change (unix)
    
    Return the sorted list if file names.
    """
    dl = []
    for fn in files:
        item = []
        s = os.stat(fn)
        for stat_name in stat_names:
            item.append(getattr(s, stat_name))
        item.append(fn)
        dl.append(item)
    dl.sort(reverse=reverse)
    return [item[-1] for item in dl]
