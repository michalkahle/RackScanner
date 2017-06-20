set port=%1
set parport=%1

set browser=
::set browser=iexplore 

if "%port%" == "" set port=8080

if "%parport%" == "" goto py
:: start the clinent just by starting a browser at the given port
start "PlateScan Client" /MIN %browser% "http://localhost:%port%/wwwcgi.py?action=call&module=platescan&function=main"
goto end

:py
:: Start the client using the python platescan_start script 
:: This is the prefered way because it shows eventual error messages (if the server
:: start is running)
python platescan_start.py client

:end
