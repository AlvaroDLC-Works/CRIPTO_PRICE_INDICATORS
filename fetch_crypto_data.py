import ccxt
import pandas as pd
import os
from pathlib import Path


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
        'timeframe': os.getenv('TIMEFRAME', '15m').strip(),
        'limit': int(os.getenv('LIMIT', '1000')),
    }


def fetch_ohlcv_to_csv(symbol: str, exchange_name: str, timeframe: str = '15m', limit: int = 500, filename: str = None):
    """Fetch OHLCV data for a symbol from a public exchange and save it to CSV."""
    exchange_cls = getattr(ccxt, exchange_name, None)
    if exchange_cls is None:
        raise ValueError(f'Exchange no soportado: {exchange_name}')

    exchange = exchange_cls({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    print(f"Conectando a {exchange_name} para {symbol} en timeframe {timeframe}...")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

    if filename is None:
        safe_symbol = symbol.replace('/', '_')
        filename = f"{exchange_name}_{safe_symbol}_{timeframe}.csv"

    df.to_csv(filename, index=False)
    print(f"Guardado: {filename} ({len(df)} filas)")
    return filename


if __name__ == '__main__':
    config = load_config()
    for symbol in config['symbols']:
        fetch_ohlcv_to_csv(symbol, config['exchange'], timeframe=config['timeframe'], limit=config['limit'])
