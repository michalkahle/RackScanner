
""" https://github.com/denisenkom/pytwain """    
import platform
if platform.system() == 'Windows':
    import twain

class TwainutlError(Exception):
    pass

scanner_defaults = {  
    'pixeltype' : 2, # 0: BW, 1: grayscale, 2: RGB
    'resolution' : 600.0,
    'autocrop' : 0,
    'left' : 0,
    'top' : 0,
    'right' : 3.5,
    'bottom' : 5,
}

# override defaults here
scanners = {
    'AVA6' : {}
}

def scan(fullfilename = 'dg_pic.bmp', **kwargs):
    sm, scanner = open_scanner()
    try:
        adjust_scanner_properties(scanner, **kwargs)
        scanner.RequestAcquire(0, 0) # 1,1 to show scanner user interface
        (handle, more_to_come) = scanner.XferImageNatively()
        twain.DIBToBMFile(handle, fullfilename)
        twain.GlobalHandleFree(handle)
    finally:
        scanner.destroy()
        sm.destroy()

def adjust_scanner_properties(scanner, **kwargs):
    params = scanner_defaults.copy()
    params.update(kwargs)
    scanner_type = scanner.GetSourceName()
    if scanner_type in scanners:
        params.update(scanners[scanner_type])
    # Layout = scanner.GetImageLayout()
    DocNumber, PageNumber, FrameNumber = 1, 1, 1
    frame = tuple(float(params[key]) for key in ['left', 'top', 'right', 'bottom'])
    scanner.SetImageLayout(frame, DocNumber, PageNumber, FrameNumber)
    # scanner.GetCapability(twain.ICAP_PIXELTYPE)
    scanner.SetCapability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, int(params['pixeltype']))
    scanner.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, float(params['resolution'])) 
    scanner.SetCapability(twain.ICAP_AUTOMATICBORDERDETECTION, twain.TWTY_BOOL, 0) # autocrop
    # 'deskew': twain.ICAP_AUTOMATICDESKEW,
    # 'barcodes': twain.ICAP_BARCODEDETECTIONENABLED,

def open_scanner():
    sm = twain.SourceManager(0)
    sourcenames = sm.GetSourceList()
    if len(sourcenames) == 0:
        raise TwainutlError('No TWAIN sources available.')
    elif len(sourcenames) == 1:
        scanner = sm.OpenSource(sourcenames[0])
    else:
        scanner = sm.OpenSource() # select interactively
    return sm, scanner