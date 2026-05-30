import ccxt
import pandas as pd
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_since(value: str | None) -> int | None:
    if not value:
        return None

    value = value.strip()
    if value.isdigit():
        ts = int(value)
        return ts if ts > 1_000_000_000_000 else ts * 1000

    dt = pd.to_datetime(value, utc=True)
    return int(dt.timestamp() * 1000)


def load_config() -> dict:
    env_path = Path('.env')
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path)
            print('Cargando configuración de .env')
        except ImportError:
            print('Aviso: python-dotenv no está instalado. Se usan variables de entorno del sistema.')

    return {
        'exchange': os.getenv('EXCHANGE', 'binance').strip().lower(),
        'symbols': [symbol.strip() for symbol in os.getenv('SYMBOLS', 'BTC/USDT,ETH/USDT').split(',') if symbol.strip()],
        'timeframe': os.getenv('TIMEFRAME', '1d').strip(),
        'limit': int(os.getenv('LIMIT', '1000')),
        'since': parse_since(os.getenv('SINCE')),
    }


def safe_fetch_ohlcv(exchange, symbol: str, timeframe: str, since: int | None = None, limit: int = 1000, max_retries: int = 5):
    wait_seconds = 1
    for attempt in range(1, max_retries + 1):
        try:
            if since is not None:
                return exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
            return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except ccxt.BaseError as exc:
            if attempt == max_retries:
                raise
            print(f'  Error de conexión o límite detectado: {exc}. Reintentando en {wait_seconds}s... (intento {attempt}/{max_retries})')
            time.sleep(wait_seconds)
            wait_seconds = min(wait_seconds * 2, 30)
    raise RuntimeError('No se pudo obtener datos tras varios reintentos.')


def fetch_ohlcv_all(exchange, symbol: str, timeframe: str, since_ms: int, limit: int = 1000):
    timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
    all_ohlcv = []
    now = exchange.milliseconds()
    current_since = since_ms

    while current_since < now:
        start_dt = datetime.fromtimestamp(current_since / 1000, tz=timezone.utc)
        print(f'  Descargando batch desde {start_dt:%Y-%m-%dT%H:%M:%SZ}')
        batch = safe_fetch_ohlcv(exchange, symbol, timeframe, since=current_since, limit=limit)
        if not batch:
            break

        if all_ohlcv and batch[0][0] <= all_ohlcv[-1][0]:
            break

        all_ohlcv.extend(batch)
        last_ts = batch[-1][0]
        if last_ts == current_since:
            break

        current_since = last_ts + timeframe_ms
        if len(batch) < limit:
            break

        time.sleep(exchange.rateLimit / 1000)

    return all_ohlcv


def fetch_ohlcv_to_csv(symbol: str, exchange_name: str, timeframe: str = '1d', limit: int = 500, since_ms: int | None = None, filename: str = None):
    """Fetch OHLCV data for a symbol from a public exchange and save it to CSV."""
    exchange_cls = getattr(ccxt, exchange_name, None)
    if exchange_cls is None:
        raise ValueError(f'Exchange no soportado: {exchange_name}')

    exchange = exchange_cls({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    print(f"Conectando a {exchange_name} para {symbol} en timeframe {timeframe}...")
    if since_ms is not None:
        ohlcv = fetch_ohlcv_all(exchange, symbol, timeframe, since_ms, limit=limit)
    else:
        ohlcv = safe_fetch_ohlcv(exchange, symbol, timeframe, limit=limit)

    if not ohlcv:
        raise ValueError(f'No se obtuvieron datos para {symbol} en {exchange_name}.')

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['symbol'] = symbol
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']]

    if filename is None:
        safe_symbol = symbol.replace('/', '_')
        since_suffix = '' if since_ms is None else f'_{datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc):%Y%m%d}'
        filename = f"{exchange_name}_{safe_symbol}_{timeframe}{since_suffix}.csv"

    df.to_csv(filename, index=False)
    print(f"Guardado: {filename} ({len(df)} filas)")
    return filename


if __name__ == '__main__':
    config = load_config()
    for symbol in config['symbols']:
        fetch_ohlcv_to_csv(
            symbol,
            config['exchange'],
            timeframe=config['timeframe'],
            limit=config['limit'],
            since_ms=config['since'],
        )
