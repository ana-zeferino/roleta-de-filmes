"""Leitura/gravação da lista de filmes em data/movies.json.

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
import re
import uuid

import paths

DATA_DIR = paths.data_dir()
MOVIES_FILE = os.path.join(DATA_DIR, "movies.json")
RTF_FILE = paths.resource_path("filmes_iniciais.rtf")


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
    }


# --------------------------------------------------------------------------- #
# Parser simples de RTF -> lista de títulos
# --------------------------------------------------------------------------- #
def _rtf_to_titles(rtf_text):
    """Extrai os títulos (uma linha por filme) de um RTF simples do TextEdit."""
    # As linhas de conteúdo terminam com "\" (quebra de parágrafo do RTF).
    # Removemos blocos de cabeçalho {...} e grupos de controle como {\fonttbl ...}.
    text = rtf_text

    # Decodifica caracteres acentuados no formato \'e3 -> ã (cp1252).
    def _hex(match):
        return bytes([int(match.group(1), 16)]).decode("cp1252", errors="replace")

    text = re.sub(r"\\'([0-9a-fA-F]{2})", _hex, text)

    titles = []
    for raw_line in text.split("\\\n"):
        line = raw_line
        # Remove grupos {...} (tabelas de fonte/cor) inteiros.
        line = re.sub(r"\{[^{}]*\}", "", line)
        # Remove comandos de controle do RTF (\f0, \cf0, \pard, \tx566, etc.).
        line = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", line)
        # Remove chaves soltas e símbolos de controle restantes.
        line = line.replace("{", "").replace("}", "").replace("\\", "")
        line = line.strip()
        if line:
            titles.append(line)
    return titles


def seed_from_rtf():
    """Cria itens a partir do RTF, se ele existir."""
    if not os.path.exists(RTF_FILE):
        return []
    with open(RTF_FILE, "r", encoding="utf-8", errors="replace") as fh:
        titles = _rtf_to_titles(fh.read())
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
    """Carrega a lista; na primeira vez, semeia a partir do RTF."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MOVIES_FILE):
        items = seed_from_rtf()
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
