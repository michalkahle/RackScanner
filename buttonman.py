"""Module to work with Avision "Button Manager" application

Read the current Button Manager settings - folders where the scanned files
are placed.
"""
import os
import sys
import glob
import shutil

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except:
        json = None
    

#from jipylib import inifile as ifile
import utils

PIC_INFOS = {'1':{'name':'BMP','ext':'.bmp'},
             '2':{'name':'TIFF','ext':'.tif'},
             '3':{'name':'JPEG','ext':'.jpg'},
             '4':{'name':'GIF', 'ext':'.gif'}
}

CUSTOM = 'custom - 0.50 x 0.50 Inch'
MAXIMUM = 'Scanner Maximum'

class ButtonError(Exception):
    pass

class ButtonInfo:
    def __init__(self, manager, number):
        self.manager = manager
        self.number = str(number)
        self.ini = utils.AttrDict(ifile.load(self.manager.inifile, section=self.number))
        """
[1]
path=C:\Button_Data\
fileName=Image###
file_FileNameMethod=3
file_MultiPage=0
file_MultiPageNum=2
folder=2
zNum=3
pdfCompression=3
pdfRecognition=-1
pdfSecure=
pdfA=0
pdfSegmentation=1
ID_CARD=0
list2Sel=0
apPath=C:\WINDOWS\system32\mspaint.exe
property=1
tittleName=Single tube (L)
dpi=600
list1Str=custom - 0.50 x 0.50 Inch
list1Sel=2
imageType=8
picFormat=2
pdfCompresion=3
        """
    def get_folder(self):
        """Return path to the folder where scanned image files are stored"""
        pic_info = PIC_INFOS[self.ini.picFormat]
        return os.path.join(self.ini.path, pic_info['name'])
    
        
    def get_backup_folder(self):
        f = os.path.join(self.get_folder(), 'backup')
        if not os.path.exists(f):
            os.mkdir(f)
        return f
    
    def get_filemask(self):
        """Return full path filemask (wildcard) for files created by this button.
        To be used by glob
        """
        pic_info = PIC_INFOS[self.ini.picFormat]
        return os.path.join(self.get_folder(), self.get_filebase() + '*' + pic_info['ext'])
    
    def get_filebase(self):
        """Get basename for files created by this button.
        
        Should be 'vial' or 'rack'.
        """
        return self.ini.fileName.strip('#')
    
    def get_latestfile(self):
        """Return name of the newest file in the folder or '' if none found"""
        files = glob.glob(self.get_filemask())
        if files:
            files.sort()
            return files[-1]
        else:
            return ''
        
    def hide_file(self, filename):
        """Hide the image file which was worked up to backup folder"""
        bfn = os.path.join(self.get_backup_folder(), os.path.split(filename)[-1])
        shutil.move(filename, bfn)

    def get_dic(self):
        if self.number == '1':
            fileName = 'vial###'
            apPath = os.path.join(self.manager.get_bat_folder(), 'start_vial.bat')
            tittleName = 'Single vial (L)'
            list1Str = CUSTOM
        else:
            fileName = 'rack###'
            apPath = os.path.join(self.manager.get_bat_folder(), 'start_rack.bat')
            tittleName = 'Rack (R)'
            list1Str = MAXIMUM
            
        dic = {
            'path': 'C:\\Button_Data\\',
            'fileName': fileName,
            'file_FileNameMethod':'3',
            'file_MultiPage':'0',
            'file_MultiPageNum':'2',
            'folder':'2',
            'zNum':'3',
            'pdfCompression':'3',
            'pdfRecognition':'-1',
            'pdfSecure':'',
            'pdfA':'0',
            'pdfSegmentation':'1',
            'ID_CARD':'0',
            'list2Sel':'0',
            'apPath': apPath,
            'property':'1',
            'tittleName': tittleName,
            'dpi':'600',
            'list1Str': list1Str,
            'list1Sel':'2',
            'imageType':'24', # color
            'picFormat':'1', # bmp
            'pdfCompresion':'3',
        }
        return dic

    
    def check_ini(self):
        """Check if there is some incorrect ini variable in Button ini files.
        If yes, recreate all ini files.
        
        Return '' if no changes were made to ini files, otherwise the
        return text (error) massage describing what was/should done.
        """
        msg = ''
        modified = 'Avision Button Manager configuration files were modified, please restart the computer.'
        if self.number == '1':
            #vial scanning
            if not self.ini.fileName.startswith('vial'):
                #modify the ini for vial scanning (button 1)
                self.manager.save_ini()
                msg = modified
        if self.number == '2' and not modified:
            #rack scanning:
            if not self.ini.fileName.startswith('rack'):
                #modify the ini section for rack scanning (button 2)
                self.manager.save_ini()
                msg = modified
        return msg
    
        
        
class ButtonMan:
    def __init__(self, inifile='C:\\Avision_FBBM\\DATA\\AVA6\\data.ini'):
        self.inifile = inifile
        if not os.path.exists(inifile):
            raise ButtonError('Avision Button Manager is not installed (file %s not found). Please install it first.' % inifile)
        self.button1 = ButtonInfo(self, 1)
        self.button2 = ButtonInfo(self, 2)
        
    def get_inifilename(self, baseext):
        path, be = os.path.split(self.inifile)
        return os.path.join(path, baseext)
    
    def hide_file(self, filename):
        if filename.find(self.button1.get_filebase()):
            self.button1.hide_file(filename)
        elif filename.find(self.button2.get_filebase()):
            self.button2.hide_file(filename)

    def check_inis(self):
        """Check if the Avision Button Manager software ini files are modified to work
        with platescan. 
        
        Return message saying to user what should be done. ('' if nothing).
        """
        msg = self.button1.check_ini()
        if not msg:
            msg = self.button2.check_ini()
        return msg

    def get_bat_name(self, name):
        if not name.endswith('.bat'):
            name += '.bat'
        return os.path.join(self.get_bat_folder(), name)
    
    def get_bat_folder(self):
        """Return folder where start_vial.bat and start_rack.bat files are located"""
        f = os.path.dirname(__file__)
        b = 'start_rack.bat'
        
        if os.path.exists(os.path.join(f, b)):
            return f
        f = os.path.dirname(f) # buttonman.py can be also in lib subfolder in dist 
        if os.path.exists(os.path.join(f, b)):
            return f

    def save_ini(self):
        #dic = self.get_dic()
        #ifile.save(dic, self.ini.inifile, section=self.number)
        
        inis = [
            ('data.ini', [
                ('1', self.button1.get_dic()),
                ('2', self.button2.get_dic()),
            ]),
            ('data1.ini', [
                ('2', {
                'page1_tittleName': CUSTOM, 
                'page1_imageType': 24, 
                'page1_resolution': 600,
                'page1_paperLength':0,
                
                'page1_paperSize': CUSTOM,
                'page1_combo3Userdef': CUSTOM,
                }
                ),
               ('5', {
                'page1_tittleName': MAXIMUM,
                'page1_resolution': 600,
                'page1_paperLength': 0,
                'page1_paperSize': MAXIMUM,
                })]
            ),
        
            ('data2.ini', [
                ('sum', {'count':4}),
                ('2', {
                'group':'34567892',
                'apPath': self.get_bat_name('start_vial'),
                'argument':'',
                'apName':'start_vial',
                'hitFormat':1,
                'property':1,
                'hit':'19173961',
                }),
                ('3',{
                'group':'13456789',
                'apPath': self.get_bat_name('start_rack'),
                'argument':'',
                
                'apName':'start_rack',
                'hitFormat':1,
                'property':1,
                'hit':'19173961',

                })]
            ),
            
            ('scanData.ini', [
                ('1', {
                'ID_CARD': 0,
                'file_tittleName':'start_vial',
                'file_ApplicationPath': self.get_bat_name('start_vial'),
                'file_FileName':'vial###',
                'MultiFeedDetection':0,
                'Resolution':600,
                'paperLength':300,
                'paperWidth': 300,
                'file_BlankPageSkip':50,
                'scan_method':0,
                'ip_crop': 0, #automatic cropping
                'ip_deskew': 0,
                'SC':0,
                
                }),
                ('2', {
                'ID_CARD': 0,
                'file_tittleName':'start_rack',
                'file_ApplicationPath': self.get_bat_name('start_rack'),
                'file_FileName':'rack###',
                'MultiFeedDetection':0,
                'Resolution':600,
                'paperLength':3400,
                'paperWidth': 2488,
                'file_BlankPageSkip':50,
                'scan_method':0,
                'ip_crop': 0, #automatic cropping
                'ip_deskew': 0,
                'SC':0,
                
                })]
             ),
            
        ]
        
        for baseext, secvars in inis:
            filename = self.get_inifilename(baseext)
            for sec, dic in secvars:
                ifile.save(dic, filename, section=sec)


def check_inis():
    """Make sure, Button manager is installed and ini file contains platescan setup values.
    
    Return the error message(s) or '' if everything is OK.
    """
    try:
        b = ButtonMan()
        return b.check_inis()
    except Exception, e:
        return e.message

def get_latestfile(num, format='html'):
    """Called from platescan.status 
    
    I.e. this function is invoked periodically (every few seconds) by ajax calls from 
    platescan web page.
    Return the name of the latest scanned file if present, otherwise return ''.
    Also upon any error return ''. Errors should have been reported by check_inis()
    
    If format== 'json' return "{'filename': FILENAME, 'error': ERROR}"
    where FILENAME is '' or the last file name and ERROR is '' or the error message
    """
    if format == 'json':
        result = {'filename':'', 'error':''}
        try:
            num = str(num)
            b = ButtonMan()
            if num == "1":
                result['filename'] = b.button1.get_latestfile()
            elif num == "2":
                result['filename'] = b.button2.get_latestfile()
        except Exception, e:
            result['error'] = e.message
        if json:
            return json.dumps(result)
        else:
            return str(result)
    else:
        try:
            num = str(num)
            b = ButtonMan()
            if num == "1":
                return b.button1.get_latestfile()
            elif num == "2":
                return b.button2.get_latestfile()
        except:
            pass
        return ''
        
    
def test():
    b = ButtonMan()
    print b.button1.get_folder()
    print b.button2.get_filemask()
    print b.button2.get_latestfile()
    fn = b.button2.get_latestfile()
    b.button2.hide_file(fn)
    
def main():
    #return check_inis()
    return get_latestfile("2", "json")
    
if __name__ == '__main__':
    print main()