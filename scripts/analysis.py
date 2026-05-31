import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from Indicacdores import apply_indicator, get_indicator, load_indicators
except ImportError:
    from scripts.Indicacdores import apply_indicator, get_indicator, load_indicators


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
ANALYSIS_DATA_DIR = PROJECT_ROOT / 'data' / 'analysis'
SIGNAL_SYSTEMS_PATH = PROJECT_ROOT / 'config' / 'signal_systems.json'
DEFAULT_SIGNAL_SYSTEM = {
    'name': 'EMA40 Close Cross',
    'indicator_id': 'ema',
    'source': 'close',
    'length': 40,
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
    if not signal_systems:
        signal_systems = [DEFAULT_SIGNAL_SYSTEM]
        save_signal_systems(signal_systems)
    return signal_systems


def save_signal_systems(signal_systems: list[dict[str, str]]) -> None:
    SIGNAL_SYSTEMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SIGNAL_SYSTEMS_PATH.write_text(
        json.dumps({'signal_systems': signal_systems}, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def list_base_files() -> list[Path]:
    if not RAW_DATA_DIR.exists():
        return []
    return sorted(RAW_DATA_DIR.glob('*.csv'), key=lambda path: path.stat().st_mtime, reverse=True)


def select_base_file() -> Path | None:
    files = list_base_files()
    if not files:
        print('No hay archivos base en data/raw/. Ejecuta primero la opcion 1 del menu principal.')
        return None

    print('\n=== Archivos base disponibles ===')
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


def create_signal_system() -> None:
    signal_systems = load_signal_systems()
    indicators = load_indicators()

    print('\n=== Crear Sistema de senales ===')
    print('Indicadores disponibles:')
    for index, indicator in enumerate(indicators, start=1):
        default_source = indicator.get('default_source', 'ohlc')
        default_length = indicator.get('default_length', 'n/a')
        print(f'{index}) {indicator["name"]} [{indicator["id"]}] source={default_source} length={default_length}')

    name_value = prompt_input('Nombre del sistema de senales (Enter para EMA40 Close Cross): ')
    if name_value is None:
        return
    indicator_choice = prompt_input('Selecciona indicador [1-{}] (Enter para EMA): '.format(len(indicators)))
    if indicator_choice is None:
        return

    name = name_value or DEFAULT_SIGNAL_SYSTEM['name']
    if not indicator_choice:
        indicator = get_indicator(DEFAULT_SIGNAL_SYSTEM['indicator_id'])
    elif indicator_choice.isdigit() and 1 <= int(indicator_choice) <= len(indicators):
        indicator = indicators[int(indicator_choice) - 1]
    else:
        print('Opcion no valida.')
        return

    source = indicator.get('default_source', 'close')
    if indicator['id'] != 'atr':
        source_value = prompt_input(f'Source (Enter para {source}): ')
        if source_value is None:
            return
        source = source_value or source

    length = indicator.get('default_length')
    length_value = None
    if length is not None:
        length_value = prompt_input(f'Length (Enter para {length}): ')
        if length_value is None:
            return
        length = int(length_value or length)

    if any(signal_system['name'].lower() == name.lower() for signal_system in signal_systems):
        print('Ya existe un sistema de senales con ese nombre.')
        return

    signal_system = {
        'name': name,
        'indicator_id': indicator['id'],
    }
    if indicator['id'] != 'atr':
        signal_system['source'] = source
    if length is not None:
        signal_system['length'] = length
    for key in ['fast_length', 'slow_length', 'signal_length', 'std_multiplier']:
        if key in indicator:
            signal_system[key] = indicator[key]

    signal_systems.append(signal_system)
    save_signal_systems(signal_systems)
    print(f'Sistema de senales creado: {name} ({indicator["id"]})')


def select_signal_system() -> dict[str, str] | None:
    signal_systems = load_signal_systems()

    print('\n=== Sistemas de senales disponibles ===')
    for index, signal_system in enumerate(signal_systems, start=1):
        indicator_id = signal_system.get('indicator_id', signal_system.get('type', 'ema40'))
        print(f'{index}) {signal_system["name"]} [{indicator_id}]')

    choice = prompt_input('Selecciona sistema de senales [1-{}]: '.format(len(signal_systems)))
    if choice is None:
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(signal_systems):
        return signal_systems[int(choice) - 1]

    print('Opcion no valida.')
    return None


def apply_signal_system_to_dataframe(df: pd.DataFrame, signal_system: dict[str, str]) -> pd.DataFrame:
    if 'indicator_id' not in signal_system and signal_system.get('type') == 'ema40':
        signal_system = {
            **signal_system,
            'indicator_id': 'ema',
            'source': 'close',
            'length': 40,
        }

    result, calculated_columns = apply_indicator(df, signal_system)
    result['signal_system_name'] = signal_system['name']

    ordered_columns = list(df.columns)
    if 'signal_system_name' not in ordered_columns:
        ordered_columns.append('signal_system_name')
    for column in calculated_columns:
        if column not in ordered_columns:
            ordered_columns.append(column)

    return result[ordered_columns]


def sanitize_filename_part(value: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9]+', '', value)
    return cleaned or 'signals'


def build_analysis_filename(base_file: Path, signal_system: dict[str, str]) -> Path:
    timestamp = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')
    signal_system_code = sanitize_filename_part(signal_system['name'])
    return ANALYSIS_DATA_DIR / f'{base_file.stem}{signal_system_code}{timestamp}.csv'


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

    print(f'Analisis guardado: {output_path}')
    return output_path


def show_analysis_menu(current_file: Path | None) -> None:
    selected_name = current_file.name if current_file else 'ultimo archivo generado por defecto'
    print('\n=== Analisis ===')
    print(f'Archivo base actual: {selected_name}')
    print('1) Cargar Archivos Base')
    print('2) Crear Sistema de senales')
    print('3) Aplicar Sistema de senales')
    print('4) Volver al menu principal')


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
        choice = prompt_input('Selecciona una opcion [1-4]: ')
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
            break
        else:
            print('Opcion no valida. Intenta de nuevo.')


def main() -> None:
    analysis_menu()


if __name__ == '__main__':
    main()
