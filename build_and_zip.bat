@echo off
echo Installing required packages...
py -m pip install -r requirements.txt

echo Building the EXE...
py build_exe.py

echo Creating ZIP...
powershell -NoProfile -Command "Compress-Archive -Path dist\* -DestinationPath karaoke_manager_windows.zip -Force"

echo Done.
echo ZIP created at:
echo %CD%\karaoke_manager_windows.zip
pause
