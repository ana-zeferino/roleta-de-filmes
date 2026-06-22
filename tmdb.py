"""Cliente mínimo da API do TMDB (The Movie Database).

Usa a API Key v3 (parâmetro `api_key`) lida do .env. Região fixa: Brasil (BR),
idioma pt-BR. Os resultados são pensados para enriquecer os itens da lista.
"""

import os

import requests
from dotenv import load_dotenv

import paths

# Lê o .env empacotado (dentro do .app) e, se existir, também um na pasta de dados
# do usuário (permite trocar a chave sem reempacotar).
load_dotenv(paths.resource_path(".env"))
load_dotenv(os.path.join(paths.data_dir(), ".env"), override=True)

API_KEY = os.getenv("TMDB_API_KEY", "").strip()
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"
REGION = "BR"
LANG = "pt-BR"

_genre_cache = None


class TMDBError(Exception):
    pass


def is_configured():
    return bool(API_KEY) and API_KEY != "cole_sua_chave_aqui"


def _get(path, **params):
    if not is_configured():
        raise TMDBError("TMDB_API_KEY não configurada. Crie o arquivo .env (veja o README).")
    params["api_key"] = API_KEY
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=15)
    if resp.status_code == 401:
        raise TMDBError("Chave do TMDB inválida. Confira o valor em .env.")
    resp.raise_for_status()
    return resp.json()


def genres():
    """Mapa { genre_id: nome } unindo gêneros de filme e TV (pt-BR)."""
    global _genre_cache
    if _genre_cache is not None:
        return _genre_cache
    mapping = {}
    for kind in ("movie", "tv"):
        data = _get(f"/genre/{kind}/list", language=LANG)
        for g in data.get("genres", []):
            mapping[g["id"]] = g["name"]
    _genre_cache = mapping
    return mapping


def _img(path, size="w500"):
    return f"{IMG_BASE}/{size}{path}" if path else None


def search_candidates(title, limit=8):
    """Lista de candidatos (filme/tv) para o usuário confirmar qual é o certo.

    Ordena por popularidade (desc) para o mais conhecido vir primeiro — evita pegar
    curtas/clipes homônimos.
    """
    data = _get("/search/multi", language=LANG, query=title, include_adult="false")
    results = [
        r for r in data.get("results", [])
        if r.get("media_type") in ("movie", "tv")
    ]
    results.sort(key=lambda r: r.get("popularity", 0), reverse=True)

    out = []
    for r in results[:limit]:
        date = r.get("release_date") or r.get("first_air_date") or ""
        out.append({
            "tmdb_id": r["id"],
            "media_type": r["media_type"],
            "title": r.get("title") or r.get("name") or title,
            "year": date[:4] if date else "",
            "overview": r.get("overview") or "",
            "poster": _img(r.get("poster_path"), "w185"),
            "popularity": r.get("popularity", 0),
        })
    return out


def trailer(media_type, tmdb_id):
    """Retorna a URL de um trailer no YouTube (pt-BR com fallback en-US) ou None."""
    for lang in (LANG, "en-US"):
        try:
            data = _get(f"/{media_type}/{tmdb_id}/videos", language=lang)
        except requests.HTTPError:
            continue
        videos = data.get("results", [])
        # Preferimos type=Trailer; senão Teaser; senão qualquer YouTube.
        for wanted in ("Trailer", "Teaser", None):
            for v in videos:
                if v.get("site") != "YouTube":
                    continue
                if wanted is None or v.get("type") == wanted:
                    return f"https://www.youtube.com/watch?v={v['key']}"
    return None


def providers(media_type, tmdb_id):
    """Provedores de streaming no Brasil (flatrate/rent/buy), sem duplicar."""
    try:
        data = _get(f"/{media_type}/{tmdb_id}/watch/providers")
    except requests.HTTPError:
        return []
    br = data.get("results", {}).get(REGION, {})
    seen = set()
    out = []
    for bucket in ("flatrate", "free", "ads", "rent", "buy"):
        for p in br.get(bucket, []):
            name = p.get("provider_name")
            if name and name not in seen:
                seen.add(name)
                out.append({"name": name, "logo": _img(p.get("logo_path"), "w92")})
    return out


def enrich_by_id(item, media_type, tmdb_id):
    """Preenche o item com os dados de um título específico do TMDB (mutação in-place)."""
    detail = _get(f"/{media_type}/{tmdb_id}", language=LANG)
    item["tmdb_id"] = tmdb_id
    item["media_type"] = media_type
    item["genres"] = [g["name"] for g in detail.get("genres", [])]
    item["overview"] = detail.get("overview") or ""
    item["poster"] = _img(detail.get("poster_path"))
    item["trailer_url"] = trailer(media_type, tmdb_id)
    item["providers"] = providers(media_type, tmdb_id)
    item["enriched"] = True
    return item


def enrich(item):
    """Enriquece um item escolhendo automaticamente o candidato mais popular."""
    candidates = search_candidates(item["title"], limit=10)
    if not candidates:
        item["enriched"] = True  # marca como tentado para não rebuscar sempre
        return item
    best = candidates[0]  # já vem ordenado por popularidade
    return enrich_by_id(item, best["media_type"], best["tmdb_id"])
