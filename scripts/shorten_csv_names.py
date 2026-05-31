from pathlib import Path

try:
    from csv_file_logger import build_unique_csv_path, log_csv_file
except ImportError:
    from scripts.csv_file_logger import build_unique_csv_path, log_csv_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
TARGETS = {
    'raw': DATA_DIR / 'raw',
    'ana': DATA_DIR / 'analysis',
}


def is_short_csv_name(path: Path, prefix: str) -> bool:
    stem = path.stem
    return stem.startswith(prefix) and len(stem) == 17 and stem[3:].isdigit()


def shorten_existing_csv_files() -> int:
    renamed_count = 0
    for prefix, target_dir in TARGETS.items():
        if not target_dir.exists():
            continue

        for csv_path in sorted(target_dir.glob('*.csv')):
            if is_short_csv_name(csv_path, prefix):
                continue

            new_path = build_unique_csv_path(target_dir, prefix)
            original_name = csv_path.name
            csv_path.rename(new_path)
            dashboard = (
                '--- Migracion de nombres CSV ---\n'
                f'Tipo: {prefix}\n'
                f'Archivo original: {original_name}\n'
                f'Archivo nuevo: {new_path.name}'
            )
            log_csv_file(
                new_path,
                f'Migracion de nombre corto | original={original_name}',
                dashboard,
            )
            print(f'{original_name} -> {new_path.name}')
            renamed_count += 1

    return renamed_count


def main() -> None:
    renamed_count = shorten_existing_csv_files()
    print(f'CSV renombrados: {renamed_count}')


if __name__ == '__main__':
    main()
