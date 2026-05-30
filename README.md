# CriptoPrice

Proyecto para descargar datos historicos de criptoactivos y generar archivos CSV para analisis. Usa `ccxt` para obtener velas OHLCV desde exchanges publicos.

## Instalacion y ejecucion

```powershell
.\CriptoPriceStart.ps1
```

El instalador verifica Python. Si no esta instalado, intenta instalar Python 3 con `winget`. Luego crea `.venv`, instala dependencias, crea `config/.env` desde `config/.env.example` si todavia no existe y abre el menu principal.

Si PowerShell bloquea la ejecucion de scripts, usa:

```powershell
powershell -ExecutionPolicy Bypass -File .\CriptoPriceStart.ps1
```

## Configuracion

Edita `config/.env` con los parametros principales:

```env
EXCHANGE=binance
FALLBACK_EXCHANGES=bybit,okx,kucoin
SYMBOLS=BTC,ETH
TIMEFRAME=1d
```

Tambien puedes usar el menu principal para editar la configuracion:

```powershell
.\CriptoPriceStart.ps1
```

El menu `Herramientas` permite ejecutar utilidades de mantenimiento:

- Verificar o reparar el ambiente con `scripts/install.py`.
- Regenerar `config/env_config_fields.json` desde `config/.env.example`.

## Uso

Descargar datos:

```powershell
py scripts/fetch_crypto_data.py
```

Esto descarga datos OHLCV para los simbolos configurados y genera un CSV por simbolo en `data/raw/`.

Los simbolos se configuran como monedas base. La moneda de intercambio se asume siempre como `USDT`.
Si el exchange principal falla, el script intenta los exchanges definidos en `FALLBACK_EXCHANGES` en orden.

## Nombre de archivos CSV

Los archivos generados usan este formato:

```text
binanceBTC1w260301260530221801.csv
```

El nombre no usa espacios, guiones ni barras bajas. Se compone asi:

- `binance`: exchange.
- `BTC`: activo base descargado.
- `1w`: periodo o timeframe.
- `260301260530221801`: codigo de descarga.

El codigo de descarga se lee en bloques:

- Primeras 6 cifras: fecha inicial `YYMMDD`, por ejemplo `260301`.
- Siguientes 6 cifras: fecha de descarga `YYMMDD`, por ejemplo `260530`.
- Ultimas 6 cifras: hora de descarga `HHMMSS`, por ejemplo `221801`.

El codigo usa `enableRateLimit=True` en `ccxt` y reintentos con backoff para evitar exceder los limites del exchange.

## Estructura

- `config/`: definicion de campos editables para el menu de configuracion.
- `data/raw/`: archivos CSV generados por las descargas.
- `docs/`: documentacion extendida.
- `scripts/`: scripts de instalacion, descarga y configuracion.
- `CriptoPriceStart.ps1`: instalador y lanzador principal para Windows.
