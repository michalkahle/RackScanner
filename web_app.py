import sys
import os
import logging
import datetime
import re
import matplotlib as mpl
import time
import cgi
import traceback

import scanner_controller
import dm_reader
reload(scanner_controller)
reload(dm_reader)

os.chdir(os.path.abspath(os.path.dirname(__file__)))

for subdir in ['bmp', 'csv']:
    if not os.path.exists(subdir):
        os.mkdir(subdir)

logging.basicConfig(filename = 'rackscanner.log', 
                    format = '%(asctime)s %(levelname)s: %(message)s', 
                    level = logging.INFO)

head_template = """
<!DOCTYPE html>
<html>
<head>
    <title>%(title)s</title>
    <link type="text/css" rel="stylesheet" media="all" href="/platescan.css" />
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
    <td><button type="submit" name="action" value="test">Test</button>
</table>
</form>
"""

foot_template = """
</body>
</html>
"""

defaults = {
    'reload' : '',
}

def main(**kwargs):
    """Called by http_server, kwargs are http get parameters"""
    try:
        run(**kwargs)
    except:
        print '<pre>%s</pre>' % cgi.escape(traceback.format_exc())

def run(**kwargs):
    params = defaults.copy()
    params.update(kwargs)
    platebarcode = params.get('platebarcode')
    print head_template % {'title' : 'RackScanner 2.0'}
    print form_template % params
    
    action = params.get('action')
    if action =='rack':
        filename = create_filename(rack_or_vial='rack', barcode = platebarcode)
        scanner_controller.scan(filename)
        decode_plate(filename)
    elif action == 'vial':
        filename = create_filename(rack_or_vial='vial')
        scanner_controller.scan(filename)
        decode_vial(filename)
    elif action == 'csv':
        self.run_uploadcsv()
    elif action == 'test':
        filename = 'demo/rack_96_sample.bmp'
        # filename = 'bmp/rack20170918040434.bmp'
        # filename = 'demo/rack_24_sample.bmp'
        decode_plate(filename)

    print foot_template
        
def create_filename(rack_or_vial = 'rack', barcode = None):
    base = rack_or_vial + '-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
    if barcode:
        base += '_' + barcode
    filename = os.path.join('bmp',  base + '.bmp')
    return filename

def decode_vial(filename):
    reader = dm_reader.ImgMatrix(filename = filename)
    crb = reader.read_barcode(filename)
    if crb and crb[2]:
        
        params['lastvialbarcode'] = crb[2]
    else:
        logging.info('run_vial_reader = no barcode found in %s' % filename)
   
def decode_plate(filename):
    wells, dg_pic = dm_reader.read(filename)
    write_table(wells)
    mpl.image.imsave('dg_pic.png', dg_pic)
    print '<img src="dg_pic.png" />'
    print '<input id=last_csv name=last_csv value="%s"/>' % (filename)
                    
def write_table(wells):
    plate = wells['code'].unstack()
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








class PlateScanner(object):
    def __init__(self, **kwargs):
        self.csvfilename = None
        self.messages = []

    def uploadcsv(self, filename=None):
        """Upload specified file to the server."""
        uploadurl = params.get('uploadurl')
        if not uploadurl:
            logging.info('No url specified for csv file %s upload.' % filename)
        else:
            if filename is None:
                #can be None if testing, then find the last csv file created
                filename = self._get_last_csv_file()
            #fn, url, user='', password='', filebodyfield='file', okmsg='', errdir=''):
            try:
                u = uploadfile.Uploader(url=uploadurl, user=params['user'], password=params['password'], 
                                        filebodyfield=params['uploadfield'], printmsgs=False)
                er = u.upload(filename)
                #er = uploadfile.uploadfile(filename, uploadurl, user=params['user'], password=params['password'], filebodyfield=params['uploadfield'])
                if er:
                    logging.info('File %s upload to %s failed: %s' % (filename, uploadurl, er), logging.ERROR)
                else:
                    logging.info('CSV file %s uploaded to %s' % (filename, uploadurl))
                logging.info(u.buf)
            except:
                logging.info('Failed to upload CSV file %s to %s (%s, %s)' % (filename, uploadurl, sys.exc_info()[0], sys.exc_info()[1]), logging.ERROR)
            
        
        
    def write_csv_file(self):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        print filename
        f = open(filename, 'w')
        f.write('\n'.join([','.join(str(rcb[0:2])) for rcb in barcodes]))
        f.close()

        
