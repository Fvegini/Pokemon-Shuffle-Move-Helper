@echo off
echo Removing build and dist folders...
rd /s /q dist
rd /s /q build

echo Executing pyinstaller...
pyinstaller main.spec

echo Copying assets folder to dist...
xcopy /E /I assets dist\main\assets

echo Extracting Version Number
for /f %%v in ('python -c "from app.src.version import current_version; print(current_version)"') do set version=%%v

echo Zipping contents of dist\main...
cd dist
powershell Compress-Archive -Path .\main\* -DestinationPath ..\%version%.zip
cd ..

echo Done.
pause
