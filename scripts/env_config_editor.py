import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_PATH = PROJECT_ROOT / 'config' / '.env'
DEFAULT_FIELDS_PATH = PROJECT_ROOT / 'config' / 'env_config_fields.json'


def load_config_fields(fields_path: Path = DEFAULT_FIELDS_PATH) -> list[dict[str, str]]:
    if not fields_path.exists():
        raise FileNotFoundError(f'No existe el archivo de campos: {fields_path}')

    data = json.loads(fields_path.read_text(encoding='utf-8'))
    fields = data.get('fields') if isinstance(data, dict) else data

    if not isinstance(fields, list) or not fields:
        raise ValueError('El archivo de campos debe contener una lista no vacia.')

    normalized_fields = []
    for index, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            raise ValueError(f'El campo #{index} debe ser un objeto JSON.')

        key = str(field.get('key', '')).strip()
        if not key:
            raise ValueError(f'El campo #{index} no tiene key.')

        normalized_fields.append({
            'key': key,
            'label': str(field.get('label') or key).strip(),
            'default': str(field.get('default', '')).strip(),
        })

    return normalized_fields


def read_key_value_lines(target_path: Path) -> list[str]:
    if target_path.exists():
        return target_path.read_text(encoding='utf-8').splitlines()
    return []


def get_key_value_data(lines: list[str], fields: list[dict[str, str]]) -> dict[str, str]:
    values = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in line:
            continue

        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()

    for field in fields:
        values.setdefault(field['key'], field['default'])

    return values


def build_download_dashboard(values: dict[str, str]) -> str:
    raw_symbols = values.get('SYMBOLS', 'BTC')
    base_symbols = [symbol.strip().split('/', 1)[0].upper() for symbol in raw_symbols.split(',') if symbol.strip()]
    base_assets = ', '.join(base_symbols)
    pairs = ', '.join(f'{symbol}/USDT' for symbol in base_symbols)

    return (
        '\n--- Estado actual de descarga ---\n'
        f'Exchange: {values.get("EXCHANGE", "binance")}\n'
        f'Fallback exchanges: {values.get("FALLBACK_EXCHANGES", "bybit,okx,kucoin")}\n'
        f'Activos base: {base_assets}\n'
        f'Pares a descargar: {pairs}\n'
        f'Timeframe: {values.get("TIMEFRAME", "1d")}\n'
        f'Limite por batch: {values.get("LIMIT", "1000")}\n'
        f'Desde: {values.get("SINCE", "sin fecha inicial")}\n'
        'Activo de intercambio asumido: USDT'
    )


def set_key_value_data(lines: list[str], key: str, value: str) -> list[str]:
    updated_lines = []
    found = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in line:
            updated_lines.append(line)
            continue

        current_key, _ = line.split('=', 1)
        if current_key.strip() == key:
            updated_lines.append(f'{key}={value}')
            found = True
        else:
            updated_lines.append(line)

    if not found:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append('')
        updated_lines.append(f'{key}={value}')

    return updated_lines


def save_key_value_lines(target_path: Path, lines: list[str]) -> None:
    target_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def select_field(target_path: Path, fields: list[dict[str, str]]) -> dict[str, str] | None:
    exit_option = len(fields) + 1
    display_path = target_path.relative_to(PROJECT_ROOT)

    while True:
        lines = read_key_value_lines(target_path)
        values = get_key_value_data(lines, fields)

        print(f'\n=== Editar configuracion {display_path} ===')
        for index, field in enumerate(fields, start=1):
            key = field['key']
            print(f'{index}) {key} = {values[key]}')
        print(f'{exit_option}) Volver al menu principal')
        print(build_download_dashboard(values))

        choice = input(f'Selecciona el dato a revisar [1-{exit_option}]: ').strip()
        if choice == str(exit_option):
            return None

        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(fields):
                return fields[index - 1]

        print('Opcion no valida. Intenta de nuevo.')


def update_selected_field(target_path: Path, fields: list[dict[str, str]], field: dict[str, str]) -> None:
    lines = read_key_value_lines(target_path)
    values = get_key_value_data(lines, fields)
    key = field['key']
    current_value = values[key]

    print(f'\n{field["label"]}')
    print(f'Parametro actual: {key}={current_value}')
    new_value = input('Nuevo valor (Enter para mantener el anterior): ').strip()

    if not new_value:
        print(f'Se mantiene {key}={current_value}')
        return

    lines = set_key_value_data(lines, key, new_value)
    save_key_value_lines(target_path, lines)
    print(f'Actualizado: {key}={new_value}')


def run_editor(
    target_path: Path = DEFAULT_TARGET_PATH,
    fields_path: Path = DEFAULT_FIELDS_PATH,
) -> None:
    fields = load_config_fields(fields_path)

    while True:
        field = select_field(target_path, fields)
        if field is None:
            break
        update_selected_field(target_path, fields, field)


def main() -> None:
    try:
        run_editor()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f'Error al cargar el editor de configuracion: {exc}')


if __name__ == '__main__':
    main()
