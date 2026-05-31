import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / 'config' / '.env'
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


def run_script(script_name: str) -> int:
    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        print(f'Error: {script_name} no existe en el proyecto.')
        return 1

    command = [sys.executable, str(script_path)]
    print(f'Ejecutando: {command}')
    result = subprocess.run(command)
    return result.returncode


def prompt_input(prompt: str) -> str | None:
    try:
        return input(prompt).strip()
    except EOFError:
        print('\nEntrada finalizada. Volviendo/saliendo del menu actual.')
        return None


def show_menu() -> None:
    print(build_download_dashboard())
    print('\n=== CriptoPrice Menu ===')
    print('1) Configurar Descarga (config/.env)')
    print('2) Descargar Datos (fetch_crypto_data)')
    print('3) Analisis de Datos')
    print('4) Herramientas')
    print('5) Salir')


def show_tools_menu() -> None:
    print('\n=== Herramientas ===')
    print('1) Verificar / reparar ambiente (install)')
    print('2) Regenerar config/env_config_fields.json')
    print('3) Limpiar CSV con backup')
    print('4) Volver al menu principal')


def read_env_values() -> dict[str, str]:
    values = {
        'EXCHANGE': 'binance',
        'FALLBACK_EXCHANGES': 'bybit,okx,kucoin',
        'SYMBOLS': 'BTC',
        'TIMEFRAME': '1d',
        'LIMIT': '1000',
        'SINCE': 'sin fecha inicial',
    }

    if not ENV_PATH.exists():
        return values

    for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue

        key, value = stripped.split('=', 1)
        values[key.strip()] = value.strip()

    return values


def parse_base_symbols(raw_symbols: str) -> list[str]:
    return [symbol.strip().split('/', 1)[0].upper() for symbol in raw_symbols.split(',') if symbol.strip()]


def get_latest_raw_file() -> str:
    if not RAW_DATA_DIR.exists():
        return 'sin archivo base'

    files = sorted(RAW_DATA_DIR.glob('*.csv'), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        return 'sin archivo base'
    return files[0].name


def build_download_dashboard() -> str:
    values = read_env_values()
    exchange = values['EXCHANGE']
    fallback_exchanges = values.get('FALLBACK_EXCHANGES', 'bybit,okx,kucoin')
    base_symbols = parse_base_symbols(values['SYMBOLS'])
    pairs = ', '.join(f'{symbol}/USDT' for symbol in base_symbols)
    base_assets = ', '.join(base_symbols)

    return (
        '\n--- Estado actual de descarga ---\n'
        f'Exchange: {exchange}\n'
        f'Fallback exchanges: {fallback_exchanges}\n'
        f'Activos base: {base_assets}\n'
        f'Pares a descargar: {pairs}\n'
        f'Timeframe: {values["TIMEFRAME"]}\n'
        f'Limite por batch: {values["LIMIT"]}\n'
        f'Desde: {values["SINCE"]}\n'
        f'Archivo base actual: {get_latest_raw_file()}\n'
        'Activo de intercambio asumido: USDT'
    )


def tools_menu() -> None:
    while True:
        show_tools_menu()
        choice = prompt_input('Selecciona una herramienta [1-4]: ')
        if choice is None:
            break

        if choice == '1':
            run_script('scripts/install.py')
        elif choice == '2':
            run_script('scripts/env_config_fields_generator.py')
        elif choice == '3':
            run_script('scripts/cleanup_csv.py')
        elif choice == '4':
            break
        else:
            print('Opcion no valida. Intenta de nuevo.')


def main() -> None:
    while True:
        show_menu()
        choice = prompt_input('Selecciona una opcion [1-5]: ')
        if choice is None:
            break

        if choice == '1':
            run_script('scripts/env_config_editor.py')
        elif choice == '2':
            run_script('scripts/fetch_crypto_data.py')
        elif choice == '3':
            run_script('scripts/analysis.py')
        elif choice == '4':
            tools_menu()
        elif choice == '5':
            print('Saliendo...')
            break
        else:
            print('Opcion no valida. Intenta de nuevo.')


if __name__ == '__main__':
    main()
