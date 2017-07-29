""" Example of module function which can be called from wwwcgi.py CGI script 

"""

import sys
import serial

def forward(data='', portname='COM1', **kw):
    """ Send data to serial port of given portname """
    try:
        p = serial.Serial(portname)
        p.open()
        p.write(data)
        p.close()
        print 'DATA:%s SENT_TO: %s' % (data, portname)
    except:
        print 'Failed to send data to %s (%s, %s)' % ((portname,) + sys.exc_info()[:2])
    print '<form><input type="button" value="Back" onclick="history.go(-1);" /></form>'

if __name__ == '__main__':
    forward('test from main')


