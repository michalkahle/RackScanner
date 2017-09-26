<img align="left" height="56px" src="resources/logo.png?raw=true"/>

# RackScanner

Application for reading racks of Data Matrix barcoded tubes. Tested with Thermo Scientific Matrix tubes and racks. Can read 96-well racks, 24-well racks, and single tubes.

<img align="left" height="100px" src="resources/vial_1ml_sample.bmp"/>
<img align="left" height="500px" src="resources/rack_96_sample.bmp"/>
<img height="500px" src="resources/rack_24_sample.bmp"/>

RackScanner can currently control just one type of scanner - Avision AVA6 flatbed scanner. This scanner has only Windows 32-bit TWAIN driver. It should not be too hard to make it work with other scanners but in order to work the scanner needs to be able to focus on the plane of the tubes bottoms which is approximately 2mm above the scanner surface. Small scanner format is also a benefit - A6 in the case of AVA6.

RackScanner first localizes the wells of the rack by pattern matching and recognizes the type of the rack. It then determines which wells are empty and which contain barcoded tubes. Attempts to locate and digitize barcodes are then made by three different algorithms using the excellent and fast [OpenCV](http://opencv.org) library. Decoding is done by [libdmtx](http://libdmtx.sourceforge.net) which also serves as fallback in case that previous attempts to locate the code fail.

Original RackScanner was developed in 2011 by [jindrichjindrich](https://github.com/jindrichjindrich) and used at [CZ-OPENSCREEN](https://openscreen.cz/en) since then. The current update was motivated by the introduction of new tube design by Thermo Scientific with round Data Matrix modules which libdmtx has problems reading. During this work we found [Scantelope](https://github.com/dmtaub/scantelope) which has similar goals to RackScanner and inspired some of its algorithms. It does not, however, solve the redesigned barcode tubes problem.

RackScanner was tested on Linux and Windows. Step by step installation instructions for Windows are located in the [install.txt](install/install.txt) file.

RackScanner is released under the [MIT license](https://opensource.org/licenses/MIT).
