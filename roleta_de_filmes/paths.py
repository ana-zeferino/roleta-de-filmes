"""Resolução de caminhos que funciona tanto rodando via `python app.py`
quanto dentro de um .app empacotado pelo PyInstaller.

- recursos só-leitura (web/, data/) -> ao lado do código ou em sys._MEIPASS
- dados graváveis (movies.json) -> pasta do usuário (Application Support)
"""

import os
import sys

APP_NAME = "Roleta de Filmes"
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)


def is_frozen():
    return getattr(sys, "frozen", False)


def resource_path(*parts):
    """Caminho de um recurso do pacote `roleta_de_filmes` (só-leitura)."""
    if is_frozen():
        base = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)), "roleta_de_filmes")
    else:
        base = PACKAGE_DIR
    return os.path.join(base, *parts)


def data_dir():
    """Pasta gravável e persistente para os dados do usuário."""
    if sys.platform == "darwin":
        base = os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
    else:
        base = os.path.expanduser(f"~/.local/share/{APP_NAME}")
    os.makedirs(base, exist_ok=True)
    return base
