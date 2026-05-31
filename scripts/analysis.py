import json
from pathlib import Path

import pandas as pd

try:
    from console_style import header
    from Indicacdores import apply_indicator, get_indicator, load_indicators
    from csv_file_logger import build_download_dashboard, build_unique_csv_path, log_csv_file
except ImportError:
    from scripts.console_style import header
    from scripts.Indicacdores import apply_indicator, get_indicator, load_indicators
    from scripts.csv_file_logger import build_download_dashboard, build_unique_csv_path, log_csv_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
ANALYSIS_DATA_DIR = PROJECT_ROOT / 'data' / 'analysis'
SIGNAL_SYSTEMS_PATH = PROJECT_ROOT / 'config' / 'signal_systems.json'
ENV_PATH = PROJECT_ROOT / 'config' / '.env'
DEFAULT_SIGNAL_SYSTEM = {
    'name': 'EMA40 Close Cross',
    'indicators': [
        {
            'indicator_id': 'ema',
            'source': 'close',
            'length': 40,
        },
    ],
}


def add_ema40(
    df: pd.DataFrame,
    close_column: str = 'close',
) -> pd.DataFrame:
    if close_column not in df.columns:
        raise ValueError(f'No existe la columna requerida: {close_column}')

    result = df.copy()
    close = pd.to_numeric(result[close_column], errors='coerce')
    result['ema_40'] = close.ewm(span=40, adjust=False).mean()
    return result


def add_ema40_close_cross_signals(
    df: pd.DataFrame,
    close_column: str = 'close',
    ema_period: int = 40,
) -> pd.DataFrame:
    """Add EMA and close/EMA cross signals equivalent to the PineScript logic."""
    if close_column not in df.columns:
        raise ValueError(f'No existe la columna requerida: {close_column}')

    result = df.copy()
    close = pd.to_numeric(result[close_column], errors='coerce')
    ema_column = f'ema_{ema_period}'

    result[ema_column] = close.ewm(span=ema_period, adjust=False).mean()

    previous_close = close.shift(1)
    previous_ema = result[ema_column].shift(1)

    result['ema40XCloseOver'] = (previous_close <= previous_ema) & (close > result[ema_column])

    crossunder = (previous_close >= previous_ema) & (close < result[ema_column])
    previous_bar_crossover = (close.shift(2) <= result[ema_column].shift(2)) & (previous_close > previous_ema)
    result['ema40XCloseUnder'] = crossunder & ~previous_bar_crossover.fillna(False)

    return result


def load_signal_systems() -> list[dict[str, str]]:
    if not SIGNAL_SYSTEMS_PATH.exists():
        save_signal_systems([DEFAULT_SIGNAL_SYSTEM])

    data = json.loads(SIGNAL_SYSTEMS_PATH.read_text(encoding='utf-8'))
    signal_systems = data.get('signal_systems', [])
    return [normalize_signal_system(signal_system) for signal_system in signal_systems]


def normalize_signal_system(signal_system: dict) -> dict:
    if 'indicators' in signal_system:
        return signal_system

    indicator = {
        'indicator_id': signal_system.get('indicator_id', signal_system.get('type', 'ema')),
    }
    for key in ['source', 'length', 'fast_length', 'slow_length', 'signal_length', 'std_multiplier']:
        if key in signal_system:
            indicator[key] = signal_system[key]

    return {
        'name': signal_system.get('name', 'Sistema de senales'),
        'indicators': [indicator],
    }


def save_signal_systems(signal_systems: list[dict[str, str]]) -> None:
    SIGNAL_SYSTEMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_signal_systems = [normalize_signal_system(signal_system) for signal_system in signal_systems]
    SIGNAL_SYSTEMS_PATH.write_text(
        json.dumps({'signal_systems': normalized_signal_systems}, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def list_base_files() -> list[Path]:
    if not RAW_DATA_DIR.exists():
        return []
    return sorted(RAW_DATA_DIR.glob('*.csv'), key=lambda path: path.stat().st_mtime, reverse=True)


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
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key, value = stripped.split('=', 1)
            values[key.strip()] = value.strip()
    return values


def build_signal_systems_dashboard(signal_systems: list[dict]) -> str:
    return (
        '\n' + header('--- Estado sistemas de senales ---', 'status') + '\n'
        f'Sistemas guardados: {len(signal_systems)}\n'
        f'Archivo de sistemas: {SIGNAL_SYSTEMS_PATH.relative_to(PROJECT_ROOT)}'
    )


def select_base_file() -> Path | None:
    files = list_base_files()
    if not files:
        print('No hay archivos base en data/raw/. Ejecuta primero la opcion 2 del menu principal.')
        return None

    print('\n' + header('=== Archivos base disponibles ===', 'files'))
    for index, file_path in enumerate(files, start=1):
        default_marker = ' (ultimo generado)' if index == 1 else ''
        print(f'{index}) {file_path.name}{default_marker}')

    choice = prompt_input('Selecciona archivo base (Enter para usar el ultimo): ')
    if choice is None:
        return None
    if not choice:
        selected = files[0]
    elif choice.isdigit() and 1 <= int(choice) <= len(files):
        selected = files[int(choice) - 1]
    else:
        print('Opcion no valida.')
        return None

    print(f'Archivo base seleccionado: {selected.name}')
    return selected


def print_indicators(indicators: list[dict]) -> None:
    for index, indicator in enumerate(indicators, start=1):
        default_source = indicator.get('default_source', 'ohlc')
        default_length = indicator.get('default_length', 'n/a')
        print(f'{index}) {indicator["name"]} [{indicator["id"]}] source={default_source} length={default_length}')


def build_indicator_config(indicators: list[dict], default_indicator_id: str = 'ema') -> dict | None:
    print('\n' + header('--- Estado catalogo de indicadores ---', 'indicators'))
    print(f'Indicadores disponibles: {len(indicators)}')
    print('Archivo de indicadores: config/indicators.json')

    print('Indicadores disponibles:')
    print_indicators(indicators)

    indicator_choice = prompt_input('Selecciona indicador [1-{}] (Enter para EMA, A para atras): '.format(len(indicators)))
    if indicator_choice is None or indicator_choice.lower() == 'a':
        return None

    if not indicator_choice:
        indicator = get_indicator(default_indicator_id)
    elif indicator_choice.isdigit() and 1 <= int(indicator_choice) <= len(indicators):
        indicator = indicators[int(indicator_choice) - 1]
    else:
        print('Opcion no valida.')
        return None

    indicator_config = {
        'indicator_id': indicator['id'],
    }

    source = indicator.get('default_source', 'close')
    if indicator['id'] != 'atr':
        source_value = prompt_input(f'Source (Enter para {source}): ')
        if source_value is None:
            return None
        indicator_config['source'] = source_value or source

    length = indicator.get('default_length')
    if length is not None:
        length_value = prompt_input(f'Length (Enter para {length}): ')
        if length_value is None:
            return None
        indicator_config['length'] = int(length_value or length)

    for key in ['fast_length', 'slow_length', 'signal_length', 'std_multiplier']:
        if key in indicator:
            indicator_config[key] = indicator[key]

    return indicator_config


def create_signal_system() -> None:
    signal_systems = load_signal_systems()
    indicators = load_indicators()

    print('\n' + header('=== Crear Sistema de senales ===', 'signals'))
    name_value = prompt_input('Nombre del sistema de senales (Enter para EMA40 Close Cross): ')
    if name_value is None:
        return

    name = name_value or DEFAULT_SIGNAL_SYSTEM['name']
    if any(signal_system['name'].lower() == name.lower() for signal_system in signal_systems):
        print('Ya existe un sistema de senales con ese nombre.')
        return

    selected_indicators = []
    while True:
        indicator_config = build_indicator_config(indicators)
        if indicator_config is None:
            if selected_indicators:
                break
            print('Debes agregar al menos un indicador.')
            return

        selected_indicators.append(indicator_config)
        add_more = prompt_input('Agregar otro indicador? [s/N]: ')
        if add_more is None or add_more.lower() != 's':
            break

    signal_system = {
        'name': name,
        'indicators': selected_indicators,
    }
    signal_systems.append(signal_system)
    save_signal_systems(signal_systems)
    print(f'Sistema de senales creado: {name} ({len(selected_indicators)} indicador/es)')


def select_signal_system() -> dict[str, str] | None:
    signal_systems = load_signal_systems()
    if not signal_systems:
        print('No hay sistemas de senales creados.')
        return None

    print(build_signal_systems_dashboard(signal_systems))
    print('\n' + header('=== Sistemas de senales disponibles ===', 'signals'))
    for index, signal_system in enumerate(signal_systems, start=1):
        indicator_ids = ', '.join(indicator.get('indicator_id', indicator.get('type', 'ema')) for indicator in signal_system['indicators'])
        print(f'{index}) {signal_system["name"]} [{indicator_ids}]')
    print('A) Atras')

    choice = prompt_input('Selecciona sistema de senales [1-{}] o A para atras: '.format(len(signal_systems)))
    if choice is None or choice.lower() == 'a':
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(signal_systems):
        return signal_systems[int(choice) - 1]

    print('Opcion no valida.')
    return None


def apply_signal_system_to_dataframe(df: pd.DataFrame, signal_system: dict[str, str]) -> pd.DataFrame:
    signal_system = normalize_signal_system(signal_system)
    result = df.copy()
    calculated_columns = []
    for indicator_config in signal_system['indicators']:
        result, new_columns = apply_indicator(result, indicator_config)
        calculated_columns.extend(column for column in new_columns if column not in calculated_columns)

    result['signal_system_name'] = signal_system['name']

    ordered_columns = list(df.columns)
    if 'signal_system_name' not in ordered_columns:
        ordered_columns.append('signal_system_name')
    for column in calculated_columns:
        if column not in ordered_columns:
            ordered_columns.append(column)

    return result[ordered_columns]


def delete_signal_system() -> None:
    signal_systems = load_signal_systems()
    if not signal_systems:
        print('No hay sistemas de senales para eliminar.')
        return

    print(build_signal_systems_dashboard(signal_systems))
    print('\n' + header('=== Eliminar Sistema de senales ===', 'signals'))
    for index, signal_system in enumerate(signal_systems, start=1):
        print(f'{index}) {signal_system["name"]}')
    print('A) Atras')

    choice = prompt_input('Selecciona sistema a eliminar [1-{}] o A para atras: '.format(len(signal_systems)))
    if choice is None or choice.lower() == 'a':
        return
    if not choice.isdigit() or not 1 <= int(choice) <= len(signal_systems):
        print('Opcion no valida.')
        return

    selected = signal_systems[int(choice) - 1]
    confirm = prompt_input(f'Eliminar "{selected["name"]}"? [s/N]: ')
    if confirm is None or confirm.lower() != 's':
        print('Eliminacion cancelada.')
        return

    del signal_systems[int(choice) - 1]
    save_signal_systems(signal_systems)
    print(f'Sistema de senales eliminado: {selected["name"]}')


def build_analysis_filename(base_file: Path, signal_system: dict[str, str]) -> Path:
    return build_unique_csv_path(ANALYSIS_DATA_DIR, 'ana')


def apply_signal_system(base_file: Path | None = None) -> Path | None:
    selected_base_file = base_file or select_base_file()
    if selected_base_file is None:
        return None

    signal_system = select_signal_system()
    if signal_system is None:
        return None

    df = pd.read_csv(selected_base_file)
    analyzed_df = apply_signal_system_to_dataframe(df, signal_system)

    ANALYSIS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = build_analysis_filename(selected_base_file, signal_system)
    analyzed_df.to_csv(output_path, index=False)
    description = (
        f'Analisis de datos | base={selected_base_file.name} | '
        f'sistema={signal_system["name"]} | filas={len(analyzed_df)}'
    )
    dashboard = (
        f'{build_download_dashboard(read_env_values())}\n'
        f'Archivo base analizado: {selected_base_file.name}\n'
        f'Sistema de senales aplicado: {signal_system["name"]}'
    )
    log_csv_file(output_path, description, dashboard)

    print(f'Analisis guardado: {output_path}')
    return output_path


def show_analysis_menu(current_file: Path | None) -> None:
    selected_name = current_file.name if current_file else 'ultimo archivo generado por defecto'
    download_dashboard = build_download_dashboard(read_env_values()).replace(
        '--- Estado actual de descarga ---',
        header('--- Estado actual de descarga ---', 'status'),
        1,
    )
    dashboard = (
        f'{download_dashboard}\n'
        f'Archivo base actual para analisis: {selected_name}\n'
        f'Sistemas de senales guardados: {len(load_signal_systems())}'
    )
    print(f'\n{dashboard}')
    print('\n' + header('=== Analisis ===', 'analysis'))
    print('1) Cargar Archivos Base')
    print('2) Crear Sistema de senales')
    print('3) Aplicar Sistema de senales')
    print('4) Eliminar Sistema de senales')
    print('5) Volver al menu principal')


def prompt_input(prompt: str) -> str | None:
    try:
        return input(prompt).strip()
    except EOFError:
        print('\nEntrada finalizada. Volviendo al menu anterior.')
        return None


def analysis_menu() -> None:
    current_file = list_base_files()[0] if list_base_files() else None

    while True:
        show_analysis_menu(current_file)
        choice = prompt_input('Selecciona una opcion [1-5]: ')
        if choice is None:
            break

        if choice == '1':
            selected_file = select_base_file()
            if selected_file is not None:
                current_file = selected_file
        elif choice == '2':
            create_signal_system()
        elif choice == '3':
            output_path = apply_signal_system(current_file)
            if output_path is not None:
                print('Columnas agregadas: signal_system_name y columnas calculadas por el sistema de senales.')
        elif choice == '4':
            delete_signal_system()
        elif choice == '5':
            break
        else:
            print('Opcion no valida. Intenta de nuevo.')


def main() -> None:
    analysis_menu()


if __name__ == '__main__':
    main()
