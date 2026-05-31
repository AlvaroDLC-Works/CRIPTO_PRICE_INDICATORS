import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_PATH = PROJECT_ROOT / 'config' / '.env'
DEFAULT_FIELDS_PATH = PROJECT_ROOT / 'config' / 'env_config_fields.json'


def parse_env_file(source_path: Path = DEFAULT_SOURCE_PATH) -> list[dict[str, str]]:
    if not source_path.exists():
        raise FileNotFoundError(f'No existe el archivo fuente: {source_path}')

    fields = []
    pending_comments = []

    for line_number, line in enumerate(source_path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = line.lstrip('\ufeff').strip()

        if not stripped:
            pending_comments = []
            continue

        if stripped.startswith('#'):
            pending_comments.append(stripped.lstrip('#').strip())
            continue

        if '=' not in line:
            raise ValueError(f'Linea {line_number} invalida: se esperaba KEY=valor.')

        key, default = line.split('=', 1)
        key = key.strip()
        if not key:
            raise ValueError(f'Linea {line_number} invalida: key vacia.')

        label = ' '.join(comment for comment in pending_comments if comment).strip() or key
        fields.append({
            'key': key,
            'label': label,
            'default': default.strip(),
        })
        pending_comments = []

    if not fields:
        raise ValueError('No se encontraron campos KEY=valor en el archivo fuente.')

    return fields


def save_config_fields(fields: list[dict[str, str]], fields_path: Path = DEFAULT_FIELDS_PATH) -> None:
    content = {
        'fields': fields,
    }
    fields_path.parent.mkdir(parents=True, exist_ok=True)
    fields_path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def generate_config_fields(
    source_path: Path = DEFAULT_SOURCE_PATH,
    fields_path: Path = DEFAULT_FIELDS_PATH,
) -> list[dict[str, str]]:
    fields = parse_env_file(source_path)
    save_config_fields(fields, fields_path)
    return fields


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Genera env_config_fields.json desde config/.env.',
    )
    parser.add_argument(
        '--source',
        default=str(DEFAULT_SOURCE_PATH),
        help='Ruta del archivo .env usado como fuente.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_FIELDS_PATH),
        help='Ruta donde se escribira el JSON de campos.',
    )
    args = parser.parse_args()

    try:
        fields = generate_config_fields(Path(args.source), Path(args.output))
    except (OSError, ValueError) as exc:
        print(f'Error al generar campos de configuracion: {exc}')
        return

    print(f'Generado: {args.output} ({len(fields)} campos)')


if __name__ == '__main__':
    main()
