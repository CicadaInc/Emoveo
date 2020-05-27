@echo off
set /p onefile="One file? [y/n]"
echo building...
if "%onefile%" == "y" (
    pyinstaller run_desktop_onefile.spec
) else (
    pyinstaller run_desktop.spec
)
echo complete
pause