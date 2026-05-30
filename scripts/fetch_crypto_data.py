import ccxt
import pandas as pd
import os
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
DEFAULT_FALLBACK_EXCHANGES = ['bybit', 'okx', 'kucoin']


def parse_since(value: str | None) -> int | None:
    if not value:
        return None

    value = value.strip()
    if value.isdigit():
        ts = int(value)
        return ts if ts > 1_000_000_000_000 else ts * 1000

    dt = pd.to_datetime(value, utc=True)
    return int(dt.timestamp() * 1000)


def normalize_symbol(value: str, quote_currency: str = 'USDT') -> str:
    base_symbol = value.strip().upper()
    if '/' in base_symbol:
        base_symbol = base_symbol.split('/', 1)[0].strip()
    return f'{base_symbol}/{quote_currency}'


def parse_symbols(value: str | None) -> list[str]:
    raw_symbols = value or 'BTC,ETH'
    return [normalize_symbol(symbol) for symbol in raw_symbols.split(',') if symbol.strip()]


def parse_exchange_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [exchange.strip().lower() for exchange in value.split(',') if exchange.strip()]


def build_exchange_sequence(primary_exchange: str, fallback_exchanges: list[str]) -> list[str]:
    exchange_sequence = []
    for exchange in [primary_exchange, *fallback_exchanges]:
        normalized_exchange = exchange.strip().lower()
        if normalized_exchange and normalized_exchange not in exchange_sequence:
            exchange_sequence.append(normalized_exchange)
    return exchange_sequence


def load_config() -> dict:
    env_path = PROJECT_ROOT / 'config' / '.env'
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path)
            print('Cargando configuracion de config/.env')
        except ImportError:
            print('Aviso: python-dotenv no está instalado. Se usan variables de entorno del sistema.')

    exchange = os.getenv('EXCHANGE', 'binance').strip().lower()
    fallback_exchanges = parse_exchange_list(os.getenv('FALLBACK_EXCHANGES'))
    if not fallback_exchanges:
        fallback_exchanges = DEFAULT_FALLBACK_EXCHANGES

    return {
        'exchange': exchange,
        'fallback_exchanges': fallback_exchanges,
        'exchange_sequence': build_exchange_sequence(exchange, fallback_exchanges),
        'symbols': parse_symbols(os.getenv('SYMBOLS')),
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


def build_csv_filename(symbol: str, exchange_name: str, timeframe: str, since_ms: int | None = None) -> Path:
    base_symbol = symbol.split('/', 1)[0].strip().upper()
    exchange_code = exchange_name.strip().lower()
    since_code = '' if since_ms is None else f'{datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc):%y%m%d}'
    download_code = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')
    return DATA_DIR / f'{exchange_code}{base_symbol}{timeframe}{since_code}{download_code}.csv'


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
        filename = build_csv_filename(symbol, exchange_name, timeframe, since_ms)

    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"Guardado: {filename} ({len(df)} filas)")
    return str(filename)


def fetch_ohlcv_to_csv_with_fallback(
    symbol: str,
    exchange_names: list[str],
    timeframe: str = '1d',
    limit: int = 500,
    since_ms: int | None = None,
) -> str:
    last_error = None

    for exchange_name in exchange_names:
        try:
            return fetch_ohlcv_to_csv(
                symbol,
                exchange_name,
                timeframe=timeframe,
                limit=limit,
                since_ms=since_ms,
            )
        except Exception as exc:
            last_error = exc
            print(f'  No se pudo descargar {symbol} desde {exchange_name}: {exc}')
            print('  Probando siguiente exchange disponible...')

    raise RuntimeError(f'No se pudo descargar {symbol} desde ningun exchange configurado.') from last_error


if __name__ == '__main__':
    config = load_config()
    for symbol in config['symbols']:
        fetch_ohlcv_to_csv_with_fallback(
            symbol,
            config['exchange_sequence'],
            timeframe=config['timeframe'],
            limit=config['limit'],
            since_ms=config['since'],
        )
