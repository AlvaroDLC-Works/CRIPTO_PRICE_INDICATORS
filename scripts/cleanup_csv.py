from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
BACKUP_DIR = PROJECT_ROOT / 'backup'
TARGET_DIRS = {
    'raw': DATA_DIR / 'raw',
    'analysis': DATA_DIR / 'analysis',
}


def list_csv_files(target_names: list[str]) -> list[Path]:
    files = []
    for target_name in target_names:
        target_dir = TARGET_DIRS[target_name]
        if target_dir.exists():
            files.extend(sorted(path.resolve() for path in target_dir.glob('*.csv')))
    return files


def build_backup_name(backup_type: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')
    return BACKUP_DIR / f'{backup_type}{timestamp}.zip'


def build_cleanup_dashboard() -> str:
    raw_count = len(list(TARGET_DIRS['raw'].glob('*.csv'))) if TARGET_DIRS['raw'].exists() else 0
    analysis_count = len(list(TARGET_DIRS['analysis'].glob('*.csv'))) if TARGET_DIRS['analysis'].exists() else 0
    return (
        '\n--- Estado actual de CSV ---\n'
        f'CSV en data/raw: {raw_count}\n'
        f'CSV en data/analysis: {analysis_count}\n'
        f'Carpeta backup: {BACKUP_DIR.relative_to(PROJECT_ROOT)}'
    )


def backup_and_clean(target_names: list[str], backup_type: str) -> Path | None:
    csv_files = list_csv_files(target_names)
    if not csv_files:
        print('No se encontraron archivos CSV para limpiar.')
        return None

    print('\nArchivos que se moveran al backup:')
    for file_path in csv_files:
        print(f'- {file_path.resolve().relative_to(PROJECT_ROOT)}')

    confirmation_value = prompt_input('\nConfirma limpieza y backup [s/N]: ')
    if confirmation_value is None:
        return None

    confirmation = confirmation_value.lower()
    if confirmation not in {'s', 'si', 'y', 'yes'}:
        print('Operacion cancelada.')
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = build_backup_name(backup_type)

    with ZipFile(backup_path, 'w', compression=ZIP_DEFLATED) as zip_file:
        for file_path in csv_files:
            resolved_file = file_path.resolve()
            zip_file.write(resolved_file, arcname=resolved_file.relative_to(PROJECT_ROOT))

    for file_path in csv_files:
        file_path.unlink()

    print(f'Backup creado: {backup_path}')
    print(f'CSV limpiados: {len(csv_files)}')
    return backup_path


def show_menu() -> None:
    print(build_cleanup_dashboard())
    print('\n=== Limpieza CSV ===')
    print('1) Limpiar data/raw')
    print('2) Limpiar data/analysis')
    print('3) Limpiar todo data/raw + data/analysis')
    print('4) Volver')


def prompt_input(prompt: str) -> str | None:
    try:
        return input(prompt).strip()
    except EOFError:
        print('\nEntrada finalizada. Volviendo al menu anterior.')
        return None


def main() -> None:
    while True:
        show_menu()
        choice = prompt_input('Selecciona una opcion [1-4]: ')
        if choice is None:
            break

        if choice == '1':
            backup_and_clean(['raw'], 'raw')
        elif choice == '2':
            backup_and_clean(['analysis'], 'analysis')
        elif choice == '3':
            backup_and_clean(['raw', 'analysis'], 'todos')
        elif choice == '4':
            break
        else:
            print('Opcion no valida. Intenta de nuevo.')


if __name__ == '__main__':
    main()
