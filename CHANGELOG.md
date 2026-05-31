# Changelog

## v0.1.0 - Primera version publica

- Descarga de datos OHLCV desde exchanges via `ccxt`.
- Configuracion editable desde menu usando `config/.env`.
- Fallback de exchanges si falla el principal.
- Nombres cortos para archivos CSV en `data/raw` y `data/analysis`.
- Log de archivos generados en `data/csv_files_log.txt`.
- Sistemas de senales con uno o varios indicadores.
- Indicadores iniciales: EMA, SMA, RSI, MACD, Bollinger Bands, ATR y ROC.
- Exportacion de resultados de analisis a CSV.
- Menu de graficos con salida HTML, PDF horizontal y DXF.
- Limpieza con backup zip para datos y graficos.
- Lanzadores Windows: `CriptoPriceStart.bat` autonomo y `CriptoPriceStart.ps1`.
