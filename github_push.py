from pathlib import Path
import subprocess
import sys
from typing import Optional


def run_git(args, capture_output: bool = False) -> str:
    result = subprocess.run(['git'] + args, capture_output=capture_output, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} falló")
    return result.stdout.strip()


def ensure_repo_initialized() -> str:
    if not Path('.git').exists():
        print('Inicializando repositorio git...')
        run_git(['init'])

    branch = run_git(['branch', '--show-current'], capture_output=True)
    if not branch:
        branch = 'main'
    return branch


def get_remote_url() -> Optional[str]:
    try:
        return run_git(['remote', 'get-url', 'origin'], capture_output=True)
    except RuntimeError:
        return None


def get_env_remote() -> Optional[str]:
    env_path = Path('.env')
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        if line.startswith('GITHUB_REMOTE='):
            return line.split('=', 1)[1].strip() or None
    return None


def add_remote(remote: str) -> None:
    print(f'Agregando remote origin: {remote}')
    run_git(['remote', 'add', 'origin', remote])


def commit_changes(message: str) -> bool:
    status = run_git(['status', '--short'], capture_output=True)
    if not status:
        print('No hay cambios para commitear.')
        return False

    run_git(['add', '--all'])
    run_git(['commit', '-m', message])
    print('Commit creado.')
    return True


def push_changes(branch: str) -> None:
    print(f'Pushing a remote origin rama {branch}...')
    run_git(['push', '-u', 'origin', branch])
    print('Push completado.')


def main() -> None:
    branch = ensure_repo_initialized()
    remote = get_remote_url() or get_env_remote()

    if remote is None:
        raise SystemExit('No se encontró un remote SSH. Ajusta GITHUB_REMOTE en .env o configura origin.')

    if get_remote_url() is None:
        add_remote(remote)

    try:
        print('Verificando conexión SSH con remote...')
        run_git(['ls-remote', remote], capture_output=True)
    except RuntimeError as exc:
        raise SystemExit(f'La conexión SSH falló o el remote no es accesible: {exc}')

    if commit_changes('Actualización automática de código'):
        push_changes(branch)
    else:
        print('Nada nuevo que subir.')


if __name__ == '__main__':
    main()
