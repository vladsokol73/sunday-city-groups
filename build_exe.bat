@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Сборка приложения через PyInstaller...
python -m PyInstaller --noconfirm --clean --windowed --name SundayCityGroups --icon "assets\amg.ico" --add-data "assets\amg.ico;assets" main.py
if errorlevel 1 (
    echo.
    echo Сборка не удалась. Проверьте, что зависимости установлены:
    echo   pip install -r requirements.txt
    exit /b %errorlevel%
)

echo.
echo [2/2] Готово. Папка со сборкой: dist\SundayCityGroups
