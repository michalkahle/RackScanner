set port=%1
set parport=%1

set PYTHONDIR=%2


if "%PYTHONDIR%" == "" set PYTHONDIR=C:\Python25
if "%port%" == "" set port=8080

set PYTHONPATH=%~dp0
cd /d %PYTHONPATH%

::SEE: http://www.wingware.com/doc/howtos/debugging-under-py2exe
set EXTRA_PYTHONPATH=%PYTHONPATH%;%PYTHONDIR%\lib;%PYTHONDIR%\dlls
set WINGDB_EXITONFAILURE=1
set WINGHOME=C:\Program Files\Wing IDE 4.0

python -c"import os; print os.environ.get('EXTRA_PYTHONPATH')"
pause
if not "%parport%" == "80" goto defportend
:: if on command line specified explicitly a port number and it is 80
:: try to stop all servers which can eventually run on that port
net stop Zope_565048793
net stop Apache2.2

:defportend

if "%parport%" == "" goto depl

:: if port specified on a command line run it in developer mode, i.e.
:: debugging, cmd window will not close when server terminated
::start cmd /k "python wwwcgi\wwwcgi.py %port%"
::goto cont

:depl
:: if the server is run by a user, remove all old temporary files upon
:: server startup

del *.tmp
if not exist platescan_start.exe goto pystart
platescan_start.exe
goto cont

:pystart
::start "PlateScan Server" /MIN %PYTHON% %WWWCGIDIR%\wwwcgi.py %port%
echo In WingIDE "Enable Passive Listen" by left down icon
pause
start "PlateScan Server" /MIN %PYTHONDIR%\python.exe platescan_start.py 
::run_server

:cont
::http://localhost:8080/wwwcgi.py?action=call&module=platescan&function=main
::start "PlateScan Client" /MIN iexplore "http://localhost:%port%/wwwcgi.py?action=call&module=platescan&function=main"
