# Manual de usuario - CriptoPrice

## 1. Objetivo

`CriptoPrice` es una herramienta en Python para descargar datos históricos de criptomonedas (OHLCV) desde exchanges públicos, exportarlos a archivos CSV y facilitar análisis e inversiones.

## 2. Requisitos

- Python 3.8 o superior
- Conexión a internet
- Permiso para acceder a proxies/exchanges públicos
- Opcional: clave SSH configurada para GitHub si vas a usar `github_push.py`

## 3. Archivos principales

- `install.py`: prepara el entorno, crea `.env` si no existe y asegura dependencias.
- `fetch_crypto_data.py`: descarga datos históricos de OHLCV y los exporta a CSV.
- `github_push.py`: inicializa el repositorio git si es necesario, hace commit y push al remoto SSH.
- `requirements.txt`: lista de dependencias Python.
- `.env.example`: plantilla de configuración.
- `README.md`: resumen de uso y comandos básicos.
- `USER_MANUAL.md`: este manual.

## 4. Configuración inicial

1. Abre PowerShell en el directorio del proyecto:

```powershell
cd c:\Users\Gamer\Projects\Investing\CriptoPrice
```

2. Crea un entorno virtual (opcional pero recomendado):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Ejecuta el instalador:

```powershell
py install.py
```

4. Revisa el archivo `.env` generado y ajusta las variables si es necesario.

## 5. Configuración de `.env`

El archivo `.env` controla el comportamiento del script.

Ejemplo:

```text
GITHUB_REMOTE=git@github.com:username/CriptoPrice.git
EXCHANGE=binance
SYMBOLS=BTC/USDT,ETH/USDT
TIMEFRAME=1d
LIMIT=1000
SINCE=2015-01-01
```

Explicación de cada variable:

- `GITHUB_REMOTE`: URL SSH de tu repositorio GitHub.
- `EXCHANGE`: nombre del exchange compatible con `ccxt` (`binance`, `kraken`, etc.).
- `SYMBOLS`: lista de pares separados por comas.
- `TIMEFRAME`: intervalo de velas (`1d`, `15m`, `1h`, etc.).
- `LIMIT`: máximo de velas por llamada en cada batch.
- `SINCE`: fecha inicial de descarga en formato `YYYY-MM-DD`.

## 6. Ejecución del script

Para descargar datos configurados en `.env`:

```powershell
py fetch_crypto_data.py
```

Esto generará un CSV por cada símbolo en el proyecto.

### Ejecución solo para un par específico

Si quieres probar solo `BTC/USDT` sin cambiar `.env`:

```powershell
$env:SYMBOLS='BTC/USDT'
py fetch_crypto_data.py
```

## 7. Resultado esperado

Los CSV se generan con las columnas:

- `symbol`
- `datetime`
- `open`
- `high`
- `low`
- `close`
- `volume`

El nombre del archivo encaja con el exchange, el símbolo y el intervalo, por ejemplo:

- `binance_BTC_USDT_1d_20150101.csv`

## 8. Límites y buenas prácticas

- `ccxt` usa la librería para conectarse al exchange, pero los límites son los que impone el exchange.
- En Binance hay límite de requests por minuto y por segundo.
- Usa `enableRateLimit=True` para que `ccxt` gestione pausas automáticamente.
- Descarga datos en rangos grandes en lugar de muchas consultas pequeñas.
- Si recibes errores `429` o timeouts, reduce la frecuencia de peticiones.

## 9. Publicar en GitHub

1. Verifica que `GITHUB_REMOTE` está configurado en `.env`.
2. Asegúrate de tener acceso SSH a GitHub.
3. Ejecuta:

```powershell
py github_push.py
```

El script hará commit de los cambios y realizará el push al remoto.

## 10. Verificación y pruebas

- Confirma que existen los archivos CSV generados.
- Abre un CSV con Excel, pandas o cualquier editor de texto.
- Verifica que el primer registro corresponde a la fecha histórica esperada.
- Verifica que el último registro corresponde a la fecha actual o más reciente disponible.

## 11. Problemas comunes

- `python` no reconocido en Windows: usa `py`.
- `429 Too Many Requests`: espera y reduce la tasa de llamadas.
- `No se obtuvo datos`: revisa el símbolo y el exchange.
- `Repository not initialized` en `github_push.py`: el script inicializa git automáticamente.

## 12. Extensiones futuras

- Añadir más indicadores técnicos (RSI, EMA, SMA).
- Exportar un solo CSV con varios símbolos concatenados.
- Agregar soporte de múltiples exchanges configurables en `.env`.
- Agregar logging y métricas de descarga.
