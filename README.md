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

## Ejecucion rapida con parametros

`CriptoPriceStart.ps1` puede recibir parametros para actualizar `config/.env` antes de abrir el menu. Si un parametro no se entrega, se conserva el valor actual de `config/.env`.

Ejemplos:

```powershell
.\CriptoPriceStart.ps1 -Symbols BTC,ETH -Timeframe 1d
```

```powershell
.\CriptoPriceStart.ps1 -Exchange binance -FallbackExchanges bybit,okx,kucoin -Symbols BTC -Timeframe 1w -Limit 1000 -Since 2026-03-01
```

Para preparar el ambiente, actualizar parametros y ejecutar la descarga inmediatamente:

```powershell
.\CriptoPriceStart.ps1 -Symbols BTC,ETH -Timeframe 1d -RunDownload
```

Para solicitar analisis despues de preparar el ambiente:

```powershell
.\CriptoPriceStart.ps1 -Symbols BTC -Timeframe 1w -Analysis
```

El parametro `-Analysis` abre el modulo de analisis para cargar archivos base, crear sistemas de senales y aplicarlos sobre CSV ya descargados.

Parametros disponibles:

- `-Exchange`: exchange principal, por ejemplo `binance`.
- `-FallbackExchanges`: exchanges alternativos separados por coma.
- `-Symbols`: activos base separados por coma, por ejemplo `BTC,ETH`.
- `-Timeframe`: periodo, por ejemplo `1d` o `1w`.
- `-Limit`: cantidad de velas por batch.
- `-Since`: fecha inicial, por ejemplo `2026-03-01`.
- `-RunDownload`: ejecuta la descarga directamente despues de preparar el ambiente.
- `-Analysis`: ejecuta el modulo de analisis.

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
- Limpiar CSV de `data/raw/`, `data/analysis/` o ambos, creando antes un `.zip` en `backup/`.

La herramienta de limpieza conserva la estructura dentro del `.zip`, por ejemplo `data/raw/...csv` y `data/analysis/...csv`. Los nombres de backup son cortos:

```text
raw260531121500.zip
analysis260531121500.zip
todos260531121500.zip
```

El menu principal muestra primero un dashboard con la configuracion de descarga y el ultimo archivo base disponible en `data/raw/`. Debajo aparecen las opciones:

```text
1) Configurar Descarga (config/.env)
2) Descargar Datos (fetch_crypto_data)
3) Analisis de Datos
4) Herramientas
5) Salir
```

## Uso

Descargar datos:

```powershell
py scripts/fetch_crypto_data.py
```

Esto descarga datos OHLCV para los simbolos configurados y genera un CSV por simbolo en `data/raw/`.
Ese archivo es la base limpia para analisis, por ejemplo:

```text
binanceBTC1w260301260531004807.csv
```

Los simbolos se configuran como monedas base. La moneda de intercambio se asume siempre como `USDT`.
Si el exchange principal falla, el script intenta los exchanges definidos en `FALLBACK_EXCHANGES` en orden.

## Analisis

La opcion `Analisis` del menu principal abre un submenu:

```text
1) Cargar Archivos Base
2) Crear Sistema de senales
3) Aplicar Sistema de senales
4) Eliminar Sistema de senales
5) Volver al menu principal
```

- `Cargar Archivos Base`: permite seleccionar un CSV desde `data/raw/`. Si no eliges uno, se usa por defecto el ultimo archivo generado.
- `Crear Sistema de senales`: lista indicadores desde `config/indicators.json` y registra uno o varios indicadores dentro de un sistema en `config/signal_systems.json`.
- `Aplicar Sistema de senales`: permite elegir un sistema creado y genera un nuevo CSV en `data/analysis/`.
- `Eliminar Sistema de senales`: permite borrar un sistema guardado.

El CSV de analisis conserva los datos base y agrega columnas de resultado, por ejemplo:

- `signal_system_name`: nombre del sistema de senales aplicado.
- `ema_40`: media movil exponencial de 40 periodos calculada sobre `close`.

Cuando el sistema contiene mas de un indicador, el CSV agrega una columna por cada resultado calculado, por ejemplo `ema_40`, `rsi_14` o las columnas de `macd`.

Los indicadores iniciales disponibles son:

- `ema(source, length)`: media movil exponencial.
- `sma(source, length)`: media movil simple.
- `rsi(source, length)`: indice de fuerza relativa.
- `macd(source, fast_length, slow_length, signal_length)`: momentum por cruce de medias.
- `bbands(source, length, std_multiplier)`: bandas de Bollinger.
- `atr(length)`: volatilidad por rango verdadero promedio.
- `roc(source, length)`: tasa de cambio.

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
- `config/indicators.json`: catalogo de indicadores disponibles para crear sistemas de senales.
- `config/signal_systems.json`: sistemas de senales creados para el modulo de analisis.
- `data/raw/`: archivos CSV generados por las descargas.
- `data/analysis/`: archivos CSV generados por sistemas de senales.
- `backup/`: archivos comprimidos generados por la limpieza de CSV.
- `docs/`: documentacion extendida.
- `scripts/`: scripts de instalacion, descarga, configuracion y analisis.
- `scripts/Indicacdores.py`: funciones Python para calcular indicadores tecnicos.
- `CriptoPriceStart.ps1`: instalador y lanzador principal para Windows.
