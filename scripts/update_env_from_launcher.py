import argparse
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / 'config' / '.env'

DEFAULT_VALUES = {
    'EXCHANGE': 'binance',
    'FALLBACK_EXCHANGES': 'bybit,okx,kucoin',
    'SYMBOLS': 'BTC,ETH',
    'TIMEFRAME': '1d',
    'LIMIT': '1000',
    'SINCE': '2025-01-01',
}

ENVIRONMENT_MAP = {
    'EXCHANGE': 'CRIPTOPRICE_EXCHANGE',
    'FALLBACK_EXCHANGES': 'CRIPTOPRICE_FALLBACK_EXCHANGES',
    'SYMBOLS': 'CRIPTOPRICE_SYMBOLS',
    'TIMEFRAME': 'CRIPTOPRICE_TIMEFRAME',
    'LIMIT': 'CRIPTOPRICE_LIMIT',
    'SINCE': 'CRIPTOPRICE_SINCE',
}

COMMENTS = {
    'EXCHANGE': 'Exchange publico para datos OHLCV',
    'FALLBACK_EXCHANGES': 'Exchanges alternativos si falla el principal',
    'SYMBOLS': 'Simbolos base separados por coma. La moneda de intercambio se asume USDT.',
    'TIMEFRAME': 'Intervalo de velas',
    'LIMIT': 'Cantidad de velas a descargar por batch',
    'SINCE': 'Fecha de inicio para descargas historicas',
}


def read_env_values() -> dict[str, str]:
    values = DEFAULT_VALUES.copy()
    if not ENV_PATH.exists():
        return values

    for line in ENV_PATH.read_text(encoding='utf-8-sig').splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        values[key.strip()] = value.strip()
    return values


def write_env_values(values: dict[str, str]) -> None:
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in DEFAULT_VALUES:
        if lines:
            lines.append('')
        lines.append(f'# {COMMENTS[key]}')
        lines.append(f'{key}={values[key]}')
    ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Actualiza config/.env desde parametros del lanzador.')
    parser.add_argument('-Exchange')
    parser.add_argument('-FallbackExchanges')
    parser.add_argument('-Symbols')
    parser.add_argument('-Timeframe')
    parser.add_argument('-Limit')
    parser.add_argument('-Since')
    parser.add_argument('-RunDownload', action='store_true')
    parser.add_argument('-Analysis', action='store_true')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    values = read_env_values()
    changed = False

    argument_values = {
        'EXCHANGE': args.Exchange,
        'FALLBACK_EXCHANGES': args.FallbackExchanges,
        'SYMBOLS': args.Symbols,
        'TIMEFRAME': args.Timeframe,
        'LIMIT': args.Limit,
        'SINCE': args.Since,
    }

    for key, env_name in ENVIRONMENT_MAP.items():
        new_value = argument_values[key] or os.environ.get(env_name)
        if new_value:
            values[key] = new_value
            changed = True

    missing_keys = [key for key in DEFAULT_VALUES if not values.get(key)]
    if missing_keys:
        for key in missing_keys:
            values[key] = DEFAULT_VALUES[key]
        changed = True

    if changed or not ENV_PATH.exists():
        write_env_values(values)
        print('Actualizado config/.env desde parametros de CriptoPriceStart.bat.')
    else:
        print('config/.env sin cambios desde parametros de CriptoPriceStart.bat.')


if __name__ == '__main__':
    main()
