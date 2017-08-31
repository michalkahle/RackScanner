# Run as root! 
# Then direct your browser to:
# http://localhost:80/wwwcgi.py?action=call&module=platescan&function=main
# add &reload=true to reload the module during each request

import os
os.chdir(os.path.dirname(__file__))
import sys
#import urllib
sys.path.append('./lib')
from wwwcgi import wwwcgi

def main():
#    try:
#        url = 'http://localhost:80'
#        urllib.urlopen(url)
##        log.info('Server already running at: %s' % url)
#        return
#    except:
#        pass
    wwwcgi.runwww()        

if __name__ == '__main__':
    main()
