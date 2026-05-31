# Manual de usuario - CriptoPrice

## 1. Objetivo

`CriptoPrice` es una herramienta en Python para descargar datos historicos de criptomonedas (OHLCV) desde exchanges publicos y exportarlos a archivos CSV.

## 2. Requisitos

- Conexion a internet
- Permiso para acceder a exchanges publicos
- Windows con PowerShell

## 3. Archivos principales

- `main.py`: menu principal del proyecto.
- `CriptoPriceStart.ps1`: instalador y lanzador principal para Windows.
- `scripts/install.py`: prepara el entorno, crea `config/.env` si no existe y verifica dependencias.
- `scripts/fetch_crypto_data.py`: descarga datos historicos OHLCV y los exporta a CSV.
- `scripts/env_config_editor.py`: permite editar `config/.env` desde la terminal.
- `scripts/env_config_fields_generator.py`: genera `config/env_config_fields.json` desde `config/.env.example`.
- `scripts/analysis.py`: modulo reservado para analisis futuros.
- `config/env_config_fields.json`: define los campos editables del menu de configuracion.
- `config/.env.example`: plantilla de configuracion.
- `requirements.txt`: lista de dependencias Python.

## 4. Configuracion inicial

Abre PowerShell en el directorio del proyecto:

```powershell
cd c:\Users\Gamer\Projects\Investing\CriptoPrice
```

Ejecuta el instalador:

```powershell
.\CriptoPriceStart.ps1
```

Si Python no esta instalado, el instalador intenta instalar Python 3 con `winget`. Luego crea `.venv`, ejecuta `scripts/install.py` automaticamente y abre `main.py`.

Si PowerShell bloquea la ejecucion de scripts, usa:

```powershell
powershell -ExecutionPolicy Bypass -File .\CriptoPriceStart.ps1
```

## 5. Configuracion de `config/.env`

El archivo `config/.env` controla el comportamiento de descarga.

Ejemplo:

```env
EXCHANGE=binance
FALLBACK_EXCHANGES=bybit,okx,kucoin
SYMBOLS=BTC,ETH
TIMEFRAME=1d
```

Variables:

- `EXCHANGE`: nombre del exchange compatible con `ccxt`, por ejemplo `binance` o `kraken`.
- `FALLBACK_EXCHANGES`: exchanges alternativos separados por comas si falla el principal.
- `SYMBOLS`: lista de monedas base separadas por comas. La moneda de intercambio se asume siempre como `USDT`.
- `TIMEFRAME`: intervalo de velas, por ejemplo `1d`, `15m` o `1h`.

## 6. Menu principal

Ejecuta:

```powershell
.\CriptoPriceStart.ps1
```

Opciones disponibles:

- Descargar datos.
- Editar configuracion `config/.env`.
- Abrir el submenu de analisis.
- Abrir herramientas de mantenimiento.
- Salir.

El submenu `Analisis` permite:

- Cargar un archivo base desde `data/raw/`.
- Crear una estrategia. Actualmente el tipo soportado es `ema40`.
- Aplicar una estrategia y guardar un CSV en `data/analysis/` con columnas como `strategy_name` y `ema_40`.

El menu `Herramientas` permite:

- Verificar o reparar el ambiente con `scripts/install.py`.
- Regenerar `config/env_config_fields.json` desde `config/.env.example`.

## 7. Descargar datos

Para descargar datos configurados en `config/.env`:

```powershell
py scripts/fetch_crypto_data.py
```

Esto genera un CSV por cada simbolo configurado en `data/raw/`.

## 8. Resultado esperado

Los CSV se generan con las columnas:

- `symbol`
- `datetime`
- `open`
- `high`
- `low`
- `close`
- `volume`

Ejemplo de nombre de archivo:

- `bin_BTC_1d_250101_260530_214034.csv`

## 9. Limites y buenas practicas

- `ccxt` respeta los limites del exchange con `enableRateLimit=True`.
- El script incluye reintentos con backoff para manejar errores temporales.
- Si recibes errores `429`, espera antes de volver a ejecutar.
- Evita muchas ejecuciones rapidas seguidas.

## 10. Problemas comunes

- `python` no reconocido en Windows: ejecuta `.\CriptoPriceStart.ps1` para intentar instalar Python automaticamente.
- `429 Too Many Requests`: espera y reduce la frecuencia de llamadas.
- `No se obtuvieron datos`: revisa el simbolo, el exchange y el intervalo.
