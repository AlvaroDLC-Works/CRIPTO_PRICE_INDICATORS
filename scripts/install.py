from pathlib import Path
import subprocess
import sys

REQUIRED_PACKAGES = {
    'ccxt': 'ccxt',
    'pandas': 'pandas',
    'python-dotenv': 'dotenv',
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def python_executable() -> str:
    return sys.executable


def load_env_file() -> None:
    env_path = PROJECT_ROOT / 'config' / '.env'
    example_path = PROJECT_ROOT / 'config' / '.env.example'
    env_path.parent.mkdir(parents=True, exist_ok=True)

    if not env_path.exists():
        if example_path.exists():
            env_path.write_text(example_path.read_text(encoding='utf-8'), encoding='utf-8')
            print('Se creo config/.env a partir de config/.env.example.')
        else:
            env_path.write_text(
                'EXCHANGE=binance\n'
                'FALLBACK_EXCHANGES=bybit,okx,kucoin\n'
                'SYMBOLS=BTC,ETH\n'
                'TIMEFRAME=1d\n',
                encoding='utf-8',
            )
            print('Se creo config/.env con valores de ejemplo.')
    else:
        print('config/.env encontrado.')

    required_keys = ['EXCHANGE', 'SYMBOLS', 'TIMEFRAME']
    env_text = env_path.read_text(encoding='utf-8')
    missing_keys = [key for key in required_keys if f'{key}=' not in env_text]

    if missing_keys:
        print('Advertencia: faltan claves en config/.env:', ', '.join(missing_keys))
        print('Por favor, actualiza config/.env con los valores necesarios.')
    else:
        print('Claves config/.env verificadas.')


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
    requirements = PROJECT_ROOT / 'requirements.txt'
    if not requirements.exists():
        raise SystemExit('No se encontro requirements.txt.')

    print('Instalando dependencias desde requirements.txt...')
    subprocess.check_call([python_executable(), '-m', 'pip', 'install', '-r', str(requirements)])
    print('Instalacion de dependencias completada.')


def main() -> None:
    print('Verificando el entorno de instalacion...')

    if sys.version_info < (3, 8):
        raise SystemExit('Python 3.8 o superior es requerido.')

    load_env_file()
    check_dependencies()

    print('\nInstalacion y verificacion completadas.')
    print('Ejecuta py scripts/fetch_crypto_data.py para descargar datos.')


if __name__ == '__main__':
    main()
