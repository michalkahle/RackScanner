import sys
import os
import logging
import datetime
import glob
sys.path.append('./lib')
import utils 
import imgmatrix
import re
import matplotlib as mpl
import twainutl
import time

reload(twainutl)
reload(imgmatrix)

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
log.setLevel(20)

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
<input name="platebarcode" placeholder="Plate barcode"></input>
<table class="form">
  <tr>
    <td><button type="submit" name="action" value="rack">Scan Rack</button> 
    <td><button type="submit" name="action" value="vial">Scan Single Tube</button>
    <td><button type="submit" name="action" value="csv">Upload CSV</button>
    <td><button type="submit" name="action" value="test">Test Decoding</button>
    <td><button type="submit" name="action" value="scan">Test Scanning</button>
</table>
<input type="hidden" name="reload" value="%(reload)s" />
</form>
"""

foot_template = """
</body>
</html>
"""

defaults = {
    'reload' : '',
    'platebarcode' : '',
    'lastvialbarcode' : '',
}

class PlateScanner(object):
    def __init__(self, **kwargs):
        self.kwargs = defaults.copy()
        self.kwargs.update(kwargs)
        self.csvfilename = None
        self.reader = None
        self.messages = []
        self.bmpfilename = None

    def run(self):
        print head_template % {'title' : 'RackScanner 2.0'}
        print form_template % self.kwargs
        
        action = self.kwargs.get('action')
        if action =='rack':
            self.run_plate()
        elif action == 'vial':
            self.run_vial()
        elif action == 'csv':
            self.run_uploadcsv()
        elif action == 'test':
            self.bmpfilename = 'demo/rack_96_sample.bmp'
            # self.bmpfilename = 'bmp/rack20170918040434.bmp'
#            self.bmpfilename = 'demo/rack_24_sample.bmp'
            self.run_plate()
        elif action == 'scan':
            self.scan_image(bottom = 0.5, right = 0.5)
            print '<img src="bmp/%s" />' % self.filename

        if self.messages:
            print '<ul id="messages">\n'
            for m in self.messages:
                print '<li>%s</li>' % m
            print '</ul>'
        
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print '<pre>'
        pp.pprint(self.kwargs)
        print '</pre>'
        print foot_template % self.kwargs
        
    def run_plate(self):
        if not self.bmpfilename:
            self.scan_image(rack_or_vial='rack')
        
        if self.kwargs.get('reload'):
            reload(imgmatrix)
        self.reader = imgmatrix.ImgMatrix(filemask = self.bmpfilename)
        self.reader.read_rack()
        
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
        

        mpl.image.imsave('dg_pic.png', self.reader.dg_small)
        print '<img src="dg_pic.png" />'
        
        base = 'rack-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
        if self.kwargs.get('platebarcode'):
            base += '_' + self.kwargs.get('platebarcode')
        self.csvfilename = os.path.join(CSVDIR,  base + '.csv')
        self.log('Barcodes written to file: <a href="file:///%s">%s</a><br />' % (self.csvfilename, self.csvfilename))
                    
    def scan_image(self, rack_or_vial = 'rack'):
        self.filename = rack_or_vial + time.strftime('%Y%m%d%H%M%S.bmp')
        self.bmpfilename = os.path.join(BMPDIR, self.filename)
        twainutl.scan(self.bmpfilename)

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
        if self.bmpfilename and not os.path.exists(self.bmpfilename):
            self.bmpfilename = None # could have been removed before other platescan browser page noticed
        if not self.bmpfilename: # bmpfilename is not usually supplied (only when debugging)
            self.scan_image(rack_or_vial = 'vial')

        dic = {}
        dic['filemask'] = self.bmpfilename
        dic['csvdir'] = CSVDIR 
        reader = imgmatrix.ImgMatrix(**dic)
        crb = reader.read_barcode(self.bmpfilename)
        if crb and crb[2]:
            
            self.kwargs['lastvialbarcode'] = crb[2]
        else:
            self.log('run_vial_reader = no barcode found in %s' % self.bmpfilename)
        
    def write_csv_file(self):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        print filename
        f = open(filename, 'w')
        f.write('\n'.join([','.join(str(rcb[0:2])) for rcb in barcodes]))
        f.close()

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
