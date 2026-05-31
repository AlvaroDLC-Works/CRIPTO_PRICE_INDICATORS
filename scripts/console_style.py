import os


os.system('')

RESET = '\033[0m'
STYLES = {
    'status': '\033[96m',
    'main': '\033[95m',
    'tools': '\033[93m',
    'analysis': '\033[94m',
    'charts': '\033[92m',
    'cleanup': '\033[91m',
    'config': '\033[36m',
    'files': '\033[35m',
    'signals': '\033[34m',
    'indicators': '\033[32m',
}


def color_text(text: str, style: str) -> str:
    if os.environ.get('NO_COLOR'):
        return text
    return f'{STYLES.get(style, "")}{text}{RESET}'


def header(text: str, style: str) -> str:
    return color_text(text, style)
