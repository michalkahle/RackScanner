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
import pandas as pd

import scanner_controller
import dm_reader
reload(scanner_controller)
reload(dm_reader)
try:
    import settings
    reload(settings)
except ImportError:
    import settings_template as settings

os.chdir(os.path.abspath(os.path.dirname(__file__)))

for subdir in ['bmp', 'csv']:
    if not os.path.exists(subdir):
        os.mkdir(subdir)

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
<form name="scan" method="get">
%(barcode)s
<button type="submit" name="action" value="rack">%(verb)s Rack</button> 
<button type="submit" name="action" value="vial">%(verb)s Single Tube</button>
<input type="checkbox" name="check_codes" id="check_codes" %(check)s>
<label for="check_codes">check codes</label>
"""

foot_template = """
</form>
</body>
</html>
"""

def main(**params):
    """Called by http_server, kwargs are http get parameters"""
    try:
        run(**params)
    except:
        print '<pre>%s</pre>' % cgi.escape(traceback.format_exc())

def run(**params):
    platebarcode = params.get('platebarcode')
    check_codes = True if params.get('check_codes') else False
    print head_template % {
        'title' : 'RackScanner 2.1', 
        'verb' : {'scanner':'Scan', 'demo':'Demo', 'read_last':'Read'}[settings.mode],
        'barcode' : '<input name="platebarcode" placeholder="Plate barcode" autofocus></input>' if settings.mode == 'scanner' else '',
        'check' : 'checked' if check_codes else ''
        }

    action = params.get('action')
    if action in ('rack', 'vial'):
        if settings.mode == 'demo':
            filename = 'resources/rack_96_sample.bmp' if action == 'rack' else 'resources/vial_1ml_sample.bmp'
        elif settings.mode == 'scanner':
            filename = create_filename(action, platebarcode)
            if action == 'vial':
                scanner_controller.scan(filename, right=0.5, bottom=0.5)
            else:
                scanner_controller.scan(filename)
        else:
            filename = last_image(settings.images_dir)
        decode(filename, action == 'vial', check_codes=check_codes)
    elif action == 'csv':
        settings.upload(params['last_csv'])

    print foot_template
        
def create_filename(rack_or_vial, barcode = None):
    base = rack_or_vial + '-' + datetime.datetime.now().isoformat()[:19].replace('T','-').replace(':','-')
    if barcode:
        base += '_' + barcode
    filename = os.path.join('bmp',  base + '.bmp')
    return filename

def write_table(wells, check_codes=False):
    if check_codes:
        codes = pd.to_numeric(wells['code'].str.extract('(\d+)', expand=False))
        outliers = ((codes - codes.median()).abs() > 47).unstack()
    plate = wells['code'].unstack()
    html = ['<table class="plate">']
    html += ['<tr><th>'] + ['<th>%s' % i for i in plate.columns]
    for row in plate.index:
        html.append('<tr><th>%s' % row)
        for col in plate.columns:
            code = plate.loc[row, col]
            if check_codes and outliers.loc[row, col]:
                cls = ' class="check"'
            elif re.match('\d{10}', code):
                cls = ''
            else:
                cls = ' class="%s"' % code
            html.append('<td%s>%s' % (cls, code))
    html.append('</table>')
    print '\n'.join(html)

def decode(filename, vial = False, check_codes=False):
    wells, dg_pic = dm_reader.read(filename, vial = vial)
    write_table(wells, check_codes)
    mpl.image.imsave('dg_pic.png', dg_pic)
    print '<img id="dg_pic" src="dg_pic.png" />'
    csvfilename = 'csv/' + os.path.split(filename)[1].replace('bmp', 'csv')
    wells.loc[wells['method'] != 'empty'].code.to_csv(csvfilename, sep = ';')
    print '<input id=last_csv name=last_csv value="%s"/>' % (csvfilename)
    if settings.user:
        print '<button type="submit" name="action" value="csv">Upload CSV</button>'

def last_image(dirname):
    max_mtime, max_file = 0, None
    for filename in os.listdir(dirname):
        full_path = os.path.join(dirname, filename)
        mtime = os.path.getmtime(full_path)
        if mtime > max_mtime and filename.split('.')[-1] in ['bmp', 'png', 'tiff', 'jpeg']:
            max_mtime = mtime
            max_file = full_path
    return max_file
