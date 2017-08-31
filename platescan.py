import sys
import os
import logging
import datetime
import glob
import urllib

import  utils 
#import imp
import imgmatrix
#import buttonman
import re

#ROOT = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.dirname(sys.argv[0])) #os.path.abspath(os.curdir)

def checksubdir(sub):
    subdir = os.path.join(ROOT, sub)
    if not os.path.exists(subdir):
        os.mkdir(subdir)
    return subdir       
BMPDIR = checksubdir('bmp') # where the scanned image files should be stored
CSVDIR = checksubdir('csv') # where the csv files with samples barcodes should be stored
LOGDIR = checksubdir('log') # where log files should be stored
DEMODIR = os.path.join(ROOT, 'demo') # where demo/example files are placed

log = logging.getLogger()
logfile = os.path.join(LOGDIR, 'platescan_%s.log' % datetime.date.today())
log.addHandler(logging.FileHandler(logfile))

head_template = """
<!DOCTYPE html>
<html>
<head>
    <title>%(title)s</title>
    <script type="text/javascript" src="http://code.jquery.com/jquery.min.js" ></script>
    <script type="text/javascript" src="/js/platescan.js" ></script>
    <script type="text/javascript" src="/js/jijslib.js" ></script>
    <link type="text/css" rel="stylesheet" media="all" href="/css/platescan.css" />
</head>
<body>
    <h1>%(title)s</h1>
    <p class="hint">Place the tube or rack with its A1 position to the upper left corner or the scanning area. </p>
"""

form_template = """
<form name="scan" method="get">
<table class="form">
  <tr>
    <td class="label">Plate barcode
    <td><input id="platebarcode" name="platebarcode" type="%(platebarcode)s" />
    <span class="hint">(None for new plate)
  <tr>
    <td>Last image file name:
    <td><input id="imagefilename" name="bmpfilename" value="" size="80" />
</table>
<table class="form">
  <tr>
    <td><input type="submit" id="scanrack" name="scanrack" value="Scan Rack" /> 
    <td><input type="submit" id="scanvial" name="scanvial" value="Scan Single Tube" />
    <td><input type="submit" id="uploadcsv" name="uploadcsv" value="Upload CSV" />
</table>
       
<input type="hidden" name="action" value="call" />
<input type="hidden" name="module" value="platescan" />
<input type="hidden" name="function" value="main" />
  
<input type="hidden" name="reload" value="%(reload)s" />
<input type="hidden" name="submitted" value="1" />
</form>
"""

foot_template = """
</body>
</html>
"""

defaults = {
    'title' : 'RackScanner 2.0',
    'reload' : '',
    'platebarcode' : '',
    'lastvialbarcode' : '',
}

avision600 = {  
    'origin' : (170,210),
    'matrixsize' : (12,8),
    'boxsize' : (210,210),
    'pixeltype' : 2,
    'autocrop' : 0,
    'left' : 0,
    'top' : 0,
    'right' : 3.5,
    'bottom' : 5 }

avision600_vial = { 
    'right' : 0.5,
	'bottom' : 0.5 }

class PlateScanner(object):
    def __init__(self, **kwargs_):
        kwargs = defaults
        kwargs.update(kwargs_)
        self.reader = None
        self.kwargs = kwargs
        self.unquote_kwargs()
        self.bmpfilename = kwargs.get('bmpfilename')
        self.csvfilename = None
        self.messages = []
        try:
            log.setLevel(int(kwargs.get('loglevel', 20)))
        except:
            pass

    def run(self):
        if self.kwargs.get('scanvial'):
            self.run_vial()
        elif self.kwargs.get('uploadcsv'):
            self.run_uploadcsv()
        elif self.kwargs.get('runcsv'):
            self.run_csv()
        elif self.kwargs.get('scanrack'):
            self.run_plate()
        self.display_form_page()
        
    def display_form_page(self):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print head_template % self.kwargs
        print form_template % self.kwargs
        if self.reader:
            plate = self.reader.wells['code'].unstack()
            html = ['<table class="plate">']
            html += ['<tr><th>'] + ['<th>%s' % i for i in plate.columns]
            for row in plate.index:
                html.append('<tr><th>%s' % row)
                for col in plate.columns:
                    code = plate.loc[row, col]
                    cls = '' if re.match('\d{10}', code) else ' class="%s"' % code
                    html.append('<td%s>%s' % (cls, code))
            html.append('</table>')
            print '\n'.join(html)
        if self.messages:
            print '<ul id="messages">\n'
            for m in self.messages:
                print '<li>%s</li>' % m
            print '</ul>'
        
        print '<pre>'
        pp.pprint(self.kwargs)
        print '</pre>'
        
        print foot_template % self.kwargs
        
    def scan_image(self, **kwargs):
        what = kwargs.pop('what') # 'rack' or 'vial'
        
        kwargs.setdefault('folder', BMPDIR)
        kwargs.setdefault('resolution', 600.0)
        
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

    def run_vial_reader(self):
        dic = self.inipars
        dic['filemask'] = self.bmpfilename
        dic['csvdir'] = CSVDIR 
        reader = imgmatrix.ImgMatrix(**dic)
        crb = reader.read_barcode(self.bmpfilename)
        if crb and crb[2]:
            
            self.kwargs['lastvialbarcode'] = crb[2]
        else:
            self.log('run_vial_reader = no barcode found in %s' % self.bmpfilename)
        
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
        
    def run_vial(self):
        self.inipars = self.kwargs.copy()
        self.inipars.update(avision600)
        self.inipars.update(avision600_vial)
        if self.bmpfilename and not os.path.exists(self.bmpfilename):
            self.bmpfilename = None # could have been removed before other platescan browser page noticed
        if not self.bmpfilename: # bmpfilename is not usually supplied (only when debugging)
            self.scan_image(what='vial', **self.inipars)
        self.run_vial_reader()
        self.hide_bmpfile(self.bmpfilename)
        
    def run_plate(self):
        self.inipars = self.kwargs.copy()
        self.inipars.update(avision600)
        
        if not self.bmpfilename: # bmpfilename is not usually supplied (only when debugging)
            self.scan_image(what='rack', **self.inipars)
        
        if os.path.exists(self.bmpfilename):
            if self.kwargs.get('reload'):
                reload(imgmatrix)
            self.reader = imgmatrix.ImgMatrix(filemask = self.bmpfilename)
            self.reader.read_rack()
    
        base = 'rack-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
        if self.kwargs.get('platebarcode'):
            base += '_' + self.kwargs.platebarcode
        self.csvfilename = os.path.join(CSVDIR,  base + '.csv')
        self.log('Barcodes written to file: <a href="file:///%s">%s</a><br />' % (self.csvfilename, self.csvfilename))
        
            
        #self.uploadcsv(csvfilename)
        
                    
    def write_csv_file(self):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        print filename
        f = open(filename, 'w')
        f.write('\n'.join([','.join(str(rcb[0:2])) for rcb in barcodes]))
        f.close()

    def unquote_kwargs(self, keys=['bmpfilename','uploadurl']):
        """Eventual %xx encoded chars get replaced back by urllib.unquote"""
        for k in keys:
            if self.kwargs.get(k):
                self.kwargs[k] = urllib.unquote(self.kwargs[k])
                
    def log(self, message, level=logging.INFO):
        log.log(level, message)
        self.messages.append(message)
        
def main(**kwargs):
    """Called by wwwcgi, kwargs are http get parameters"""
    try:
        p = PlateScanner(**kwargs)
        p.run()
    except:
        import cgi
        import traceback
        print '<pre>%s</pre>' % cgi.escape(traceback.format_exc())
