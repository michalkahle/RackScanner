import sys
import os
import logging
import datetime
import threading
import glob
import urllib
import shutil

from jipylib import  utils #twainutl, inifile, winkeys, uploadfile,
#from jipylib.xpil import imgmatrix
import imp
imgmatrix = imp.load_source('imgmatrix', 'lib/jipylib/xpil')

# import buttonman

#ROOT = os.path.dirname(__file__)

#the root/home folder for the platscan software should be in the directory 
#where the platescan_start.py script (starting the platescan app) is located
ROOT = os.path.abspath(os.path.dirname(sys.argv[0])) #os.path.abspath(os.curdir)

PROJECT_TITLE = 'RackScanner'
VERSION = '1.1'

TITLE = 'RackScanner Client'
#CLIENT_TITLE = TITLE + ' Client'

INI_FILENAME = 'platescan.ini'
INIFOLDERS = [ROOT, os.path.dirname(imgmatrix.__file__)]
URL = 'http://%(hostname)s:%(port)s/wwwcgi.py?action=call&module=platescan&function=main'
EXIT_URL = 'http://%(hostname)s:%(port)s/wwwcgi.py?action=exit'
JQUERY_URL = 'http://code.jquery.com/jquery.min.js'
JS_URLS = [JQUERY_URL, '/js/platescan.js','/js/jijslib.js']

CSS_URL = '/css/platescan.css'


def checksubdir(sub):
    subdir = os.path.join(ROOT, sub)
    if not os.path.exists(subdir):
        os.mkdir(subdir)
    return subdir
        
BMPDIR = checksubdir('bmp') # where the scanned image files should be stored
CSVDIR = checksubdir('csv') # where the csv files with samples barcodes should be stored
LOGDIR = checksubdir('log') # where log files should be stored

DEMODIR = os.path.join(ROOT, 'demo') # where demo/example files are placed

ROWS = [chr(ord('A') + i) for i in range(8)] #['A','B','C','D','F','G','H']
COLS = [str(i+1) for i in range(12)] # ['1','2', ..., '12']

log = logging.getLogger()
logfile = os.path.join(LOGDIR, 'platescan_%s.log' % datetime.date.today())
log.addHandler(logging.FileHandler(logfile))

head_template = """
<html>
<head>
<title>%(title)s</title>
%(js)s
%(css)s
</head>
<body>
<h1>%(project_title)s %(version)s</h1>
<div id="main">
<div class="clear menu">
<a id="home" class="button" href="%(url)s"><span>Home</span></a>
<a id="ready" class="button" href="#"><span>Get Ready</span></a>
<!-- <a id="exit" class="button" href="%(exit_url)s"><span>Exit</span></a> -->
</div>
"""

foot_template = """
</div>
</body>
</html>
"""

form_template = """
<h2>Parameters</h2>
<form name="scan" method="get">
  <table class="form">
    <tr>
      <td class="label">Plate barcode</td><td><input id="platebarcode" name="platebarcode" type="%(platebarcode)s" /></td><td class="hint">(None for new plate)</td>
    </tr>
    <tr>
      <td class="label">Server upload url</td><td><input name="uploadurl" type="text" value="%(uploadurl)s"/></td><td class="hint">To what URL upload the scanned .csv file. Useful mainly if you run ChemGenDB server and "Plate barcode" is specified.</td>
    </tr>
    <tr>
      <td class="label">Server user name</td><td><input name="user" type="text" value="%(user)s"/></td><td class="hint">User name for connection to the upload server.</td>
    </tr>
    <tr>
      <td class="label">Server user password</td><td><input name="password" type="text" value="%(password)s"/></td><td class="hint">Password for the connection to the upload server</td>
    </tr>
    <tr>
      <td class="label">Server upload field</td><td><input name="uploadfield" type="text" value="%(uploadfield)s"/></td><td class="hint">Name of the form field used at the upload URL which holds the name of the .csv file.</td>
    </tr>
    <tr>
      <td class="label">Scanner</td><td><input name="scanner" value="%(scanner)s" /></td><td class="hint">Model of the used scanner.</td>
    </tr>
    <tr>
      <td class="label">Application name</td><td><input name="appname" value="%(appname)s" /></td><td class="hint">To which application send the scanned single vial barcode (using keyboard buffer). Here entered word(s) must appears in the application window title. The application must be already running!!! </td>
    </tr>
    <tr>
      <td class="label">Display image</td><td><input type="checkbox" name="displayimage" %(displayimage)s /></td><td class="hint">Display the scanned image when scanning is finished?</td>
    </tr>
    <tr>
      <td class="label">Open csv file</td><td><input type="checkbox" name="opencsv" %(opencsv)s /></td><td class="hint">Open the .csv file containing the vial barcodes in the rack when scanning is finished?</td>
    </tr>
    
  </table>
       
  %(plate)s
  
  <h2>Commands:</h2>
  <table>
  <tr>
    <td><input type="submit" id="scanrack" name="scanrack" value="Scan Rack" /> </td>
    <td>Scan the whole rack of barcoded tubes. The same function as the right scanner button.</td>
    <td class="hint">Place the rack to the upper left corner or the scanning area, rack manufacturer labels facing you, then click "Rack" or press the scanner right button.</td>
  </tr>
  <tr>
    <td> <input type="submit" id="scanvial" name="scanvial" value="Scan Single Tube" /></td>
    <td>Scan barcode of just one tube. The same function as the left scanner button.</td>
    <td><span class="hint">Place the tube to the upper left corner, ~0.5 cm from the edges)</span></td>
  </tr>
  <tr>
    <td>Last tube barcode: </td>
    <td><span id="tubebarcode">%(lastvialbarcode)s</span> </td>
    <td><span class="hint"> Last scanned and recognized 2D barcode of single scanned vial.</span></td>
  </tr>
  <tr>
    <td>Disable "Button Manager" AVA6 Scanner files checking:</td>
    <td><input type="checkbox" id="timerdisabled" name="timerdisabled" /></td>
    <td><span class="hint">If checked, the scanner buttons invoked actions will be ignored by this application.</span></td>
  </tr>
  <tr>
    <td>Last image file name:</td>
    <td><input id="imagefilename" name="bmpfilename" value="" size="80" /></td>
    <td class="hint">... paste here full path name of the scanned image file with 2D barcodes to restart their recognition. 
        Works only if the above Disable "Button Manager" checkbox is unchecked.</td>
  </tr>
  <tr>
    <td><input type="submit" id="uploadcsv" name="uploadcsv" value="Upload CSV" /></td>
    <td></td>
    <td><span class="hint">Try to upload the last obtained .csv file to the above "Server upload url".</span></td>
  </tr>
  <tr>
    <td><input type="submit" id="runcsv" name="runcsv" value="Open CSV" /></td>
    <td></td>
    <td><span class="hint">Open the last obtained .csv file.</span></td>
  </tr>
  </table>
       
  <input type="hidden" name="action" value="call" />
  <input type="hidden" name="module" value="platescan" />
  <input type="hidden" name="function" value="main" />
  
  
  <input type="hidden" name="reload" value="%(reload)s" />
  <input type="hidden" name="submitted" value="1" />
</form>
"""

running_template = """
<html>
<head>
<meta http-equiv="Refresh" content="5; URL=%(url)s" />
<title>%(title)s</title>
%(js)s
%(css)s
<script type="text/javascript">
running = true;
</script>
</head>
<body><div id="main">
... Running ... %(message)s %(current_item)s/%(item_count)s
</div></body>
</html>
"""

_thread = None
_parser = None

INI_DEFAULTS = [ # to be saved to ini
    ('uploadurl', 'http://db.chemgen.cz/upload'),
    ('uploadfield', 'thefile'),
    ('user','uploader'),
    ('password','ccguploader'),
    ('scanner', 'AVA6'),
    #('platebarcode', ''),
    ('reload', ''),
    ('inifile','avision-600.ini'),
    ('inifile_vial','avision-600-vial.ini'),
    ('port', '8080'),
    ('hostname','localhost'),
    ('imagemagick', "imgmatrix.IMAGE_MAGICK"), # installation subfolder will be searched for in %ProgramFiles%, %ProgramFiles(x86)% 
    ('appname', 'Microsoft Excel'),
    ('opencsv', 'checked'),
]

RUN_DEFAULTS = [
    ('platebarcode',''),
    ('lastvialbarcode',''),
]

class PlateScanner(object):
    def __init__(self, **kwargs_):
        kwargs = inifile.load(INI_FILENAME, INIFOLDERS)
        
        kwargs.update(kwargs_)
        
        self.set_defaults(kwargs)
        kwargs['js'] = ''
        for jsurl in JS_URLS:
            kwargs['js'] += """    <script type="text/javascript" src="%s" ></script>""" % jsurl
        kwargs['css'] = """
    <link type="text/css" rel="stylesheet" media="all" href="%s" />
        """ % CSS_URL
        kwargs['title'] = TITLE
        kwargs.setdefault('url', URL % kwargs)
        kwargs.setdefault('exit_url', EXIT_URL % kwargs)
        kwargs.setdefault('error', '')

        
        kwargs['plate'] = '' # source code for the plate - samples barcodes; created during parsing the scanned image
        
        #on/off params (checkboxes in html):
        if kwargs_.get('submitted'):
            for cb in ['displayimage','opencsv']:
                if not kwargs_.get(cb):
                    #not specified in incoming request parameters (overrides eventual ini)
                    kwargs[cb] = ''
        for cb in ['opencsv','displayimage']:
            #make sure for checkbox parameters to have the correct value format for the html form
            if kwargs.get(cb):
                kwargs[cb] = 'checked'
            else:
                kwargs[cb] = ''

        kwargs['project_title'] = PROJECT_TITLE
        kwargs['version'] = VERSION
        
        self.kwargs = kwargs
        self.unquote_kwargs()
        
        self.wells = {}
        self.bmpfilename = kwargs.get('bmpfilename')
        # if bmpfilename supplied, scanning will be skipped and the image parsed
        self.messages = []
        self.errors = []
        
        try:
            log.setLevel(int(kwargs.get('loglevel', 20)))
        except:
            pass

    def save_ini(self):
        """Save only current values of keys defined in INI_DEFAULTS to ini file"""
        d = {}
        for k, v in INI_DEFAULTS:
            d[k] = self.kwargs.get(k, v)
        inifile.save(d, INI_FILENAME, INIFOLDERS)
        
    def set_defaults(self, kwargs):
        for k, v in INI_DEFAULTS + RUN_DEFAULTS:
            kwargs.setdefault(k, v)
            
    def unquote_kwargs(self, keys=['bmpfilename','uploadurl','error']):
        """Eventual %xx encoded chars get replaced back by urllib.unquote"""
        for k in keys:
            if self.kwargs.get(k):
                self.kwargs[k] = urllib.unquote(self.kwargs[k])
                
    def log(self, message, level=logging.INFO):
        log.log(level, message)
        if level > logging.INFO:
            self.errors.append(message)
        else:
            self.messages.append(message)
        
    def display_form_page(self):
        print head_template % self.kwargs
        self.display_messages()
        self.display_form()
        print foot_template % self.kwargs
        
    def display_messages(self):
        
        errors = ''
        if self.errors:
            errors += '<br />'.join(self.errors)
        if self.kwargs.get('error'):
            errors += '<br />' + self.kwargs['error']
        if errors:
            print '<div id="error">%s</div>' % errors
            
        if self.messages:
            print '<ul id="messages">\n'
            for m in self.messages:
                print '<li>%s</li>' % m
            print '</ul>'
            
    def display_form(self):
        print form_template % self.kwargs
        
    def display_running(self):
        self.kwargs['message'] = _parser._message
        self.kwargs['current_item'] = _parser._current_item
        self.kwargs['item_count'] = _parser._item_count
        self.kwargs['url'] = URL % self.kwargs
        print running_template % self.kwargs

    def scan_image(self, **kwargs):
        """Run the scanner for the plate. Wait for the result.
        
        The image filename is stored to self.bmpfilename upon success (or None if failed)
        """
        what = kwargs.pop('what') # 'rack' or 'vial'
        
        kwargs.setdefault('folder', BMPDIR)
        kwargs.setdefault('resolution', 600.0)
        kwargs.setdefault('displayimage', self.kwargs.get('displayimage'))
        
        kwargs.setdefault('filemask', what + '%Y%m%d%H%M%S.bmp')
        try: 
            start = datetime.datetime.now()
            # c = twainutl.TwainCtl(**kwargs)
            # c.run()
            stop = datetime.datetime.now()
            print 'Scanned to file: %s (%s) <br />' % (c.filename, stop - start)
            self.bmpfilename = c.filename
        except:
            msg = 'TwainCtl Error: (%s, %s)' % sys.exc_info()[:2]
            self.log(msg, logging.ERROR)
            print msg

    def run_vial_parser(self):
        """Try to find one vial barcode in the scanned image"""
        dic = self.inipars
        dic['filemask'] = self.bmpfilename
        dic['csvdir'] = CSVDIR 
        parser = imgmatrix.ImgMatrix(**dic)
        crb = parser.read_barcode(self.bmpfilename)
        if crb and crb[2]:
            self.log('run_vial_parser - barcode found in %s: %s. Sending to app: %s' % (self.bmpfilename, crb[2], self.inipars['appname']))
            
            self.kwargs['lastvialbarcode'] = crb[2]
            prefix = self.kwargs.get('vialprefix', '') # was ^a, now in .ini
            suffix = self.kwargs.get('vialsuffix','') # was '', can modify to {ENTER} if needed
            s = prefix + crb[2] + suffix
            if not winkeys.send_keys(s, self.inipars['appname']):
                self.log('Failed to send keys to app %s' % self.inipars['appname'], logging.WARNING)
            self.log('send_keys: %s' % s)
        else:
            self.log('run_vial_parser = no barcode found in %s' % self.bmpfilename)
        
    def start_parser(self):
        """Start parser (in the thread) for all vials in the plate"""
        global _parser, _thread
        dic = self.inipars
        dic['filemask'] = self.bmpfilename
        dic['csvdir'] = CSVDIR #datadir ?
        dic['opencsv'] = self.kwargs['opencsv']
        try:
            self.save_ini() # to get back the kwarg values set at the time of starting the parser
            _parser = imgmatrix.ImgMatrix(**dic)
            _parser.platebarcode = self.kwargs.get('platebarcode')
            _thread = threading.Thread(target=_parser)
            _thread.start()
        except:
            msg = 'ImgMatrix Error: (%s, %s)' % sys.exc_info()[:2]
            self.log(msg, logging.ERROR)
            print msg
            _parser = None
            _thread = None

    def finish_parser(self):
        global _parser, _thread
        if _parser:
            for x, y, barcode in _parser._barcodes:
                #depending on how the plate is positioned on the scanner, create a key which always starts with a letter (A1, A2, ...)
                if _parser.rowtype == '1':
                    key = y + x
                else:
                    key = x + y
                self.wells[key] = barcode
            
            #create a new name for the csv file, just to be sure the file name
            #of the uploaded file has always the same format
            base = 'rack-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
            if _parser.platebarcode:
                #if platebarcode specified, add it at the end of the base name 
                #separated by '_'
                base += '_' + _parser.platebarcode
            csvfilename = os.path.join(CSVDIR,  base + '.csv')
            if os.path.abspath(_parser.csvfilename) != os.path.abspath(csvfilename):
                shutil.move(_parser.csvfilename, csvfilename)
            self.log('Barcodes written to file: <a href="file:///%s">%s</a><br />' % (csvfilename, csvfilename))
            
            if self.kwargs['opencsv']:
                os.system('start "%s" "%s"' % (csvfilename,csvfilename))
                
            self.uploadcsv(csvfilename)
            
            self.hide_bmpfile(_parser.filename)
        _parser = None
        _thread = None

    def _get_last_csv_file(self):
        filename = None
        files = glob.glob(os.path.join(CSVDIR, '*.csv'))
        if not files:
            self.log('No csv files found in %s' % CSVDIR)
        else:
            files = utils.sort_files(files)
            filename = files[-1]
        return filename
    
    def uploadcsv(self, filename=None):
        """Upload specified file to the server."""
        uploadurl = self.kwargs.get('uploadurl')
        if not uploadurl:
            self.log('No url specified for csv file %s upload.' % filename)
        else:
            if filename is None:
                #can be None if testing, then find the last csv file created
                filename = self._get_last_csv_file()
            #fn, url, user='', password='', filebodyfield='file', okmsg='', errdir=''):
            try:
                u = uploadfile.Uploader(url=uploadurl, user=self.kwargs['user'], password=self.kwargs['password'], 
                                        filebodyfield=self.kwargs['uploadfield'], printmsgs=False)
                er = u.upload(filename)
                #er = uploadfile.uploadfile(filename, uploadurl, user=self.kwargs['user'], password=self.kwargs['password'], filebodyfield=self.kwargs['uploadfield'])
                if er:
                    self.log('File %s upload to %s failed: %s' % (filename, uploadurl, er), logging.ERROR)
                else:
                    self.log('CSV file %s uploaded to %s' % (filename, uploadurl))
                self.log(u.buf)
            except:
                self.log('Failed to upload CSV file %s to %s (%s, %s)' % (filename, uploadurl, sys.exc_info()[0], sys.exc_info()[1]), logging.ERROR)
            
    def run_csv(self):
        filename = self._get_last_csv_file()
        if filename:
            os.system('start "%s" "%s"' % (filename, filename))
        self.display_form_page()
        
    def hide_bmpfile(self, filename=None):
        """Hide parsed bmp file to backup folder"""
        if not filename:
            filename = self.bmpfilename
        if os.path.exists(filename):
            try:
                buttonman.ButtonMan().hide_file(filename)
                self.kwargs['bmpfilename'] = ''
            except:
                self.log('ERROR: Failed to hide file %s (%s, %s)' % (filename,) + tuple(sys.exc_info[:2]), logging.ERROR)
        
    def run(self):
        if self.kwargs.get('scanvial'):
            self.run_vial()
        elif self.kwargs.get('uploadcsv'):
            self.run_uploadcsv()
        elif self.kwargs.get('runcsv'):
            self.run_csv()
        else:
            self.run_plate()

    def load_inipars(self, key):
        """Merge current global ini/self.kwargs parameters with the content
        of the for scanner inifile (which overwrites eventual params with the same
        name defined in kwargs), the name of which is in the kwargs[key] parameter.
        
        The result assign to self.inipars
        """
        fn = self.kwargs[key]
        self.inipars = self.kwargs.copy()
        idic = inifile.load(self.kwargs[key], INIFOLDERS)
        self.inipars.update(idic)
        
    def run_vial(self):
        """Scan just one vial barcode"""
        self.load_inipars('inifile_vial')
        
        #scanvial button pressed
        if self.bmpfilename and not os.path.exists(self.bmpfilename):
            self.bmpfilename = None # could have been removed before other platescan browser page noticed
        if not self.bmpfilename: # bmpfilename is not usually supplied (only when debugging)
            self.scan_image(what='vial', **self.inipars)
        self.run_vial_parser()
        self.hide_bmpfile(self.bmpfilename)
        self.display_form_page()
        
    def run_uploadcsv(self):
        """Upload the last csv file.
        Just for debugging purposes. The csv file gets uploaded automatically when the parser finished.
        """
        self.uploadcsv()
        self.display_form_page()
        
    def run_plate(self):
        global _parser, _thread
        self.load_inipars('inifile')
        #self.inipars = inifile.load(self.kwargs['inifile'], INIFOLDERS)
        if _parser:
            if not _parser.finished:
                self.display_running()
                return
            else:
                self.finish_parser()
        else:
            if self.kwargs.get('scanrack'):
                #scan button pressed
                if not self.bmpfilename: # bmpfilename is not usually supplied (only when debugging)
                    self.scan_image(what='rack', **self.inipars)
                
                if os.path.exists(self.bmpfilename):
                    self.start_parser()
                    self.display_running()
                    return
                else:
                    #either scan failed or just already parsed file name remained in input
                    self.kwargs['scanrack'] = ''
                    self.kwargs['bmpfilename'] = ''
                    pass

        if self.wells:
            self.create_plate()
            
        self.display_form_page()
                
            
    def create_plate(self):
        """Create html source for the plate and set it to self.kwargs['plate']
        To each ROWCOL position is assigned the barcode.
        """
        plate = ['<table class="plate">','<tr><th></th>'] + ['<th>%s</th>' % i for i in COLS] + ['</tr>\n']
        for row in ROWS:
            plate.append('<tr><td>%s</td>' % row)
            for col in COLS:
                plate.append('<td><input name="%s" value="%s" size="10" /></td>' % (row+col, self.wells.get(row+col,'')))
            plate.append('</tr>\n')
        plate.append('</table>')
        
        '''
        plate.append("""<table id="rackbuttons">
  <tr>
     <td><input type="button" id="rackadd" value="Add new rack to DB" /></td>
     <td><input type="button" id="rackupdate" value="Update rack info in DB" /></td>
  </tr>
  </table>"""
        )
        '''

        self.kwargs['plate'] = '\n'.join(plate)
        
def status(**kwargs):
    """Get status of the server and scanned images
    The text result is printed to the html page which will be returned.
    """
    
    format = kwargs.get('format', 'html') # can be also 'json'
    what = kwargs.get('what')
    
    result = ''
    if what == 'server':
        result = 'running'
    if what in ['vial', 'scan']:
        #is some vial*.* file present in the images folder?
        result = buttonman.get_latestfile("1", format) #buttonman.ButtonMan().button1.get_latestfile()
    if (what in ['rack', 'scan']) and (not result):
        #is some  rack*.* file present in the images folder?
        result = buttonman.get_latestfile("2", format) #buttonman.ButtonMan().button2.get_latestfile()
        
    if not what in ['vial','scan','rack','server']:
        result = 'unknown what=%s' % what
        
    print result
    
    if format == 'json':
        return {'Content-Type': 'application/json'}
    
    
        
        
def main(**kwargs):
    """Called by wwwcgi, kwargs are http get parameters"""
    p = PlateScanner(**kwargs)
    p.run()
    
