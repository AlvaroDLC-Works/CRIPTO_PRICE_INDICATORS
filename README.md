# CriptoPrice

Proyecto para descargar datos historicos de criptoactivos y generar archivos CSV para analisis. Usa `ccxt` para obtener velas OHLCV desde exchanges publicos.

## Instalacion y ejecucion

```powershell
.\CriptoPriceStart.ps1
```

El instalador verifica Python. Si no esta instalado, intenta instalar Python 3 con `winget`. Luego crea `.venv`, instala dependencias, crea `config/.env` desde `config/.env.example` si todavia no existe y abre el menu principal.
Tambien puedes usar `CriptoPriceStart.bat` desde CMD o con doble clic en el explorador de Windows; internamente ejecuta el `.ps1` con la politica de ejecucion adecuada.

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
- Regenerar `config/env_config_fields.json` desde `config/.env`.
- Limpiar CSV de `data/raw/`, CSV de `data/analysis/` y graficos de `data/charts/`, creando antes un `.zip` en `backup/`.
- Acortar nombres de CSV existentes en `data/raw/` y `data/analysis/`.

La herramienta de limpieza conserva la estructura dentro del `.zip`, por ejemplo `data/raw/...csv`, `data/analysis/...csv` y `data/charts/...dxf`. Los nombres de backup son cortos:

```text
raw260531121500.zip
analysis260531121500.zip
charts260531121500.zip
todos260531121500.zip
```

El menu principal muestra primero un dashboard con la configuracion de descarga y el ultimo archivo base disponible en `data/raw/`. Debajo aparecen las opciones:

```text
1) Configurar Descarga (config/.env)
2) Descargar Datos (fetch_crypto_data)
3) Analisis de Datos
4) Graficos
5) Herramientas
6) Salir
```

## Uso

Descargar datos:

```powershell
py scripts/fetch_crypto_data.py
```

Esto descarga datos OHLCV para los simbolos configurados y genera un CSV por simbolo en `data/raw/`.
Ese archivo es la base limpia para analisis, por ejemplo:

```text
raw26053113255201.csv
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

## Graficos

La opcion `Graficos` del menu principal permite trabajar con CSV de `data/raw/` o `data/analysis/`:

```text
1) Ver en pantalla
2) Exportar grafico en PDF horizontal
3) Exportar grafico en CAD/DXF
4) Volver al menu principal
```

- `Ver en pantalla`: genera un HTML con velas OHLC estilo TradingView y superpone columnas calculadas como `ema_40`.
- `Exportar grafico en PDF horizontal`: crea un PDF en formato horizontal con velas OHLC y columnas calculadas.
- `Exportar grafico en CAD/DXF`: exporta columnas numericas a DXF usando un layer por columna.

En pantalla, PDF y DXF puedes elegir entre linea/polilinea o solo puntos. En modo puntos se usa una `X`; en modo linea, cada columna calculada usa un color aleatorio y une sus valores siguiendo el eje X.

## Nombre de archivos CSV

Los archivos generados usan este formato:

```text
raw26053113255201.csv
ana26053113261001.csv
```

El nombre no usa espacios, guiones ni barras bajas. Es un ID corto con referencia a la fecha de generacion:

- `raw`: archivo base descargado en `data/raw/`.
- `ana`: archivo generado por analisis en `data/analysis/`.
- `260531132552`: fecha y hora UTC `YYMMDDHHMMSS`.
- `01`: correlativo para evitar colisiones si se crean varios archivos en el mismo segundo.

Cada CSV generado queda documentado en:

```text
data/csv_files_log.txt
```

El log registra el ID corto, ruta del archivo, descripcion y el estado del dashboard al momento de la descarga o del analisis.

El codigo usa `enableRateLimit=True` en `ccxt` y reintentos con backoff para evitar exceder los limites del exchange.

## Estructura

- `config/`: definicion de campos editables para el menu de configuracion.
- `config/indicators.json`: catalogo de indicadores disponibles para crear sistemas de senales.
- `config/signal_systems.json`: sistemas de senales creados para el modulo de analisis.
- `data/raw/`: archivos CSV generados por las descargas.
- `data/analysis/`: archivos CSV generados por sistemas de senales.
- `data/charts/`: archivos HTML, PDF y DXF generados desde el menu de graficos.
- `data/csv_files_log.txt`: bitacora de IDs cortos y descripcion de CSV generados.
- `backup/`: archivos comprimidos generados por la limpieza de CSV.
- `docs/`: documentacion extendida.
- `scripts/`: scripts de instalacion, descarga, configuracion y analisis.
- `scripts/Indicacdores.py`: funciones Python para calcular indicadores tecnicos.
- `CriptoPriceStart.ps1`: instalador y lanzador principal para Windows.
- `CriptoPriceStart.bat`: lanzador para CMD o doble clic en Windows.
