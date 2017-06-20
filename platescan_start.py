"""

Command line starter of the server or the client or scanning of the vial or the rack

Starts only if it is not running yet.

"""
import os
import sys
import urllib
import logging

import socket
import select
import traceback
import struct
import cPickle
try:
    import site
except ImportError:
    pass
import string

import BaseHTTPServer
import CGIHTTPServer
import threading

#for wingide debugging:
#if os.environ.has_key('WINGDB_ACTIVE'):

extra = os.environ.get('EXTRA_PYTHONPATH')
if extra:
    #http://www.wingware.com/doc/howtos/debugging-under-py2exe 
    sys.path.extend(extra.split(os.pathsep))
    print('sys.path=%s' % sys.path)
    try:
        import wingdbstub
    except:
        print('Failed to import wingdbstub')
    setenviron="""
EXTRA_PYTHONPATH=\Python25\Lib\site-packages\py2exe\samples\simple\dist;\Python25\lib;\Python25\dlls
WINGDB_EXITONFAILURE=1
WINGHOME=\Program Files\Wing IDE 2.1
"""
else:
    print('No EXTRA_PYTHONPATH found')
#/for wingide


import platescan
from platescan import imgmatrix

import buttonman

from jipylib import inifile as ifile
from jipylib import winkeys

log = logging.getLogger()

#ROOT handling
try:
    ROOT = os.path.dirname(__file__)
    log.info('Set ROOT from __file__ to %s' % ROOT)
except:
    log.warning('Failed to set root from __file__')
    ROOT = None
    
if not ROOT:
    try:
        ROOT = os.path.dirname(sys.argv[0])
        log.info('Set ROOT from sys.argv[0] to %s' % ROOT)
    except:
        log.warning('Failed to set ROOT from sys.argv[0], set to curdir')
        ROOT = None
        
if not ROOT:
    ROOT = os.path.abspath(os.curdir)
    log.info('Set ROOT from curdir to %s' % ROOT)
    
os.chdir(ROOT)
log.info('Changed current dir to %s' % ROOT)
sys.path.append(ROOT)
log.info('Appended %s to PYTHONPATH' % ROOT)
#/ROOT handling

try:
    if sys.argv[1:] == ['run_server']:
        log_base_fn = 'platescan.log'
    else:
        log_base_fn = 'platescan_start.log'
    logfn = os.path.join(platescan.LOGDIR, log_base_fn)
    log.addHandler(logging.FileHandler(logfn))
except:
    pass

log.addHandler(logging.StreamHandler())



#try:
#    import wwwcgi as wwwcgi_pkg
#    from wwwcgi import wwwcgi as wwwcgi_mod
#except ImportError:
#import jjutl.wwwcgi as wwwcgi_pkg

from jjutl.wwwcgi import wwwcgi as wwwcgi_mod

class PlateScanStarter:
    def __init__(self, what='server,client', inifile='platescan.ini'):
        self.what = what
        self.inifile = inifile
        ifn = inifile #'platescan.ini' #os.path.join(os.path.dirname(__file__), 'platescan.ini')
        self.ini = ifile.load(ifn)
        self.ini.setdefault('port', '8080')
        self.ini.setdefault('hostname','localhost')
        self.ini.setdefault('browser', '') # iexplore, firefox
        #self.ini.setdefault('python', sys.executable)
        try:
            log.setLevel(int(self.ini.get('loglevel', 20)))
        except:
            pass
        

    def run(self):
        whats = self.what
        if isinstance(whats, basestring):
            whats = whats.split(',')
        for what in whats:
            if what == 'server':
                self.start_server()
            elif what == 'vial':
                self.run_vial()
            elif what == 'rack':
                self.run_rack()
            elif what == 'client':
                self.start_client()
            #all of the above will start other independent process and continue 
            
            elif what == 'run_server':
                #this will run the server process and won't stop until the server is terminated
                self.run_server()
            else:
                raise PlateScanStarterError('Unknown what %s' % what)

    def run_server(self):
        """Run the wwwcgi platescan server process. 
        Should not be called directly from command line parameter 'run_server', use 'server' instead,
        otherwise the inifile might not be correct, if other used for server then for the client.
        """
        #os.chdir(os.path.dirname(__file__))
        #os.system('start "PlateScan Server" /min %(python)s wwwcgi\\wwwcgi.py %(port)s' % self.ini)
        #os.system('platescansrv.bat %(port)s' % self.ini)
        #from wwwcgi import wwwcgi
        import platescan
        platescan.INI_FILENAME = self.inifile
        wwwcgi_mod.runwww(port=int(self.ini['port']))
        
    def start_server(self):
        """Spawn the server by calling platescan_start.exe with internal "run_server" parameter
        Start on port defined in platescan.ini.
        """
        try:
            url = 'http://%(hostname)s:%(port)s' % self.ini
            urllib.urlopen(url)
            log.info('Server already running at: %s' % url)
            return
        except:
            pass
        if os.path.exists('platescan_start.exe'):
            #py2exe created exe file from this python script
            #cmd = 'start "PlateScan Server" /min platescan_start.exe run_server %(port)s' % self.ini
            cmd = 'start "PlateScan Server %s\\%s" /min platescan_start.exe run_server %s' % (ROOT, self.inifile, self.inifile) # port number is loaded from ini now; showing inifile name
        else:
            #cmd = 'platescansrv.bat %(port)s' % self.ini
            cmd = 'start "PlateScan Server %s\\%s" /min "%s" platescan_start.py run_server %s' % (ROOT, self.inifile, sys.executable, self.inifile)
        os.system(cmd)
        log.info('Executed: %s' % cmd)
            
        
    def start_client(self):
        """Check if browser window with title platescan is open.
        If yes, activate it. If not open in the browser window the page.
        """
        
        #  error = 'Avision configuration files were modified. Please restart the computer.'
        caption = platescan.TITLE + (' (%s)' % self.inifile)
        
        errors = []
        msg = urllib.quote(buttonman.check_inis())
        if msg:
            errors.append(msg)
        msg = imgmatrix.check_imagemagick(self.ini.get('imagemagick', imgmatrix.IMAGE_MAGICK))
        if msg:
            errors.append(msg)
            
        oini = self.ini.copy()
        if imgmatrix.IMAGE_MAGICK_FOLDER:
            #ImageMagickFolder found on this computer, save it to ini
            oini['imagemagickfolder'] = imgmatrix.IMAGE_MAGICK_FOLDER
            ifile.save(oini, self.inifile)
        
        if errors:
            self.ini['error'] = urllib.quote('\n'.join(errors))
        else:
            self.ini['error'] = ''
            
        self.ini['caption'] = caption
        #h = winkeys.find_window('PlateScan') # for some reason Firefox shows just the PlateScan word in tab title
        h = winkeys.find_window(platescan.TITLE) 
        if h:
            winkeys.activate_window(h)
            log.info('Client window is already opened. Activated.')
        else:
            cmd = 'start "%(caption)s" %(browser)s "http://%(hostname)s:%(port)s/wwwcgi.py?action=call&module=platescan&function=main&error=%(error)s"' % self.ini
            os.system(cmd)
            log.info('Executed: %s' % cmd)
        
    def run_vial(self):
        """Activate the client window and send to it a name of the scanned file (if any) and
        keyboard shortcut to start the parsing ...."""


def main(*args):
    p = PlateScanStarter(*args)
    p.run()

if __name__ == '__main__':
    main(*sys.argv[1:])
