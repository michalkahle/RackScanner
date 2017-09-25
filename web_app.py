import sys
import os
import logging
import datetime
import re
import matplotlib as mpl
import time
import cgi
import traceback
import platform

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
    <link type="text/css" rel="stylesheet" href="resources/rackscanner.css" />
</head>
<body>
    <img src="resources/logo.png" id="logo"/>
    <h1>%(title)s</h1>
    <p class="hint">Place the tube or rack with its A1 position to the 
    upper left corner or the scanning area. </p>
"""

form_template = """
<form name="scan" method="get">
<input name="platebarcode" placeholder="Plate barcode"></input>
    <button type="submit" name="action" value="rack">Scan Rack</button> 
    <button type="submit" name="action" value="vial">Scan Single Tube</button>
    <button type="submit" name="action" value="test">Test</button>
"""

foot_template = """
</form>
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
    if action in ('rack', 'vial'):
        if platform.system() == 'Windows':
            filename = create_filename(action, platebarcode)
            scanner_controller.scan(filename)
        else:
            filename = 'demo/rack_96_sample.bmp' if action == 'rack' else 'demo/vial_1ml_sample.bmp'
        decode(filename, action == 'vial')
    elif action == 'csv':
        uploadcsv(params['last_csv'])
    elif action == 'test':
        filename = 'demo/rack_96_sample.bmp'
        # filename = 'bmp/rack20170918040434.bmp'
        # filename = 'demo/rack_24_sample.bmp'
        decode(filename)

    print foot_template
        
def create_filename(rack_or_vial, barcode = None):
    base = rack_or_vial + '-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
    if barcode:
        base += '_' + barcode
    filename = os.path.join('bmp',  base + '.bmp')
    return filename

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

def decode(filename, vial = False):
    wells, dg_pic = dm_reader.read(filename, vial = vial)
    write_table(wells)
    mpl.image.imsave('dg_pic.png', dg_pic)
    print '<img src="dg_pic.png" />'
    csvfilename = 'csv/' + os.path.split(filename)[1].replace('bmp', 'csv')
    wells.code.to_csv(csvfilename, sep = ';')
    print '<input id=last_csv name=last_csv value="%s"/>' % (csvfilename)
    print '<button type="submit" name="action" value="csv">Upload CSV</button>'

def uploadcsv(filename=None):
    print filename
    return


    # uploadurl = params.get('uploadurl')
    # if not uploadurl:
    #     logging.info('No url specified for csv file %s upload.' % filename)
    # else:
    #     if filename is None:
    #         #can be None if testing, then find the last csv file created
    #         filename = self._get_last_csv_file()
    #     #fn, url, user='', password='', filebodyfield='file', okmsg='', errdir=''):
    #     try:
    #         u = uploadfile.Uploader(url=uploadurl, user=params['user'], password=params['password'], 
    #                                 filebodyfield=params['uploadfield'], printmsgs=False)
    #         er = u.upload(filename)
    #         #er = uploadfile.uploadfile(filename, uploadurl, user=params['user'], password=params['password'], filebodyfield=params['uploadfield'])
    #         if er:
    #             logging.info('File %s upload to %s failed: %s' % (filename, uploadurl, er), logging.ERROR)
    #         else:
    #             logging.info('CSV file %s uploaded to %s' % (filename, uploadurl))
    #         logging.info(u.buf)
    #     except:
    #         logging.info('Failed to upload CSV file %s to %s (%s, %s)' % (filename, uploadurl, sys.exc_info()[0], sys.exc_info()[1]), logging.ERROR)
            
        
        

        
