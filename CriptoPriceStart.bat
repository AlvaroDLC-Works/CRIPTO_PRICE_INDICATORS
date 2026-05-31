@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PYTHON_CMD="
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "RUN_DOWNLOAD=0"
set "RUN_ANALYSIS=0"
set "ALL_ARGS=%*"

echo %ALL_ARGS% | findstr /I /C:"-RunDownload" >nul
if not errorlevel 1 set "RUN_DOWNLOAD=1"

echo %ALL_ARGS% | findstr /I /C:"-Analysis" >nul
if not errorlevel 1 set "RUN_ANALYSIS=1"

call :find_python
if errorlevel 1 goto fail

call :ensure_venv
if errorlevel 1 goto fail

echo Verificando entorno del proyecto...
"%VENV_PY%" "scripts\install.py"
if errorlevel 1 goto fail

"%VENV_PY%" "scripts\update_env_from_launcher.py" %*
if errorlevel 1 goto fail

if "%RUN_DOWNLOAD%"=="1" (
    echo Ejecutando descarga rapida...
    "%VENV_PY%" "scripts\fetch_crypto_data.py"
    if errorlevel 1 goto fail
)

if "%RUN_ANALYSIS%"=="1" (
    echo Ejecutando modulo de analisis...
    "%VENV_PY%" "scripts\analysis.py"
    if errorlevel 1 goto fail
)

echo Abriendo CriptoPrice...
"%VENV_PY%" "main.py"
if errorlevel 1 goto fail

goto end

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

where winget >nul 2>nul
if errorlevel 1 (
    echo Python no esta instalado y winget no esta disponible.
    echo Instala Python 3 desde https://www.python.org/downloads/windows/ y vuelve a ejecutar CriptoPriceStart.bat.
    exit /b 1
)

echo Python no esta instalado. Instalando Python 3 con winget...
winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 exit /b 1

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

echo No se pudo encontrar Python despues de la instalacion.
exit /b 1

:ensure_venv
if exist "%VENV_PY%" exit /b 0

echo Creando entorno virtual en .venv...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 (
    echo No se pudo crear el entorno virtual .venv.
    exit /b 1
)
exit /b 0

:fail
echo.
echo CriptoPrice finalizo con errores.
pause
exit /b 1

:end
endlocal
