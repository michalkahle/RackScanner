
"""
import twain
sm = twain.SourceManager(0)
ss = sm.OpenSource()
ss.RequestAcquire(0,0)
rv = ss.XferImageNatively()
if rv:
    (handle, count) = rv
    twain.DIBToBMFile(handle, 'image.bmp')
"""    

"""
2011-03-28
http://twainmodule.sourceforge.net/docs/demo_base.html = twain_1.0.3/demo/simple_base.py TwainBase

see class TwainCtl(TwainBase) below for usable class: TwainCtl(sourcename=SOURCENAME).run() should do all

If you do not know the SOURCENAME just run it for the first time without this parameter and find it out.

"""

import sys
import os
import time
import datetime
import logging
import traceback

import twain

log = logging.getLogger('jipylib.twainutl')

XferByFile='File'
XferNatively='Natively'

tmpfilename="tmp.bmp"
OverrideXferFileName = 'c:/twainxfer.jpg'

BOOL_CAPS_DIC = {
    'autocrop': twain.ICAP_AUTOMATICBORDERDETECTION,
    'deskew': twain.ICAP_AUTOMATICDESKEW,
    'barcodes': twain.ICAP_BARCODEDETECTIONENABLED,
}
class TwainutlError(Exception):
    pass

class CannotWriteTransferFile(Exception):
    pass

class TwainBase:
    """Simple Base Class for twain functionality. This class should
    work with all the windows librarys, i.e. wxPython, pyGTK and Tk.
    """

    SM=None                        # Source Manager
    SD=None                        # Data Source
    ProductName='SimpleTwainDemo'  # Name of this product
    XferMethod = XferNatively      # Transfer method currently in use
    AcquirePending = False         # Flag to indicate that there is an acquire pending
    mainWindow = None              # Window handle for the application window

    # Methods to be implemented by Sub-Class
    def LogMessage(self, message):
        print "****LogMessage:", message

    def DisplayImage(self, ImageFileName):
        """Display the image from a file"""
        print "DisplayImage:", message

    # End of required methods


    def Initialise(self):
        """Set up the variables used by this class"""
        (self.SD, self.SM) = (None, None)
        self.ProductName='SimpleTwainDemo'
        self.XferMethod = XferNatively
        self.AcquirePending = False
        self.mainWindow = None

    def Terminate(self):
        """Destroy the data source and source manager objects."""
        if self.SD: self.SD.destroy()
        if self.SM: self.SM.destroy()
        (self.SD, self.SM) = (None, None)

    def OpenScanner(self, mainWindow=None, ProductName=None, UseCallback=False):
        """Connect to the scanner"""
        if ProductName: self.ProductName = ProductName
        if mainWindow: self.mainWindow = mainWindow
        if not self.SM:
            self.SM = twain.SourceManager(self.mainWindow, ProductName=self.ProductName)
        if not self.SM:
            return
        if self.SD:
            self.SD.destroy()
            self.SD=None
        self.SD = self.SM.OpenSource()
        if self.SD:
            self.LogMessage(self.ProductName+': ' + self.SD.GetSourceName())

        if UseCallback:
            self.SM.SetCallback(self.OnTwainEvent)
    
    def _Acquire(self):
        """Begin the acquisition process. The actual acquisition will be notified by 
        either polling or a callback function."""
        if not self.SD:
            self.OpenScanner()
        if not self.SD: return
        try:
            self.SD.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, 100.0) 
        except:
            pass
        self.SD.RequestAcquire(0, 0)  # 1,1 to show scanner user interface
        self.AcquirePending=True
        self.LogMessage(self.ProductName + ':' + 'Waiting for Scanner')

    def AcquireNatively(self):
        """Acquire Natively - this is a memory based transfer"""
        self.XferMethod = XferNatively
        return self._Acquire()

    def AcquireByFile(self):
        """Acquire by file"""
        self.XferMethod = XferByFile
        return self._Acquire()

    def PollForImage(self):
        """This is a polling mechanism. Get the image without relying on the callback."""
        if self.AcquirePending:
            Info = self.SD.GetImageInfo()
            if Info:
                self.AcquirePending = False
                self.ProcessXFer()

    def ProcessXFer(self):
        """An image is ready at the scanner - fetch and display it"""
        more_to_come = False
        try:
            if self.XferMethod == XferNatively:
                XferFileName=tmpfilename
                (handle, more_to_come) = self.SD.XferImageNatively()
                twain.DIBToBMFile(handle, XferFileName)
                twain.GlobalHandleFree(handle)
                self.LogMessage(self.ProductName + ':' + 'Image acquired natively')
            else:
                try:
                    XferFileName='TWAIN.TMP' # Default
                    rv = self.SD.GetXferFileName()
                    if rv:
                        (XferFileName, type) = rv

                    # Verify that the transfer file can be produced. Security 
                    # configurations on windows can prevent it working.
                    try:
                        self.VerifyCanWrite(XferFileName)
                    except CannotWriteTransferFile:
                        self.SD.SetXferFileName(OverrideXferFileName)
                        XferFileName = OverrideXferFileName

                except:
                    # Functionality to influence file name is not implemented.
                    # The default is 'TWAIN.TMP'
                    pass

                self.VerifyCanWrite(XferFileName)
                self.SD.XferImageByFile()
                self.LogMessage(self.ProductName + ':' + "Image acquired by file (%s)" % XferFileName)

            self.DisplayImage(XferFileName)
            if more_to_come: self.AcquirePending = True
            else: self.SD = None
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])

    def OnTwainEvent(self, event):
        """This is an event handler for the twain event. It is called 
        by the thread that set up the callback in the first place.

        It is only reliable on wxPython. Otherwise use the Polling mechanism above.
        
        """
        try:
            if event == twain.MSG_XFERREADY:
                self.AcquirePending = False
                self.ProcessXFer()
            elif event == twain.MSG_CLOSEDSREQ:
                self.SD = None
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])

    def VerifyCanWrite(self, filepath):
        """The scanner can have a configuration with a transfer file that cannot
        be created. This method raises an exception for this case."""
        parts = os.path.split(filepath)
        if parts[0]:
            dirpart=parts[0]
        else:
            dirpart='.'
        if not os.access(dirpart, os.W_OK):
            raise CannotWriteTransferFile, filepath

class TwainCtl(TwainBase):
    """Supply all needed parameters in __init___"""
    def __init__(self, 
                 sourcename='AVA6', # name of the scanner, if not specified, dialog to choose one will be shown
                 filemask='twain_%Y-%m-%d_%H-%M-%S.bmp', # file name of the image file to create, can contain time formatting params
                 # if not folder part is given it will be stored in the 'folder' (see below)
                 folder='c:\\tmp\\twain', # folder where the scanned images should be stored
                 interactive=0, # should the TWAIN user interface window be shown
                 transfermethod='natively', # how the scanned image is obtained:
                 # 'file' ... written to the specified file
                 # 'nativ[ely]' ... over memory
                 resolution=600.0, # scanner resolution DPI
                 timeout=60, # how long max. (in seconds) to wait for the image to get scanned
                 sleeptime=0.1, # how long to sleep between consecutive poll calls
                 displayimage=True, # should the acquired image be opened on the screen? (preview)
                 right=None, # right margin of the image layout
                 bottom=None, # bottom margin of the image layout
                 left=None,
                 top=None,
                 pixeltype=None, # 0 - B/W, 1 - GRAY, 2 - RGB
                 autocrop=None, # try to detect the scanned object borders?
                 deskew=None,
                 **kwargs
                ):
        self.sourcename = sourcename
        self.transfermethod = transfermethod
        self.filemask = filemask
        self.folder = folder
        self.interactive = interactive
        self.resolution = resolution
        self.timeout = timeout
        self.sleeptime = sleeptime
        self.displayimage = displayimage
        self.right = right
        self.bottom = bottom
        self.left = left
        self.top = top
        self.pixeltype = pixeltype
        self.autocrop = autocrop
        self.deskew = deskew
        
        self._inited = False
    
    
    # Methods to be implemented by Sub-Class
    def LogMessage(self, message):
        log.info(message)

    def adjustPixelType(self):
        if self.pixeltype is None:
            return
        self.pixeltype = int(self.pixeltype)

        res = self.SD.GetCapability(twain.ICAP_PIXELTYPE)
        log.info('self.SD.GetCapability(twain.ICAP_PIXELTYPE): %s' % str(res))
        a, (m, n, [x, y, z]) = res
        try:
            res2 = a, (m, n, [x, self.pixeltype, z])
            self.SD.SetCapability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, self.pixeltype) # or UINT16?
            log.info('self.SD.GetCapability(twain.ICAP_PIXELTYPE, TWTY_UINT16, %s)' % self.pixeltype)
        except:
            log.error('self.SD.SetCapability(ICAP_PIXELTYPE, %s) failed: (%s, %s)' % (res2, sys.exc_info[0], sys.exc_info[1]))
        
    def boolCap(self, cap, onOff=None):
        """Get/set the given boolean capability (see twain.CAP... or twain.ICAP..).
        Return the previously set value. If onOff=None, leave the value unchanged.
        If onOff==1 set the capability on, if onOff==0 set the capability off.
        
        Common text shortcuts which can be used for cap (will be translated to twain.CAP_XXX):
        'autocrop'
        """
        try:
            cap = BOOL_CAPS_DIC.get(cap, cap)
                
            res = self.SD.GetCapability(cap)
            if not onOff is None:
                self.SD.SetCapability(cap, twain.TWTY_BOOL, onOff)
                log.info('self.SD.SetCapability(%s, twain.TWTY_BOOL, %s)' % (cap, onOff))
            else:
                log.info('self.SD.GetCapability(%s)' % cap)
        except:
            log.error('self.boolCap(%s, %s) failed: (%s, %s)' % (cap, onOff, sys.exc_info()[0], sys.exc_info[1]))
        
    def adjustLayout(self):
        """If right or bottom margin defined, try to set the new image layout
        See twexplore.py
        """
        if (self.right is None) and (self.bottom is None) and (self.top is None) and (self.left is None):
            return
        log.info("self.SD.GetImageLayout()")
        try:
            Layout = self.SD.GetImageLayout()
        except:
            #self.Control.DisplayException("self.SS.GetImageLayout")
            log.error('self.SD.GetImageLaout error (%s, %s)' % sys.exc_info()[:2])
            return
        (frame, DocNumber, PageNumber, FrameNumber) = Layout
        left, top, right, bottom = frame
        
        log.info("self.SD.GetImageLayout(): (%f, %f, %f, %f), %d, %d, %d)" %
                (left, top, right, bottom, DocNumber, PageNumber, FrameNumber))
        
        if not self.right is None:
            right = float(self.right)
        if not self.bottom is None:
            bottom = float(self.bottom)
        if not self.left is None:
            left = float(self.left)
        if not self.top is None:
            top = float(self.top)
        try:
            log.info("self.SD.SetImageLayout((%f, %f, %f, %f), %d, %d, %d)" %
                (left, top, right, bottom, DocNumber, PageNumber, FrameNumber))
            self.SD.SetImageLayout((left, top, right, bottom), DocNumber, PageNumber, FrameNumber)
        except:
            log.error("self.SD.SetImageLayout (%s %s)" % sys.exc_info()[:2])
        
    def adjustSettings(self):
        if not self.autocrop is None:
            self.boolCap('autocrop', int(self.autocrop))
        if not self.deskew is None:
            self.boolCap('deskew', int(self.deskew))
        
    def DisplayImage(self, ImageFileName):
        """Display the image from a file"""
        #print "DisplayImage:", message
        if self.displayimage:
            log.info('Displaying: %s' % ImageFileName)
            os.system('start %s' % ImageFileName)
    # End of required methods
    
    def OpenScanner(self, mainWindow=None, ProductName=None, UseCallback=False):
        """Connect to the scanner"""
        if ProductName: self.ProductName = ProductName
        if mainWindow is not None: self.mainWindow = mainWindow
        if not self.SM:
            self.SM = twain.SourceManager(self.mainWindow, ProductName=self.ProductName)
        if not self.SM:
            return
        if self.SD:
            self.SD.destroy()
            self.SD=None
        self.sourcenames = self.SM.GetSourceList()
        log.info('Available TWAIN sources: ' + ';'.join(self.sourcenames))
        if len(self.sourcenames) == 0:
            log.error('No TWAIN sources available.')
            return
        if self.sourcename:
            if not self.sourcename in self.sourcenames:
                log.warning('Requested sourcename %s not present.' % self.sourcename)
                self.sourcename = ''
        if not self.sourcename:
            #no existing sourcename specified
            if len(self.sourcenames) == 1:
                #set the only one available
                self.sourcename = self.sourcenames[0]
        if self.sourcename:
            self.SD = self.SM.OpenSource(self.sourcename)
        else:
            #more sources available, select interactively
            self.SD = self.SM.OpenSource()
        if self.SD:
            self.LogMessage(self.ProductName+': ' + self.SD.GetSourceName())

        if UseCallback:
            self.SM.SetCallback(self.OnTwainEvent)
            
    def _Acquire(self):
        """Begin the acquisition process. The actual acquisition will be notified by 
        either polling or a callback function."""
        if not self.SD:
            self.OpenScanner()
        if not self.SD: 
            return
        
        self.adjustLayout()
        self.adjustPixelType()
        self.adjustSettings()
        try:
            self.SD.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, self.resolution) 
        except:
            pass
        if self.interactive:
            self.SD.RequestAcquire(1, 1)   # 1,1 to show scanner user interface
        else:
            self.SD.RequestAcquire(0, 0)
        self.AcquirePending=True
        self.LogMessage(self.ProductName + ':' + 'Waiting for Scanner')
    
        
    def __del__(self):
        self.Terminate()
        
    def _init(self):
        if self._inited:
            return
        self._inited = True
        self.Initialise()
        
        if self.transfermethod.lower() == 'file':
            self.XferMethod = XferByFile
        elif self.transfermethod.lower().startswith('nativ'):
            self.XferMethod = XferNatively
        else:
            self.raiseError('Invalid tansfer method %s' % self.transfermethod)
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        path, nameext = os.path.split(self.filemask)
        if not path:
            path = self.folder
        self.filename = time.strftime(os.path.join(path, nameext))
        
        self.timeout = float(self.timeout)
        self.sleeptime = float(self.sleeptime)
            
    def raiseError(self, msg):
        log.error(msg)
        raise TwainutlError(msg)
    
    def run(self):
        """Do all the necessary steps to acquire the image and save it to file.
        Using the parameters supplied in __init__ method (eventually modified after that).
        """
        self._init()
        self.OpenScanner(0)
        self._Acquire()
        start = datetime.datetime.now()
        while self.AcquirePending:
            self.PollForImage()
            if (datetime.datetime.now() - start).seconds > self.timeout:
                log.error('Scanning timed out.')
                break
        
        #sm = twain.SourceManager(0)
        #ss = sm.OpenSource()
        #ss.RequestAcquire(0,0)
        #rv = ss.XferImageNatively()
        #if rv:
        #    (handle, count) = rv
        #    twain.DIBToBMFile(handle, 'image.bmp')

        log.info('acquired: %s' % self.filename)
    
    def ProcessXFer(self):
        """An image is ready at the scanner - fetch and display it"""
        more_to_come = False
        try:
            if self.XferMethod == XferNatively:
                XferFileName=self.filename
                (handle, more_to_come) = self.SD.XferImageNatively()
                twain.DIBToBMFile(handle, XferFileName)
                twain.GlobalHandleFree(handle)
                self.LogMessage(self.ProductName + ':' + 'Image acquired natively')
            else:
                try:
                    XferFileName=self.filename #'TWAIN.TMP' # Default
                    rv = self.SD.GetXferFileName()
                    if rv:
                        (XferFileName, type) = rv

                    # Verify that the transfer file can be produced. Security 
                    # configurations on windows can prevent it working.
                    try:
                        self.VerifyCanWrite(XferFileName)
                    except CannotWriteTransferFile:
                        self.SD.SetXferFileName(OverrideXferFileName)
                        XferFileName = OverrideXferFileName

                except:
                    # Functionality to influence file name is not implemented.
                    # The default is 'TWAIN.TMP'
                    pass

                self.VerifyCanWrite(XferFileName)
                self.SD.XferImageByFile()
                self.LogMessage(self.ProductName + ':' + "Image acquired by file (%s)" % XferFileName)
                
            self.DisplayImage(XferFileName)
            #self.filename = XferFileName
            if more_to_come: self.AcquirePending = True
            else: self.SD = None
        except:
            # Display information about the exception
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2])
        
        
if __name__ == '__main__':
    from jipylib import cmdline
    t = cmdline.CmdLineWrap(TwainCtl, left=0, top=0, right=0.5, bottom=0.5, pixeltype=2)
    t.run()
    