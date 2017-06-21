import os
import glob
import logging
import datetime
import subprocess
import tempfile
from PIL import Image

#from jipylib import procutl, winenv, inifile
#http://www.pythonware.com/library/pil/handbook/introduction.htm

#http://effbot.org/zone/pil-numpy.htm

log = logging.getLogger('jipylib.xpil.imgmatrix')

CSV_FIELD_NAMES = ['row', 'col', 'barcode']

IMAGE_MAGICK = 'ImageMagick-6.6.7-Q16' # default ImageMagick installation folder in Program Files
IMAGE_MAGICK_FOLDER = None # set to folder of the ImageMagick if found on this computer
ENV = os.environ.copy() # eventually modified ENV['PATH'] to include the found IMAGE_MAGICK_FOLDER
TEST_CMD = 'identify' # Try to run this program from command line to test if ImageMagick folder is in PATH. (The corresponding .exe file must be in the ImageMagick folder.)

class ImgMatrixError(Exception):
    pass

class ImgMatrix(object):
    _argnames = ['inifile','filemask'] # instructs CmdLineWrap to assign first positional cmdline argument
    # to inifile and the second to filemask
    def __init__(self, filemask=None, matrixsize=None, origin=None, boxsize=None, margin=1, 
                 basename='', rowtype='', coltype='', fileext='', datadir='', barcodereader='dmtxread', csvfilename='',
                 csvdir='',
                 tmpdir='', leavemissingempty=0, csvfieldorder=None,
                 delimiter='', cleanup=0, 
                 imagemagick=IMAGE_MAGICK, 
                 **kwargs):
        self.filemask = filemask # filename of the image to parse into the matrix of small/box images
        #if wildcard is given, than the latest file will be processed (assuming the ISO date is part of the filename)
        self.origin = origin # origin - (x,y) - of the matrix in the image; can be given as a string "x,y"
        self.matrixsize = matrixsize # matrixsize - (rows, columns) - number of rows and columns in the image of images placed in a matrix/table format
                                     # can be given as a string "rows,columns"
        self.boxsize = boxsize # (width,height) of the image box in the matrix; if not specified, calculated from image size, origin, and matrixsize
        self.margin = margin # margin(s) of the images to extract from the grid given by origin and size
                             # can be one number or css like tuples - (top/bottom, right/left), (top, right/left,bottom), (top, right, bottom, left)
        self.basename = basename # basename of the resulting image files - _row_column will be appended 
        self.coltype = coltype # how the matrix columns should be labeled (see rowtype)
        self.rowtype = rowtype # how the matrix rows should be labeled - '1': 1, 2, 3, ...; 'A': A, B, C,...
                               # if '-'  is after '1' or 'A' ('1-', 'A-'), it means descending,
                               # i.e. the rows/cols will be labeled in descending order (according to the matrixsize)
        
        self.fileext = fileext # file extension of the created matrix images; default equals to filename's ext
        self.datadir = datadir # folder where to store the created images; default is filename.tmp subfolder of the %TMP%  dir
        self.barcodereader = barcodereader # name of the command line utility that processes image file containing the barcode image and prints the barcode to stdout
        self.csvfilename = csvfilename # name of the csv file to write the barcodes with their row and col
        self.delimiter = delimiter # field delimiter in csv file (default = ',')
        self.cleanup = cleanup # if 1, remove all created box image files when finished
        self.tmpdir = tmpdir
        #self.opencsv = opencsv # should open the csv file (probably in excel - using 'start CSVFILENAME') when finished?
        self.leavemissingempty = leavemissingempty # should the position in csv file for the unrecognized barcode be left empty 
        #(to easy spot which position is missing); if not set, than the missing position will not be listed in CSV file at all
        self.csvfieldorder = csvfieldorder # order of the csv fields (labels of columns), default: "row,col,barcode"
        #either list of field names or a string containing comma separated field names
        self.csvdir = csvdir # in what folder to store csv files
        
        self._inited = False
        self._filenames = [] # full path filenames of image created during cutting the image to the matrix boxes
        self._barcodes = [] # list of tuples (row, col, barcodes) obtained during run
        self._failed = [] # list of image file names not processed correctly
        self._datadir_created = False
        
        self._message = '' # set to a message describing what is beeing done right now (for the in thread operation)
        self._current_item = 0 # for showing the progress of the thread operation
        self._item_count = 0
        self.finished = False # set true upon end of the run method
        
    def _init(self):
        if self._inited:
            return
        self._inited = True
        self.margin_top = self.margin
        self.margin_right = self.margin
        self.margin_bottom = self.margin
        self.margin_left = self.margin
        if not self.tmpdir:
            self.tmpdir = tempfile.gettempdir()
        filenames = glob.glob(self.filemask)
        if not filenames:
            self.raiseError('No file matching "%s" found.' % self.filemask)
        filenames.sort()
        self.filename = filenames[-1]
        log.info('Scanning file "%s" for bacodes...' % self.filename)
        filedir, base_ext = os.path.split(self.filename)
        if not self.datadir:
            self.datadir = os.path.join(self.tmpdir, base_ext + '.tmp')
            if not os.path.exists(self.datadir):
                os.mkdir(self.datadir)
                self._datadir_created = True
            
        base, ext = os.path.splitext(base_ext)
        if not self.basename:
            self.basename = base
        if not self.fileext:
            self.fileext = ext
        if not self.csvfilename:
            d = self.csvdir
            if not d:
                d = self.datadir
            self.csvfilename = os.path.join(d, base + '.csv')
        if isinstance(self.matrixsize, basestring):
            self.matrixsize = [int(i) for i in self.matrixsize.split(',')]
        else:
            if self.matrixsize is None:
                self.matrixsize = (8, 12)
        if isinstance(self.origin, basestring):
            self.origin = [int(i) for i in self.origin.split(',')]
        if self.origin is None:
            self.origin = (0, 0)
        if not self.rowtype:
            self.rowtype = 'A'
        if not self.coltype:
            self.coltype = '1'
        if isinstance(self.boxsize, basestring):
            self.boxsize = [int(i) for i in self.boxsize.split(',')]
        if not self.delimiter:
            self.delimiter = ','
        if isinstance(self.csvfieldorder, basestring):
            self.csvfieldorder = [f.strip() for f in self.csvfieldorder.split(',')]
        if self.csvfieldorder:
            self._csvfieldorder = []
            for n in self.csvfieldorder: #['row','col','barcode'] is the default
                self._csvfieldorder.append(CSV_FIELD_NAMES.index(n))
        else:
            self._csvfieldorder = None

    def raiseError(self, msg):
        log.critical(msg)
        raise ImgMatrixError(msg)
    
    def getlbl(self, i, ltype='1', maxindex=0):
        """For given index of the row or column return its label give the labeltype ltype
        ltype is '1' or 'A'. If 'd' is appended ('1d' or 'Ad'), then descening order label is returned
        and correct maxindex must be supplied (maximal index of the row or col)
        """
        if ltype[0] in ['1', '0']:
            if len(ltype) == 1:
                return str(i + int(ltype[0]))
            else:
                return str(maxindex - i + int(ltype[0]))
        elif ltype[0] == 'A':
            if len(ltype) == 1:
                return chr(ord(ltype[0]) + i)
            else:
                return chr(ord(ltype[0]) + maxindex - i)
            
    def getcollbl(self, i):
        return self.getlbl(i, self.coltype, self.matrixsize[1] - 1)
    def getrowlbl(self, i):
        return self.getlbl(i, self.rowtype, self.matrixsize[0] - 1)
    def getrowcolsuf(self, row, col):
        return '_' + self.getrowlbl(row) + '_' + self.getcollbl(col)

    def getboxfilename(self, row, col):
        return os.path.join(self.datadir, self.basename + self.getrowcolsuf(row, col) + self.fileext)

    def clean(self):
        """Remove all box image files created during create_box_images"""
        for f in self._filenames:
            os.remove(f)
        if self._datadir_created:
            os.remove(self.datadir)

    def __call__(self):
        """For threading. Use ._current_item, ._item_count to check the progress."""
        self.run()
        
    def run(self):
        try:
            log.info('imgmatrix begin')
            self._init()
            self.starttime = datetime.datetime.now()
            self.create_box_images()
            self.read_barcodes()
            self.write_csv_file()
            log.info('imgmatrix end')
            if self.cleanup:
                self.clean()
            log.info('Result written to "%s". Barcodes found:' % self.csvfilename)
            for b in self._barcodes:
                log.info(b)
            if self._failed:
                log.error('FAILED to parse:')
                for f in self._failed:
                    log.error(f)
            #if self.opencsv:
            #    os.system('start "" "%s"' % self.csvfilename)
            self.stoptime = datetime.datetime.now()
            log.info('Time spent on the task: %s seconds' % (self.stoptime-self.starttime).seconds)
        finally:
            self.finished = True
        return self._barcodes, self._failed

    def write_csv_file(self, barcodes=[], filename='', delimiter=''):
        if not barcodes:
            barcodes = self._barcodes
        if not filename:
            filename = self.csvfilename
        if not delimiter:
            delimiter = self.delimiter
        f = open(filename, 'w')
        f.write('\n'.join([delimiter.join(self.getFields(rcb)) for rcb in barcodes]))
        f.close()

    def getFields(self, rcb):
        """If csvfieldorder defined, reorder rcb (=row,col,barcode) values list accordingly and return it"""
        if not self._csvfieldorder:
            return rcb
        values = []
        for i in self._csvfieldorder:
            values.append(rcb[i])
        return values
    def read_barcodes(self, files=[]):
        """For each file specified in files call dmtxread.ext - 2D DataMatrix barcode reader, return the corresponding barcodes
        in list of tuples: [(row, col, barcode), ...]
        
        The file names in files must contain at the end of the file name (befor extension) suffix *_row_col.*
        """
        self._message = 'Parsing barcodes'
        self._barcodes = []
        if not files:
            files = self._filenames
        self._item_count = len(files)
        for self._current_item, f in enumerate(files):
            r = self.read_barcode(f)
            if r:
                self._barcodes.append(r)
            if (not r) or (r[0] == ''):
                self._failed.append(f)
        return self._barcodes

    def read_barcode(self, filename):
        """For given image file containing one barcode run the program self.barcodereader
        to recognize the barcode.
        
        The filename can contain row and col as the last parts of the filename (excluding
        extension) separated by '_'. This is useful if a plate is split into separate
        image files to keep a track of their origin.
        
        Return tuple (row, col, barcode) (all of it can be '').
        
        If self.leavemissingempty = False, then None is returned instead of the tuple
        if no barcode found.
        """
        self._init()
        path, base_ext = os.path.split(filename)
        base, ext = os.path.splitext(base_ext)
        rowcol = base.split('_')[-2:]
        if len(rowcol) == 2:
            row, col = rowcol
        else:
            row, col = '', ''
        retryCount = 3
        deg = 45
        dif = 15
        fn = filename # fn - original file name, filename gets changed upon retries

        
        return filename
        



        while retryCount:
            log.info('read_barcode from "%s" ...' % filename)
            print('read_barcode from "%s" ...' % filename)
            p = subprocess.Popen('dmtxread "%s"' % filename, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV)
            o, e = p.communicate()
            if e:
                log.warning('read_barcode from "%s" failed: %s' % (filename, e))
            else:
                if o:
                    log.info('read_barcode - found: %s' % o)
                    return (row, col, o)
                else:
                    log.warning(' barcode not found ...')
            retryCount -= 1
            if retryCount:
                filename = os.path.join(self.tmpdir, base + ('_%s' % deg) + ext)
                log.info(' rotating image "%s" by %s deg to "%s" for barcode reading retry' % (fn, deg, filename))
                im = Image.open(fn)
                im2 = im.rotate(deg)

                im2.save(filename)
                deg += dif
            
        log.error('read_barcode from "%s" - no code found' % fn)
        if self.leavemissingempty:
            return ('','','')
        
    def read_barcode_test(self, filename):
        """Find out if the barcode parser is functioning.
        
        If not return text describing the problem.
        Should be used by the caller before first call to read_barcode, 
        with filename set to some default preinstalled testing 2D barcode 
        image file.
        """
        
    def create_box_images(self):
        self._message = 'Creating box images'
        self._init()
        img = Image.open(self.filename)
        p = img.load()
        y = self.origin[1]
        row = 0
        if not self.boxsize:
            self.boxsize = [round(float(img.size[0] - 2 * self.origin[0])/ self.matrixsize[1]), round(float(img.size[1] - 2 * self.origin[1]) / self.matrixsize[0])]
        self._item_count = 96 # do it one day more clever ...
        self._current_item = 0
        while y < (img.size[1] - self.boxsize[1]):
            x = self.origin[0]
            col = 0
            while x < (img.size[0] - self.boxsize[0]):
                i = Image.new(img.mode, self.boxsize)
                pi = i.load()
                for ix in range(self.boxsize[0]):
                    for iy in range(self.boxsize[1]):
                        pi[ix, iy] = p[x + ix, y + iy]
                fn = self.getboxfilename(row, col)
                i.save(fn)
                self._filenames.append(fn)
                col += 1
                if col == self.matrixsize[1]:
                    break
                x += self.boxsize[0]
            if col != self.matrixsize[1]:
                self.raiseError('Found just %s columns instead of %s' % (col, self.matrixsize[1]))
            y += self.boxsize[1]
            row += 1
            if row == self.matrixsize[0]:
                break
            self._current_item += 1
        if row != self.matrixsize[0]:
            self.raiseError('Found just %s rows instead of %s' % (row, self.matrixsize[0]))
        return self._filenames

def main():
    #if not hasattr(logging, 'basicConfig'):
    #    log.addHandler(logging.StreamHandler())
    #    log.setLevel(logging.INFO)
    #else:
    logging.basicConfig(level=logging.INFO)
    
    #2011-02-28 fi-60f scanner, 600 dpi
    pars3 = {
           'filemask':'C:\\Documents and Settings\\jindrich\\My Documents\\image002-grayscale-default.tif',
           'origin':'165,257', 
           'matrixsize':'12, 8', 
           'boxsize':'210,210', 
           'rowtype':'1',
           'coltype':'A'
    }
    
    
    #2011-02-28 fi-60f scanner, 600 dpi
    pars2 = {
           'filemask':'C:\\Documents and Settings\\jindrich\\My Documents\\image003-color256.tif',
           'origin':'165,257', 
           'matrixsize':'12, 8', 
           'boxsize':'210,210', 
           'rowtype':'1',
           'coltype':'A'
    }

    #600dpi
    pars1 = {'filemask':'C:\\D\\2D-barcodes\\scantest2d600.tif',
           'origin':'260,142', 
           'matrixsize':'8, 12', 
           'boxsize':'210,210', 
           'rowtype':'A-',
           'coltype':'1-'
    }
    #read all images ok for 600 dpi for .tif images only (jpg, png failed one or two reads)
    
    #300dpi
    pars = {'filemask':'C:\\D\\2D-barcodes\\scantest2d300.jpg',
           'origin':(130,75), 
           'matrixsize':(8, 12), 
           'boxsize':(105,105), 
           'rowtype':'A-'
    }
    #failed to read 3 images for 300 dpi

    
    im = ImgMatrix(**pars3)
    bcs, failed = im.run()
    print 'written to "%s"' % im.csvfilename
    for b in bcs:
        print b
    if failed:
        print 'FAILED:'
        for f in failed:
            print f

def check_imagemagick(imagemagick=IMAGE_MAGICK):
    """Check if ImageMagick (of given version subfolder) is installed and in PATH.
    Return '' if everything ok, otherwise return the error message.
    """
    global IMAGE_MAGICK_FOLDER, ENV, TEST_CMD
    
    folder = ''
    lines = []
    for pfn in ['ProgramFiles(x86)', 'ProgramFiles']:
        pf = os.environ.get(pfn)
        if not pf:
            msg = 'Env.var %s is empty.' % pfn
            if pfn == 'ProgramFiles':
                log.error(msg)
                lines.append(msg)
            else:
                log.debug(msg)
            continue
        
        subnames = [imagemagick, imagemagick.split('-', 1)[0]+ '*']
        for subname in subnames:
            mask = os.path.join(pf, subname)
            subs = glob.glob(mask)
            if not subs:
                msg = 'No folder found for mask: %s .' % mask
                if subname == imagemagick:
                    log.warning(msg) # the default subfolder for image magick is not present, give a warning
                else:
                    log.error(msg) # not even any other imagemagick version folder is present give an error
                lines.append(msg)
                continue
            if len(subs) > 1:
                msg = 'More folders found for mask %s: %s .' % (mask, subs)
                log.warning(msg)
                lines.append(msg)
            sub = subs[0]
            folder = os.path.join(pf, sub)
            #folder with imagemagick found
            IMAGE_MAGICK_FOLDER = folder
            break
        
        break
    
    #try to run program identify.exe which should be in this folder
    #if it fails, it might mean the folder is not in PATH
    res = procutl.run(TEST_CMD, env=ENV)
    if res['resultcode'] != 0:
        folder_msg = ''
        if folder:
            # try to add the folder to PATH and run again
            wres = winenv.update_env_var('PATH', folder, 'add')
            ENV = os.environ.copy()
            if wres['result'] != 0:
                log.error('Attempt to add %s to PATH failed: %s' % (folder, wres['error_message']))
            else:
                wres = winenv.update_env_var('PATH', '', 'get')
                if wres['oldvalue'].find(folder) >= 0:
                    folder_msg = 'Folder %s added to PATH. Restart the the RackScanner/computer to reflect the change, if you encounter problems.' % folder
                    
            if ENV['PATH'].find(IMAGE_MAGICK_FOLDER ) < 0:
                ENV['PATH'] = IMAGE_MAGICK_FOLDER  + os.pathsep + ENV['PATH']
            res = procutl.run(TEST_CMD, env=ENV)
        if res['resultcode'] != 0:
            msg = 'Test run of ImageMagick %s.exe failed: %s.' % (TEST_CMD, res)
            log.error(msg)
            lines.append(msg)
            if folder:
                if folder_msg:
                    msg = folder_msg
                else:
                    msg = 'ImageMagick folder %s might not be in PATH environmental variable. Add it there and restart the RackScanner/computer.' % folder
                log.error(msg)
                lines.append(msg)
    else:
        #ignore all previous error/warning messages, if identify is running ok
        lines = []
    
    return '\n'.join(lines)

def cmd():
    logging.basicConfig(level=logging.INFO, filename='imgmatrix.log')
    log.addHandler(logging.StreamHandler())
    from jipylib import cmdline
    i = cmdline.CmdLineWrap(ImgMatrix)
    i.run()
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #cmd()
    print check_imagemagick()
