@echo off
setlocal
cd /d "%~dp0"

call build_exe.bat
if errorlevel 1 exit /b %errorlevel%

set "ISCC_PATH="
for %%I in (ISCC.exe) do set "ISCC_PATH=%%~$PATH:I"

if not defined ISCC_PATH if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC_PATH (
    echo.
    echo Не найден Inno Setup Compiler ^(ISCC.exe^).
    echo Установите Inno Setup 6, затем снова запустите этот файл.
    echo Сайт: https://jrsoftware.org/isinfo.php
    exit /b 1
)

echo.
echo Сборка установщика через Inno Setup...
"%ISCC_PATH%" "installer.iss"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Готово. Установщик лежит в папке: installer-output
