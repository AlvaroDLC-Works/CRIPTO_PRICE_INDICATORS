$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

function Get-PythonCommand {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @('py', '-3')
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @('python')
    }

    return $null
}

function Install-Python {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'Python no esta instalado y winget no esta disponible. Instala Python 3 desde https://www.python.org/downloads/windows/ y vuelve a ejecutar CriptoPriceStart.ps1.'
    }

    Write-Host 'Python no esta instalado. Instalando Python 3 con winget...'
    winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements

    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Invoke-PythonScript {
    param(
        [string[]] $PythonCommand,
        [string] $ScriptPath
    )

    $executable = $PythonCommand[0]
    $arguments = @()
    if ($PythonCommand.Count -gt 1) {
        $arguments += $PythonCommand[1..($PythonCommand.Count - 1)]
    }
    $arguments += $ScriptPath

    & $executable @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "El script fallo: $ScriptPath"
    }
}

function Ensure-VirtualEnvironment {
    param(
        [string[]] $PythonCommand
    )

    if (Test-Path $VenvPython) {
        return @($VenvPython)
    }

    Write-Host 'Creando entorno virtual en .venv...'
    $executable = $PythonCommand[0]
    $arguments = @()
    if ($PythonCommand.Count -gt 1) {
        $arguments += $PythonCommand[1..($PythonCommand.Count - 1)]
    }
    $arguments += @('-m', 'venv', '.venv')

    & $executable @arguments
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo crear el entorno virtual .venv.'
    }

    return @($VenvPython)
}

$pythonCommand = Get-PythonCommand
if (-not $pythonCommand) {
    Install-Python
    $pythonCommand = Get-PythonCommand
}

if (-not $pythonCommand) {
    throw 'No se pudo encontrar Python despues de la instalacion.'
}

$pythonCommand = Ensure-VirtualEnvironment -PythonCommand $pythonCommand

Write-Host 'Verificando entorno del proyecto...'
Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath 'scripts/install.py'

Write-Host 'Abriendo CriptoPrice...'
Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath 'main.py'
