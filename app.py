"""Roleta de Filmes — app local com pywebview.

Janela frameless + transparente, com a roleta circular flutuante.
Toda a comunicação JS -> Python passa pela classe Api (js_api).
"""

import webbrowser
from urllib.parse import quote

import webview

import paths
import store
import tmdb

INDEX = paths.resource_path("web", "index.html")


class Api:
    """Métodos expostos ao front-end via window.pywebview.api.<metodo>()."""

    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    # ----- estado / configuração ----- #
    def tmdb_configured(self):
        return tmdb.is_configured()

    # ----- lista ----- #
    def get_movies(self):
        return store.load()

    def add_movie(self, title):
        title = (title or "").strip()
        if not title:
            return {"ok": False, "error": "Título vazio."}
        item = store.add(title)
        # Enriquece já, para devolver tipo/gênero ao front.
        try:
            tmdb.enrich(item)
            store.update(item["id"], **item)
        except tmdb.TMDBError as exc:
            return {"ok": True, "item": item, "warning": str(exc)}
        except Exception as exc:  # rede etc.
            return {"ok": True, "item": item, "warning": f"Não consegui buscar no TMDB: {exc}"}
        return {"ok": True, "item": item}

    def search_candidates(self, title):
        """Retorna candidatos do TMDB para o usuário confirmar qual é o correto."""
        title = (title or "").strip()
        if not title:
            return {"ok": False, "error": "Título vazio."}
        try:
            return {"ok": True, "candidates": tmdb.search_candidates(title)}
        except tmdb.TMDBError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": f"Não consegui buscar no TMDB: {exc}"}

    def add_movie_choice(self, title, candidate):
        """Adiciona um título já vinculado ao candidato escolhido pelo usuário."""
        title = (title or "").strip()
        if not title:
            return {"ok": False, "error": "Título vazio."}
        item = store.add(title)
        if candidate:
            try:
                tmdb.enrich_by_id(item, candidate["media_type"], candidate["tmdb_id"])
                store.update(item["id"], **item)
            except Exception as exc:
                return {"ok": True, "item": item, "warning": f"Adicionado, mas falhou ao buscar dados: {exc}"}
        return {"ok": True, "item": item}

    def recast_movie(self, item_id, candidate):
        """Corrige um item existente, revinculando ao candidato escolhido."""
        items = store.load()
        for it in items:
            if it["id"] == item_id:
                try:
                    tmdb.enrich_by_id(it, candidate["media_type"], candidate["tmdb_id"])
                except Exception as exc:
                    return {"ok": False, "error": f"Falhou ao buscar dados: {exc}"}
                store.save(items)
                return {"ok": True, "item": it}
        return {"ok": False, "error": "Item não encontrado."}

    def remove_movie(self, item_id):
        store.remove(item_id)
        return {"ok": True}

    def set_media_type(self, item_id, media_type):
        """Correção manual de filme/série."""
        store.update(item_id, media_type=media_type)
        return {"ok": True}

    def set_watched(self, item_id, watched=True):
        """Marca/desmarca como assistido (assistido = fora da roleta)."""
        store.update(item_id, watched=bool(watched))
        return {"ok": True}

    # ----- enriquecimento ----- #
    def enrich_all(self):
        """Completa metadados faltantes de todos os itens. Retorna a lista atualizada."""
        items = store.load()
        if not tmdb.is_configured():
            return {"ok": False, "error": "TMDB_API_KEY não configurada.", "items": items}
        changed = False
        for it in items:
            if not it.get("enriched"):
                try:
                    tmdb.enrich(it)
                    changed = True
                except Exception:
                    continue
        if changed:
            store.save(items)
        return {"ok": True, "items": items}

    def get_details(self, item_id):
        items = store.load()
        for it in items:
            if it["id"] == item_id:
                # Garante enriquecimento sob demanda.
                if not it.get("enriched") and tmdb.is_configured():
                    try:
                        tmdb.enrich(it)
                        store.save(items)
                    except Exception:
                        pass
                return it
        return None

    # ----- ações externas ----- #
    def open_url(self, url):
        if url:
            webbrowser.open(url)
        return {"ok": True}

    def open_stremio(self, item):
        """Abre o Stremio (app) com busca pelo título; fallback para a web."""
        title = (item or {}).get("title", "")
        # Deep link de busca do app Stremio.
        webbrowser.open(f"stremio://search?search={quote(title or '')}")
        return {"ok": True}

    # ----- janela ----- #
    def minimize_app(self):
        if self._window:
            self._window.minimize()
        return {"ok": True}

    def close_app(self):
        if self._window:
            self._window.destroy()
        return {"ok": True}


def main():
    api = Api()
    window = webview.create_window(
        "Roleta de Filmes",
        INDEX,
        js_api=api,
        width=720,
        height=720,
        frameless=True,
        easy_drag=False,
        transparent=True,
        background_color="#000000",
        resizable=True,
        min_size=(560, 560),
    )
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()
