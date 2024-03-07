@echo off
echo Removing build and dist folders...
rd /s /q dist
rd /s /q build

echo Executing pyinstaller...
pyinstaller app\main.py

echo Copying assets folder to dist...
xcopy /E /I assets dist\main\assets

echo Zipping contents of dist\main...
cd dist
powershell Compress-Archive -Path .\main\* -DestinationPath ..\output.zip
cd ..

echo Done.
pause
