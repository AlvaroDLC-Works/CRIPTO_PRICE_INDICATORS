from pathlib import Path
import subprocess
import sys

REQUIRED_PACKAGES = {
    'ccxt': 'ccxt',
    'pandas': 'pandas',
    'python-dotenv': 'dotenv',
}


def python_executable() -> str:
    return sys.executable


def load_env_file() -> None:
    env_path = Path('.env')
    example_path = Path('.env.example')

    if not env_path.exists():
        if example_path.exists():
            env_path.write_text(example_path.read_text())
            print('Se creó .env a partir de .env.example.')
        else:
            env_path.write_text(
                'GITHUB_REMOTE=git@github.com:username/CriptoPrice.git\n'
                'EXCHANGE=binance\n'
                'SYMBOLS=BTC/USDT,ETH/USDT\n'
                'TIMEFRAME=1d\n'
                'LIMIT=1000\n'
                'SINCE=2015-01-01\n'
            )
            print('Se creó .env con valores de ejemplo.')
    else:
        print('.env encontrado.')

    required_keys = ['GITHUB_REMOTE', 'EXCHANGE', 'SYMBOLS', 'TIMEFRAME', 'LIMIT', 'SINCE']
    env_text = env_path.read_text()
    missing_keys = [key for key in required_keys if f'{key}=' not in env_text]

    if missing_keys:
        print('Advertencia: faltan claves en .env:', ', '.join(missing_keys))
        print('Por favor, actualiza .env con los valores necesarios.')
    else:
        print('Claves .env verificadas.')


def check_dependencies() -> None:
    missing = []
    for package, module_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package)

    if missing:
        print('Paquetes faltantes:', ', '.join(missing))
        install_requirements()
    else:
        print('Dependencias instaladas.')


def install_requirements() -> None:
    requirements = Path('requirements.txt')
    if not requirements.exists():
        raise SystemExit('No se encontró requirements.txt.')

    print('Instalando dependencias desde requirements.txt...')
    subprocess.check_call([python_executable(), '-m', 'pip', 'install', '-r', str(requirements)])
    print('Instalación de dependencias completada.')


def ensure_git_initialized() -> None:
    if not Path('.git').exists():
        print('No se encontró un repositorio git. Se inicializará uno nuevo.')
        subprocess.check_call(['git', 'init'])
        print('Repositorio git inicializado.')
    else:
        print('Repositorio git ya inicializado.')


def main() -> None:
    print('Verificando el entorno de instalación...')

    if sys.version_info < (3, 8):
        raise SystemExit('Python 3.8 o superior es requerido.')

    ensure_git_initialized()
    load_env_file()
    check_dependencies()

    print('\nInstalación y verificación completadas.')
    print('Ejecuta python fetch_crypto_data.py para descargar datos.')


if __name__ == '__main__':
    main()
