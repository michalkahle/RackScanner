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
            filename = 'resources/rack_96_sample.bmp' if action == 'rack' else 'resources/vial_1ml_sample.bmp'
        decode(filename, action == 'vial')
    elif action == 'csv':
        status = uploadcsv(params['last_csv'])
        print status
    elif action == 'test':
        filename = 'resources/rack_96_sample.bmp'
        # filename = 'bmp/rack20170918040434.bmp'
        # filename = 'resources/rack_24_sample.bmp'
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
    wells.loc[wells['method'] != 'empty'].code.to_csv(csvfilename, sep = ';')
    print '<input id=last_csv name=last_csv value="%s"/>' % (csvfilename)
    if settings.url:
        print '<button type="submit" name="action" value="csv">Upload CSV</button>'

def uploadcsv(filename=None):
    import requests
    from settings import user, password, upload_url, login_url, status_url
    print filename
    s = requests.Session()
    s.get(login_url)
    login_data = {
        'username' : user,
        'password' : password,
        'csrfmiddlewaretoken' : s.cookies['csrftoken']
    }
    s.post(login_url, login_data, headers={'Referer' : login_url})
    data = {'upload_all': 'on', 
            'background': 'on', 
            'import_type': 'rack',
           'csrfmiddlewaretoken' : s.cookies['csrftoken']}
    files = {'thefile': (os.path.split(filename)[1], open(filename, 'rb'), 'text/csv')}
    r4 = s.post(upload_url, data = data, files = files)
    time.sleep(0.1)
    query = {
        'application' : 'chemgen',
        'task' : 'task',
        'id' : re.search('async_key = "(.*)".*$', r4.text, re.MULTILINE).group(1)
    }
    r5 = s.get(status_url, params=query)
    return r5.json()['status']