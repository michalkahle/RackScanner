import os
import sys
import urllib
import logging
import platform
sys.path.append('./lib')
sys.path.append('./lib/wwwcgi')
import platescan
import buttonman
from wwwcgi import wwwcgi

log = logging.getLogger()

try:
    ROOT = os.path.dirname(__file__)
except:
    ROOT = None
    
if not ROOT:
    try:
        ROOT = os.path.dirname(sys.argv[0])
    except:
        ROOT = None
        
if not ROOT:
    ROOT = os.path.abspath(os.curdir)
    
os.chdir(ROOT)
sys.path.append(ROOT)

log_base_fn = 'platescan_start.log'
logfn = os.path.join(platescan.LOGDIR, log_base_fn)
log.addHandler(logging.FileHandler(logfn))
log.setLevel(20)

log.addHandler(logging.StreamHandler())



ini = {}
  
def start_client():
    caption = platescan.TITLE
    errors = []
    msg = urllib.quote(buttonman.check_inis())
    if msg:
        errors.append(msg)
        
    if errors:
        ini['error'] = urllib.quote('\n'.join(errors))
    else:
        ini['error'] = ''
        
    ini['caption'] = caption

#        h = winkeys.find_window(platescan.TITLE) 
#        if h:
#            winkeys.activate_window(h)
#            log.info('Client window is already opened. Activated.')
#        else:
    
    cmd = 'start "http://localhost:80/wwwcgi.py?action=call&module=platescan&function=main"'
    os.system(cmd)
    log.info('Executed: %s' % cmd)
    

def main(*args):
    try:
        url = 'http://localhost:80'
        urllib.urlopen(url)
        log.info('Server already running at: %s' % url)
        return
    except:
        pass
    if platform.system() == 'Windows':
        cmd = 'start "PlateScan Server" /min "%s" platescan_start.py run_server' % sys.executable
        os.system(cmd)
    elif platform.system() == 'Linux':
        wwwcgi.runwww()
    start_client()

if __name__ == '__main__':
    main(*sys.argv[1:])
