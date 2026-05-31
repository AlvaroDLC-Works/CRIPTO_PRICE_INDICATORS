@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CriptoPriceStart.ps1" %*
if errorlevel 1 (
    echo.
    echo CriptoPrice finalizo con errores.
    pause
)
