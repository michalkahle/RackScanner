import os
import glob
import logging
from time import time
import subprocess
import tempfile
from PIL import Image

import numpy as np
import cv2
from pydmtx import DataMatrix
from scipy.ndimage import center_of_mass, label
import pandas as pd
import re
from math import degrees, atan, sqrt, sin, cos
#from jipylib import procutl, winenv, inifile
#http://www.pythonware.com/library/pil/handbook/introduction.htm

#http://effbot.org/zone/pil-numpy.htm

log = logging.getLogger('jipylib.xpil.imgmatrix')

class ImgMatrix(object):
    _argnames = ['inifile','filemask'] # instructs CmdLineWrap to assign first positional cmdline argument
    # to inifile and the second to filemask
    def __init__(self, filemask=None, csvfilename='', csvdir='', **kwargs):
        self.filemask = filemask # filename of the plate image
        self.img = cv2.imread(filemask, 0).T # we will trasverse back the well images
        self.dg = cv2.cvtColor(self.img, cv2.COLOR_GRAY2RGB)
        self.wells = self.locate_wells_by_matching()
        self.dm_read = DataMatrix(max_count = 1, 
                                 timeout = 300, 
                                 min_edge = 10, 
                                 max_edge = 32, 
                                 threshold = 5, 
                                 deviation = 10,
                                 shape = DataMatrix.DmtxSymbol12x12)
        # self.dm_read = DataMatrix()
        self.csvfilename = csvfilename
        self.csvdir = csvdir

        filedir, base_ext = os.path.split(self.filemask)
        base, ext = os.path.splitext(base_ext)
        if not self.csvfilename:
            self.csvfilename = os.path.join(self.csvdir, base + '.csv')
        
        self._barcodes = []
        self._failed = []
        
        self._current_item = 0 # for showing the progress of the thread operation
        self._item_count = 0
        self.finished = False # set true upon end of the run method
    
    def __call__(self):
        """For threading. Use ._current_item, ._item_count to check the progress."""
        self.run()
        
    def locate_wells_by_matching(self):
        template = cv2.imread("template.png")[:,:,0]
        res = cv2.matchTemplate(self.img, template, cv2.TM_CCOEFF_NORMED)
        b = 100
        crop = res[b:-b,b:-b]
        th, crop = cv2.threshold(crop, 0.6, 1, cv2.THRESH_TOZERO)
        labeled, n = label(crop)
        if(n != 96):
            raise NameError("%s wells detected. Should be 96." % n)
        arr = np.round(center_of_mass(crop, labeled, range(1, n+1))).astype(int) + 100
        df = pd.DataFrame(arr, columns = ("y", "x"))
        df["row"] = np.arange(8).repeat(12)
        df = df.sort_values(["row", 'x'])
        df["col"] = np.tile(np.arange(12), 8)
        df = df.set_index(['row', 'col'], drop=True)
        return df

    # def get_well_grid(self, row, col):
    #     ox, oy, dx, dy = (200, 160, 212, 206)
    #     py = oy + row * dy
    #     px = ox + col * dx
    #     well = self.img[py:py+200, px:px+200]
    #     well[0:5, :] = 0; well[:, 0:5] = 0 # for diagnostics
    #     return well[5:, 5:].copy(order = 'F')

    def get_well_matched(self, row, col):
        coo = self.wells.loc[(row, col)]
        return self.img[coo.y+35:coo.y+185, coo.x+40: coo.x+190].T.copy(order = 'C')

    def mark_well(self, row, col, mark):
        coo = self.wells.loc[(row, col)]
        color = {
                'harris' : (0,200,0),
                'failed' : (255,0,0),
                'empty' : (0,0,0)
                }[mark]
        cv2.circle(self.dg, (coo.x+115, coo.y+110), 75, color = color, thickness = 5)



    def run(self):
        try:
            log.info('imgmatrix begin')
            self.read_rack()
            self.write_csv_file()
            log.info('imgmatrix end')
            log.info('Result written to "%s". Barcodes found:' % self.csvfilename)
            for b in self._barcodes:
                log.info(b)
            if self._failed:
                log.error('FAILED to parse:')
                for f in self._failed:
                    log.error(f)
        finally:
            self.finished = True
        return self._barcodes, self._failed

    def read_rack(self):
        self._barcodes = []
        self._failed = []
        start = time()
        for (row, col), rr in self.wells.iterrows():
            well = self.get_well_matched(row, col)
            code, method = self.read_barcode(well)
            self._barcodes.append((row, col, code, method))
            if code is None: 
                self._failed.append((row, col))
            self.mark_well(row, col, method)
        s = pd.DataFrame(self._barcodes, columns=('row', 'col', 'code', 'method')).groupby('method').size()
        log.info((s, ' %.2f s' % (time() - start)))

    def read_barcode(self, well):
        x, thr = cv2.threshold(well, 128, 1, cv2.THRESH_BINARY)
        if thr.sum() < 500:
            return (1, 'empty')

        
        code = self.decode_harris(well)
        if code:
            return (code, 'harris')


        # rotated = self.improve_fft(well)
        # code = self.decode(rotated)
        # if code:
        #     return (code, 'rotated')

        # code = self.decode(well)
        # if code:
        #     return (code, 'unchanged')

        return (None, 'failed')







    def decode(self, img, reader = None):
        if reader is None:
            reader = self.dm_read
        height = img.shape[0]
        width = img.shape[1]
        code = reader.decode(width, height, img)
        if code and re.match('\d{10}', code):
            return code
        else:
            return None

    def improve_fft(self, well):
        fft = np.fft.fftshift(np.fft.fft2(well))
        mask = np.zeros(well.shape)
        center = tuple(x/2 for x in well.shape)
        cv2.circle(mask, center, 60, color = 1, thickness = -1);
        cv2.circle(mask, center, 50, color = 0, thickness = -1);
        filtered = np.copy(fft) * mask
        blur = cv2.GaussianBlur(np.abs(filtered), (5, 5), 0)
        maximum = cv2.minMaxLoc(blur)[3]
        try:
            theta = atan(float(maximum[1]-center[1])/float(maximum[0]-center[0]))
        except ZeroDivisionError: 
            theta = 0
        M = cv2.getRotationMatrix2D(center, np.rad2deg(theta), 1)
        rotated = cv2.warpAffine(well, M, (well.shape[1], well.shape[0]))
        return rotated

    def decode_harris(self, well):
        harris = cv2.cornerHarris(well, 4, 1, 0.0)
        cntr = find_contour(harris)
        if cntr is None:
            closed = cv2.morphologyEx(harris, cv2.MORPH_CLOSE, make_round_kernel(9))
            cntr = find_contour(closed)
        if cntr is None:
            return None

        box = trim(cntr)

        a = 120
        M = cv2.getAffineTransform(box[0:3], np.array([[a,0],[0,0],[0,a]], dtype = "float32"))
        dst = cv2.warpAffine(well, M, (a,a)) #, flags=cv2.INTER_NEAREST
        resized = cv2.resize(dst, (12,12))
        x, thr2 = cv2.threshold(resized, 80, 255, cv2.THRESH_BINARY)
        barcode = cv2.copyMakeBorder(thr2, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value = 0)
        barcode = cv2.resize(barcode, (80,80), interpolation = cv2.INTER_NEAREST)
        barcode_cl = cv2.cvtColor(barcode.T, cv2.COLOR_GRAY2BGR)
        reader = DataMatrix()
        return self.decode(barcode_cl, reader)










    def write_csv_file(self, barcodes=[], filename=''):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        f = open(filename, 'w')
        f.write('\n'.join([','.join(rcb) for rcb in barcodes]))
        f.close()

def trim(cntr, size = 70):
    while True:
        box, u, v = fit_box(cntr)
        center = box[0] + (box[2] - box[0]) / 2
        if cv2.norm(u) > size:
            dim = 0
        elif cv2.norm(v) > size:
            dim = 1
        else:
            break
        u1, v1 = u / cv2.norm(u), v / cv2.norm(v)
        Mb = np.column_stack((u1, v1))
        cntp = cntr.copy()[:,0,:].T
        cntp = np.dot(Mb.T, cntp)
        arr = cntp[dim, :]
        m = arr.mean()
        imax, imin = arr.argmax(), arr.argmin()
        cntp[dim, imax] = m
        cntp[dim, imin] = m
        cntr[imax, 0] = center            
        cntr[imin, 0] = center
    return box

def find_contour(img):
    x, thr = cv2.threshold(img, 0.1 * img.max(), 255, cv2.THRESH_BINARY)
    dst, cntr, hierarchy = cv2.findContours(thr.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cntr = sorted(cntr, key = cv2.contourArea, reverse = True)[0]
    size = 70
    box, u, v = fit_box(cntr)
    if cv2.norm(u) < size * 0.9 or cv2.norm(v) < size * 0.9:
        return None
    else:
        return cntr

def fit_box(cntr):
    box = cv2.boxPoints(cv2.minAreaRect(cntr))    
    u = box[0] - box [1]
    v = box[2] - box [1]
    return box, u, v

def make_round_kernel(size):
    kernel = np.zeros((size, size), np.uint8)
    r = size / 2
    kernel = cv2.circle(kernel, (r, r), r, color = 1, thickness = -1)
    return kernel

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
