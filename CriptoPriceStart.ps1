param(
    [string] $Exchange,
    [string] $FallbackExchanges,
    [string] $Symbols,
    [string] $Timeframe,
    [int] $Limit,
    [string] $Since,
    [switch] $RunDownload,
    [switch] $Analysis
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$EnvPath = Join-Path $ProjectRoot 'config\.env'

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

function Read-EnvFile {
    param(
        [string] $Path
    )

    $values = [ordered]@{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or -not $trimmed.Contains('=')) {
            continue
        }

        $parts = $trimmed.Split('=', 2)
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }

    return $values
}

function Write-EnvFile {
    param(
        [string] $Path,
        [hashtable] $Values
    )

    $content = @(
        '# Exchange publico para datos OHLCV'
        "EXCHANGE=$($Values['EXCHANGE'])"
        ''
        '# Exchanges alternativos si falla el principal'
        "FALLBACK_EXCHANGES=$($Values['FALLBACK_EXCHANGES'])"
        ''
        '# Simbolos base separados por coma. La moneda de intercambio se asume USDT.'
        "SYMBOLS=$($Values['SYMBOLS'])"
        ''
        '# Intervalo de velas'
        "TIMEFRAME=$($Values['TIMEFRAME'])"
        ''
        '# Cantidad de velas a descargar por batch'
        "LIMIT=$($Values['LIMIT'])"
        ''
        '# Fecha de inicio para descargas historicas'
        "SINCE=$($Values['SINCE'])"
    )

    $directory = Split-Path -Parent $Path
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    Set-Content -Path $Path -Value $content -Encoding UTF8
}

function Update-EnvFromParameters {
    $values = Read-EnvFile -Path $EnvPath

    if (-not $values.Contains('EXCHANGE')) { $values['EXCHANGE'] = 'binance' }
    if (-not $values.Contains('FALLBACK_EXCHANGES')) { $values['FALLBACK_EXCHANGES'] = 'bybit,okx,kucoin' }
    if (-not $values.Contains('SYMBOLS')) { $values['SYMBOLS'] = 'BTC,ETH' }
    if (-not $values.Contains('TIMEFRAME')) { $values['TIMEFRAME'] = '1d' }
    if (-not $values.Contains('LIMIT')) { $values['LIMIT'] = '1000' }
    if (-not $values.Contains('SINCE')) { $values['SINCE'] = '2025-01-01' }

    $changed = $false
    if ($Exchange) { $values['EXCHANGE'] = $Exchange; $changed = $true }
    if ($FallbackExchanges) { $values['FALLBACK_EXCHANGES'] = $FallbackExchanges; $changed = $true }
    if ($Symbols) { $values['SYMBOLS'] = $Symbols; $changed = $true }
    if ($Timeframe) { $values['TIMEFRAME'] = $Timeframe; $changed = $true }
    if ($PSBoundParameters.ContainsKey('Limit')) { $values['LIMIT'] = [string]$Limit; $changed = $true }
    if ($Since) { $values['SINCE'] = $Since; $changed = $true }

    if ($changed -or -not (Test-Path $EnvPath)) {
        Write-Host 'Actualizando config/.env con parametros de ejecucion...'
        Write-EnvFile -Path $EnvPath -Values $values
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

Update-EnvFromParameters

if ($RunDownload) {
    Write-Host 'Ejecutando descarga rapida...'
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath 'scripts/fetch_crypto_data.py'
}

if ($Analysis) {
    Write-Host 'Ejecutando modulo de analisis...'
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath 'scripts/analysis.py'
}

Write-Host 'Abriendo CriptoPrice...'
Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath 'main.py'
