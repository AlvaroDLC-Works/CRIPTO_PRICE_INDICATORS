# CriptoPrice

Proyecto para descargar datos históricos de criptoactivos y generar CSVs para análisis. Usa `ccxt` para obtener velas de intercambio público.

## Instalación

1. Crear el entorno virtual (opcional):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Ejecutar el instalador:

```powershell
python install.py
```

3. Ajustar `.env` si es necesario.

## Uso

```powershell
python fetch_crypto_data.py
```

Esto descarga datos OHLCV para los símbolos configurados y genera CSVs.

El código usa `enableRateLimit=True` en `ccxt` y reintentos con backoff para evitar exceder los límites del exchange. Descarga en batches grandes y evita muchas llamadas pequeñas.

## Pushear a GitHub con SSH

Configura `GITHUB_REMOTE` en el archivo `.env` con tu URL SSH:

```text
GITHUB_REMOTE=git@github.com:usuario/CriptoPrice.git
```

Para datos históricos desde 2015 en intervalos diarios, ajusta también:

```text
TIMEFRAME=1d
SINCE=2015-01-01
```

Luego ejecuta:

```powershell
python github_push.py
```

El script inicializa el repositorio si es necesario, crea un commit y hace `git push`.
