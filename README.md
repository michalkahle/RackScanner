<img align="left" height="56px" src="resources/logo.png?raw=true"/>

# RackScanner

Application for reading racks of Data Matrix barcoded tubes. Tested with Thermo Scientific Matrix tubes and racks. Can read 96-well racks, 24-well racks, and single tubes.

<img align="left" height="100px" src="resources/vial_1ml_sample.bmp"/>
<img align="left" height="500px" src="resources/rack_96_sample.bmp"/>
<img height="500px" src="resources/rack_24_sample.bmp"/>

RackScanner can read images from configurable directory or directly operate a scanner. Currently it is just one type of scanner - Avision AVA6 flatbed scanner. This scanner has only Windows 32-bit TWAIN driver. It should not be too hard to make it work with other scanners but in order to work the scanner needs to be able to focus on the plane of the tubes bottoms which is approximately 2mm above the scanner surface. Small scanner format is also a benefit - A6 in the case of AVA6.

RackScanner first localizes the wells of the rack by pattern matching and recognizes the type of the rack. It then determines which wells are empty and which contain barcoded tubes. Attempts to locate and digitize barcodes are then made by three different algorithms using the excellent and fast [OpenCV](http://opencv.org) library. Decoding is done by [libdmtx](http://libdmtx.sourceforge.net) which also serves as fallback in case that previous attempts to locate the code fail.

Original RackScanner was developed in 2011 by [jindrichjindrich](https://github.com/jindrichjindrich) and used at [CZ-OPENSCREEN](https://openscreen.cz/en) since then. The current update was motivated by the introduction of new tube design by Thermo Scientific with round Data Matrix modules which libdmtx has problems reading. During this work we found [Scantelope](https://github.com/dmtaub/scantelope) which has similar goals to RackScanner and inspired one of its algorithms. It does not, however, solve the redesigned barcode tubes problem.

RackScanner was tested on Linux and Windows.

We would be gratefull for feedback on performance of RackScanner with different scanners and plate/tube types.

RackScanner is released under the [MIT license](https://opensource.org/licenses/MIT).

## Installation instructions:
- install miniconda from Continuum Analytics (32 bit in case you want to use the AVA6 TWAIN driver)
- in the terminal or Anaconda prompt (Windows):
```
git clone https://github.com/michalkahle/RackScanner.git
cd RackScanner/install
conda env create --file conda_env.yaml
conda activate rackscanner3
```
- on Linux install libdmtx and pylibdmtx:
```
sudo apt install libdmtx0a
pip install pylibdmtx
```
- on Windows install binary packages by pip:
```
pip install pydmtx-0.7.4b1-cp27-none-win32.whl
pip install twain-1.0.4-cp27-cp27m-win32.whl
vcredist_x86.exe
```
- cd to parent directory and run http server:
```
cd ..
python http_server.py
```
- open browser at http://localhost:8000/ and test the functionality in demo mode
- create `settings.py` by copying `settings_template.py`
- in `settings.py` change the mode of operation to one of 'scanner' or 'read_last'

## Instalation of AVA6 driver in Windows:
- restart the system with driver signature enforcement turned off!
- run the original installer from the CD and install TWAIN and W?? driver (might not be necessary)
- from Device Manager start the driver update process
- select driver manually -> have a disk
- select the installer directory Avision Scanner\Driver\TWAIN
- you should get warning about insalling unsigned drivers. Proceed.
- unplug, plug the USB cable. The scanner should work now.
- only 32 bit TWAIN is supported by the driver!

source of binaries:
- twain‑1.0.4‑cp27‑cp27m‑win32.whl: http://www.lfd.uci.edu/~gohlke/pythonlibs/#twainmodule
- pydmtx-0.7.4b1-cp27-none-win32.whl: https://github.com/NaturalHistoryMuseum/dmtx-wrappers
