import os
import glob
import logging
import datetime
import subprocess
import tempfile
from PIL import Image

import numpy as np
import cv2
from pydmtx import DataMatrix
#from jipylib import procutl, winenv, inifile
#http://www.pythonware.com/library/pil/handbook/introduction.htm

#http://effbot.org/zone/pil-numpy.htm

log = logging.getLogger('jipylib.xpil.imgmatrix')

class ImgMatrix(object):
    _argnames = ['inifile','filemask'] # instructs CmdLineWrap to assign first positional cmdline argument
    # to inifile and the second to filemask
    def __init__(self, filemask=None, csvfilename='', csvdir='', **kwargs):
        self.filemask = filemask # filename of the plate image
        self.csvfilename = csvfilename # name of the csv file to write the barcodes with their row and col
        self.csvdir = csvdir # in what folder to store csv files
        
        self._inited = False
        self._barcodes = [] # list of tuples (row, col, barcodes) obtained during run
        self._failed = [] # list of tuples (row, col) not read
        
        self._current_item = 0 # for showing the progress of the thread operation
        self._item_count = 0
        self.finished = False # set true upon end of the run method
        
    def _init(self):
        if self._inited:
            return
        self._inited = True
        filenames = glob.glob(self.filemask)
        filenames.sort()
        self.filename = filenames[-1]
        log.info('Scanning file "%s" for bacodes...' % self.filename)
        filedir, base_ext = os.path.split(self.filename)
        base, ext = os.path.splitext(base_ext)
        if not self.csvfilename:
            d = self.csvdir
            self.csvfilename = os.path.join(d, base + '.csv')
    
    def __call__(self):
        """For threading. Use ._current_item, ._item_count to check the progress."""
        self.run()
        
    def run(self):
        try:
            log.info('imgmatrix begin')
            self._init()
            self.starttime = datetime.datetime.now()
            #self.create_box_images()
            self.read_barcodes()
            self.write_csv_file()
            log.info('imgmatrix end')
            log.info('Result written to "%s". Barcodes found:' % self.csvfilename)
            for b in self._barcodes:
                log.info(b)
            if self._failed:
                log.error('FAILED to parse:')
                for f in self._failed:
                    log.error(f)
            self.stoptime = datetime.datetime.now()
            log.info('Time spent on the task: %s seconds' % (self.stoptime-self.starttime).seconds)
        finally:
            self.finished = True
        return self._barcodes, self._failed

    def read_barcodes(self):
        self._init()
        self._barcodes = []
        img = np.array(Image.open(self.filename))
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        img = img.T # libdmtx seems to read transversed images just fine

        for row in range(8):
            for col in range(1):
                well = self.get_well(img, row, col)
                r = self.read_barcode(well)
                if r:
                    self._barcodes.append(r)
                if (not r) or (r[0] == ''):
                    self._failed.append((row, col))
        return self._barcodes

    def write_csv_file(self, barcodes=[], filename=''):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        f = open(filename, 'w')
        f.write('\n'.join([','.join(rcb) for rcb in barcodes]))
        f.close()


    def get_well(self, img, row, col):
        ox, oy, dx, dy = (200, 160, 212, 206)
        py = oy + row * dy
        px = ox + col * dx
        well = img[py:py+dy, px:px+dx]
        well_cp = np.copy(well)
        well[0:5, :] = 0; well[:, 0:5] = 0 # for diagnostics
        return well_cp

    def read_barcode(self, well):
        dm_read = DataMatrix(max_count = 1, 
                             timeout = 300, 
                             min_edge = 10, 
                             max_edge = 32, 
                             threshold = 5, 
                             deviation = 10)
        height, width = well.shape
        dmtx_code = dm_read.decode(width, height, well)
        return dmtx_code
        
def main():
    #if not hasattr(logging, 'basicConfig'):
    #    log.addHandler(logging.StreamHandler())
    #    log.setLevel(logging.INFO)
    #else:
    logging.basicConfig(level=logging.INFO)
    
    
    im = ImgMatrix(**pars3)
    bcs, failed = im.run()
    print 'written to "%s"' % im.csvfilename
    for b in bcs:
        print b
    if failed:
        print 'FAILED:'
        for f in failed:
            print f


def cmd():
    logging.basicConfig(level=logging.INFO, filename='imgmatrix.log')
    log.addHandler(logging.StreamHandler())
    from jipylib import cmdline
    i = cmdline.CmdLineWrap(ImgMatrix)
    i.run()
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pass
