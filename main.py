import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run_script(script_name: str) -> int:
    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        print(f'Error: {script_name} no existe en el proyecto.')
        return 1

    command = [sys.executable, str(script_path)]
    print(f'Ejecutando: {command}')
    result = subprocess.run(command)
    return result.returncode


def show_menu() -> None:
    print('\n=== CriptoPrice Menu ===')
    print('1) Instalar / verificar dependencias')
    print('2) Descargar datos (fetch_crypto_data)')
    print('3) Subir cambios a GitHub (github_push)')
    print('4) Salir')


def main() -> None:
    while True:
        show_menu()
        choice = input('Selecciona una opción [1-4]: ').strip()

        if choice == '1':
            run_script('install.py')
        elif choice == '2':
            run_script('fetch_crypto_data.py')
        elif choice == '3':
            run_script('github_push.py')
        elif choice == '4':
            print('Saliendo...')
            break
        else:
            print('Opción no válida. Intenta de nuevo.')


if __name__ == '__main__':
    main()
