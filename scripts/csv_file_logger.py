from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
CSV_LOG_PATH = DATA_DIR / 'csv_files_log.txt'


def build_unique_csv_path(target_dir: Path, prefix: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')

    for counter in range(1, 100):
        csv_id = f'{prefix}{timestamp}{counter:02d}'
        candidate = target_dir / f'{csv_id}.csv'
        if not candidate.exists():
            return candidate

    raise RuntimeError('No se pudo generar un nombre unico para el CSV.')


def build_download_dashboard(values: dict[str, str]) -> str:
    raw_symbols = values.get('SYMBOLS', 'BTC')
    base_symbols = [symbol.strip().split('/', 1)[0].upper() for symbol in raw_symbols.split(',') if symbol.strip()]
    base_assets = ', '.join(base_symbols) or 'sin activos'
    pairs = ', '.join(f'{symbol}/USDT' for symbol in base_symbols) or 'sin pares'

    return (
        '--- Estado actual de descarga ---\n'
        f'Exchange: {values.get("EXCHANGE", "binance")}\n'
        f'Fallback exchanges: {values.get("FALLBACK_EXCHANGES", "bybit,okx,kucoin")}\n'
        f'Activos base: {base_assets}\n'
        f'Pares a descargar: {pairs}\n'
        f'Timeframe: {values.get("TIMEFRAME", "1d")}\n'
        f'Limite por batch: {values.get("LIMIT", "1000")}\n'
        f'Desde: {values.get("SINCE", "sin fecha inicial")}\n'
        'Activo de intercambio asumido: USDT'
    )


def log_csv_file(csv_path: Path, description: str, dashboard: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resolved_path = csv_path.resolve()
    relative_path = resolved_path.relative_to(PROJECT_ROOT)
    csv_id = csv_path.stem
    created_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (
        f'[{created_at}] {csv_id}\n'
        f'Archivo: {relative_path}\n'
        f'Descripcion: {description}\n'
        f'{dashboard}\n'
        '---\n'
    )
    with CSV_LOG_PATH.open('a', encoding='utf-8') as log_file:
        log_file.write(entry)
