<img align="left" height="56px" src="resources/logo.png?raw=true"/>

# RackScanner

Application for reading racks of Data Matrix barcoded tubes. Tested with Thermo Scientific Matrix tubes and racks. Can read 96-well racks, 24-well racks, and single tubes.

<img align="left" height="100px" src="resources/vial_1ml_sample.bmp"/>
<img align="left" height="500px" src="resources/rack_96_sample.bmp"/>
<img height="500px" src="resources/rack_24_sample.bmp"/>

RackScanner can currently control just one type of scanner - Avision AVA6 flatbed scanner. This scanner has only Windows 32-bit TWAIN driver. It should not be too hard to make it work with other scanners but in order to work the scanner needs to be able to focus on the plane of the tubes bottoms which is approximately 2mm above the scanner surface. Small scanner format is also a benefit - A6 in the case of AVA6.

RackScanner first localizes the wells of the rack by pattern matching and recognizes the type of the rack. It then determines which wells are empty and which contain barcoded tubes. Attempts to locate and digitize barcodes are then made by three different algorithms using the excellent and fast [OpenCV](http://opencv.org) library. Decoding is done by [libdmtx](http://libdmtx.sourceforge.net) which also serves as fallback in case that previous attempts to locate the code fail.

[scantelope](https://github.com/dmtaub/scantelope) has similar goals to RackScanner

Step by step installation instructions are located in the [install.txt](install/install.txt) file.

License: 
