"""Leitura/gravação da lista de filmes em movies.json (na pasta de dados do usuário).

Cada item tem o formato:
{
    "id": str,            # id estável interno
    "title": str,         # título como digitado pela usuária
    "tmdb_id": int|None,  # id no TMDB (None se não enriquecido)
    "media_type": str,    # "movie" | "tv" | None
    "genres": [str],      # nomes de gênero em pt-BR
    "overview": str,      # sinopse
    "poster": str|None,   # url do pôster
    "trailer_url": str|None,
    "providers": [ {"name": str, "logo": str} ],
    "enriched": bool      # True quando já buscou no TMDB
}
"""

import json
import os
import uuid

from . import paths

DATA_DIR = paths.data_dir()
MOVIES_FILE = os.path.join(DATA_DIR, "movies.json")
SEED_FILE = paths.resource_path("data", "filmes_iniciais.txt")


def _new_item(title):
    return {
        "id": uuid.uuid4().hex[:12],
        "title": title.strip(),
        "tmdb_id": None,
        "media_type": None,
        "genres": [],
        "overview": "",
        "poster": None,
        "trailer_url": None,
        "providers": [],
        "enriched": False,
        "watched": False,
    }


# --------------------------------------------------------------------------- #
# Lista inicial
# --------------------------------------------------------------------------- #
def seed_from_file():
    """Cria itens a partir de filmes_iniciais.txt (um título por linha)."""
    if not os.path.exists(SEED_FILE):
        return []
    with open(SEED_FILE, "r", encoding="utf-8") as fh:
        titles = [line.strip() for line in fh if line.strip()]
    # Remove duplicatas preservando ordem.
    seen = set()
    items = []
    for t in titles:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            items.append(_new_item(t))
    return items


# --------------------------------------------------------------------------- #
# Persistência
# --------------------------------------------------------------------------- #
def load():
    """Carrega a lista; na primeira vez, semeia a partir do arquivo inicial."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MOVIES_FILE):
        items = seed_from_file()
        save(items)
        return items
    with open(MOVIES_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(items):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MOVIES_FILE, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=2)


def add(title):
    items = load()
    item = _new_item(title)
    items.append(item)
    save(items)
    return item


def remove(item_id):
    items = [it for it in load() if it["id"] != item_id]
    save(items)
    return items


def update(item_id, **fields):
    items = load()
    for it in items:
        if it["id"] == item_id:
            it.update(fields)
            break
    save(items)
    return items
