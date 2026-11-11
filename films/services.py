"""
films/services.py

Camada de integração com a TMDB (The Movie Database), substituindo o
antigo `services/film-service`. Todas as chamadas passam por cache em
memória (django.core.cache) para reduzir requisições repetidas, do
mesmo jeito que o serviço original usava Redis.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg
from django.db.models import Count
from django.utils import timezone

from posts.models import Post
from ratings.models import Rating

logger = logging.getLogger(__name__)

TMDB_BASE = settings.TMDB_BASE_URL
LANG = settings.TMDB_LANGUAGE
CACHE_TTL = settings.TMDB_CACHE_TTL

PLATFORMS = {
    8: {
        "name": "Netflix",
        "emoji": "🔴",
        "web": lambda i: f"https://www.netflix.com/search?q={i}",
    },
    119: {
        "name": "Prime Video",
        "emoji": "🔵",
        "web": lambda i: f"https://www.primevideo.com/search?phrase={i}",
    },
    337: {
        "name": "Disney+",
        "emoji": "🟦",
        "web": lambda i: f"https://www.disneyplus.com/search/{i}",
    },
    1899: {
        "name": "Max",
        "emoji": "🟣",
        "web": lambda i: f"https://play.max.com/search?q={i}",
    },
    531: {
        "name": "Paramount+",
        "emoji": "⭐",
        "web": lambda i: f"https://www.paramountplus.com/search/{i}",
    },
    350: {
        "name": "Apple TV+",
        "emoji": "⬛",
        "web": lambda i: f"https://tv.apple.com/search?term={i}",
    },
    619: {"name": "Star+", "emoji": "⚡", "web": lambda i: "https://www.starplus.com"},
    167: {
        "name": "Mubi",
        "emoji": "🎭",
        "web": lambda i: f"https://mubi.com/films/{i}",
    },
}


class TMDBError(Exception):
    pass


def _tmdb_get(path: str, params: dict | None = None) -> dict:
    params = params or {}
    url = f"{TMDB_BASE}{path}"
    query = {"api_key": settings.TMDB_API_KEY, "language": LANG, **params}
    try:
        res = requests.get(url, params=query, timeout=8)
    except requests.RequestException as exc:
        raise TMDBError(str(exc)) from exc
    if not res.ok:
        raise TMDBError(f"TMDB {res.status_code}: {path}")
    return res.json()


def _cached(key: str, ttl: int, fn):
    hit = cache.get(key)
    if hit is not None:
        return hit
    data = fn()
    cache.set(key, data, ttl)
    return data


def _poster(path, size="w500"):
    return f"https://image.tmdb.org/t/p/{size}{path}" if path else None


def _backdrop(path, size="w780"):
    return f"https://image.tmdb.org/t/p/{size}{path}" if path else None


def search(query: str, media_type: str = "multi") -> list[dict]:
    cache_key = f"search:{media_type}:{query.lower()}"

    def fetch():
        data = _tmdb_get(
            f"/search/{media_type}",
            {"query": query, "include_adult": "false"},
        )
        results = []
        for m in (data.get("results") or [])[:15]:
            is_tv = m.get("media_type") == "tv" or media_type == "tv"
            title = m.get("title") or m.get("name")
            if not title:
                continue
            results.append(
                {
                    "tmdb_id": m["id"],
                    "media_type": "tv" if is_tv else "movie",
                    "title": title,
                    "year": (m.get("release_date") or m.get("first_air_date") or "")[
                        :4
                    ],
                    "poster_url": _poster(m.get("poster_path")),
                    "rating": m.get("vote_average"),
                    "overview": m.get("overview"),
                },
            )
        return results

    return _cached(cache_key, 60 * 20, fetch)


def get_trailer(media_type: str, tmdb_id: int) -> dict | None:
    try:
        pt = _tmdb_get(f"/{media_type}/{tmdb_id}/videos")
        en = _tmdb_get(f"/{media_type}/{tmdb_id}/videos", {"language": "en-US"})
    except TMDBError:
        return None
    all_videos = (pt.get("results") or []) + (en.get("results") or [])
    trailer = (
        next(
            (
                v
                for v in all_videos
                if v.get("site") == "YouTube" and v.get("type") == "Trailer"
            ),
            None,
        )
        or next(
            (
                v
                for v in all_videos
                if v.get("site") == "YouTube" and v.get("type") == "Teaser"
            ),
            None,
        )
        or next((v for v in all_videos if v.get("site") == "YouTube"), None)
    )
    if not trailer:
        return None
    # autoplay=1 + mute=1: o usuário já clicou em ▶, então o vídeo começa direto
    # (navegadores só permitem autoplay sem som). Sem enablejsapi: nenhum JS
    # controla o player, e esse modo exigiria também o parâmetro `origin`.
    return {
        "key": trailer["key"],
        "url": f"https://www.youtube.com/embed/{trailer['key']}?rel=0&autoplay=1&mute=1",
    }


def _build_streaming(br_providers: dict, tmdb_id: int) -> dict:
    def to_link(kind):
        def inner(p):
            info = PLATFORMS.get(p.get("provider_id"))
            if not info:
                return None
            return {
                "provider_id": p["provider_id"],
                "name": info["name"],
                "emoji": info["emoji"],
                "kind": kind,
                "logo_url": _poster(p.get("logo_path"), "original"),
                "web_link": info["web"](tmdb_id),
            }

        return inner

    return {
        "stream": [
            x for x in map(to_link("stream"), br_providers.get("flatrate", [])) if x
        ],
        "rent": [x for x in map(to_link("rent"), br_providers.get("rent", [])) if x],
        "buy": [x for x in map(to_link("buy"), br_providers.get("buy", [])) if x],
    }


def get_detail(
    media_type: str,
    tmdb_id: int,
    request_user_id: int | None = None,
) -> dict:
    media_type = "tv" if media_type == "tv" else "movie"
    cache_key = f"film:{media_type}:{tmdb_id}"

    def fetch():
        details = _tmdb_get(f"/{media_type}/{tmdb_id}")
        credits_data = _tmdb_get(f"/{media_type}/{tmdb_id}/credits")
        providers = _tmdb_get(f"/{media_type}/{tmdb_id}/watch/providers")
        trailer = get_trailer(media_type, tmdb_id)
        br_providers = (providers.get("results") or {}).get("BR", {})
        is_tv = media_type == "tv"

        return {
            "tmdb_id": details["id"],
            "media_type": media_type,
            "title": details.get("title") or details.get("name"),
            "tagline": details.get("tagline") or "",
            "overview": details.get("overview"),
            "poster_url": _poster(details.get("poster_path")),
            "backdrop_url": _backdrop(details.get("backdrop_path"), "original"),
            "rating": details.get("vote_average"),
            "vote_count": details.get("vote_count"),
            "runtime": (details.get("episode_run_time") or [None])[0]
            if is_tv
            else details.get("runtime"),
            "release_date": details.get("release_date")
            or details.get("first_air_date"),
            "genres": [g["name"] for g in details.get("genres", [])],
            "seasons": details.get("number_of_seasons") if is_tv else None,
            "trailer": trailer,
            "cast": [
                {
                    "name": a["name"],
                    "character": a.get("character"),
                    "photo_url": _poster(a.get("profile_path"), "w185"),
                }
                for a in (credits_data.get("cast") or [])[:12]
            ],
            "directors": [
                c["name"]
                for c in (credits_data.get("crew") or [])
                if c.get("job") == "Director"
            ][:3],
            "streaming": _build_streaming(br_providers, tmdb_id),
        }

    return _cached(cache_key, CACHE_TTL, fetch)


def get_streaming(media_type: str, tmdb_id: int) -> dict:
    media_type = "tv" if media_type == "tv" else "movie"
    cache_key = f"streaming:{media_type}:{tmdb_id}"

    def fetch():
        providers = _tmdb_get(f"/{media_type}/{tmdb_id}/watch/providers")
        br = (providers.get("results") or {}).get("BR", {})
        return _build_streaming(br, tmdb_id)

    return _cached(cache_key, 60 * 60 * 12, fetch)


def _to_rank_item(m: dict, index: int, override_type: str | None = None) -> dict:
    is_tv = override_type == "tv" or m.get("media_type") == "tv"
    return {
        "rank": index + 1,
        "tmdb_id": m["id"],
        "media_type": "tv" if is_tv else "movie",
        "title": m.get("title") or m.get("name"),
        "overview": m.get("overview") or "",
        "poster_url": _poster(m.get("poster_path")),
        "backdrop_url": _backdrop(m.get("backdrop_path")),
        "rating": round(m.get("vote_average") or 0, 1),
        "year": (m.get("release_date") or m.get("first_air_date") or "")[:4],
        "source": "tmdb",
    }


def ranking_movies() -> list[dict]:
    def fetch():
        data = _tmdb_get("/trending/movie/day", {"region": "BR"})
        return [
            _to_rank_item(m, i, "movie")
            for i, m in enumerate((data.get("results") or [])[:10])
        ]

    return _cached("rankings:movies", 60 * 60 * 3, fetch)


def ranking_series() -> list[dict]:
    def fetch():
        data = _tmdb_get("/trending/tv/day", {"region": "BR"})
        return [
            _to_rank_item(m, i, "tv")
            for i, m in enumerate((data.get("results") or [])[:10])
        ]

    return _cached("rankings:series", 60 * 60 * 3, fetch)


def ranking_world() -> list[dict]:
    def fetch():
        data = _tmdb_get("/trending/all/day")
        items = [
            m
            for m in (data.get("results") or [])
            if m.get("media_type") in ("movie", "tv")
        ][:10]
        return [_to_rank_item(m, i, None) for i, m in enumerate(items)]

    return _cached("rankings:world", 60 * 60 * 3, fetch)


def ranking_upcoming() -> list[dict]:
    def fetch():
        today = timezone.localdate()
        future = today + timedelta(days=60)
        data = _tmdb_get(
            "/discover/movie",
            {
                "region": "BR",
                "release_date.gte": today.isoformat(),
                "release_date.lte": future.isoformat(),
                "sort_by": "popularity.desc",
                "with_release_type": "3|2",
            },
        )
        items = [m for m in (data.get("results") or []) if m.get("poster_path")][:10]
        if not items:
            fallback = _tmdb_get("/movie/upcoming", {"region": "BR"})
            items = [
                m for m in (fallback.get("results") or []) if m.get("poster_path")
            ][:10]
        ranked = sorted(items, key=lambda m: m.get("release_date") or "9999-99-99")
        result = []
        for i, m in enumerate(ranked):
            item = _to_rank_item(m, i, "movie")
            item["release_date"] = m.get("release_date")
            result.append(item)
        return result

    return _cached("rankings:upcoming", 60 * 60 * 6, fetch)


def ranking_app() -> list[dict]:
    """Top 10 mais indicados dentro do próprio CineClub (dados internos)."""

    def fetch():
        qs = (
            Post.objects.values("tmdb_id", "media_type", "title", "poster_url")
            .annotate(total_posts=Count("id"))
            .order_by("-total_posts")[:10]
        )
        rows = list(qs)
        if not rows:
            data = _tmdb_get("/trending/all/day")
            items = [
                m
                for m in (data.get("results") or [])
                if m.get("media_type") in ("movie", "tv")
            ][:10]
            return [
                {**_to_rank_item(m, i, None), "total_posts": 0}
                for i, m in enumerate(items)
            ]

        return [
            {
                "rank": i + 1,
                "tmdb_id": r["tmdb_id"],
                "media_type": r["media_type"],
                "title": r["title"],
                "poster_url": r["poster_url"],
                "backdrop_url": None,
                "overview": None,
                "rating": 0,
                "year": None,
                "total_posts": r["total_posts"],
                "source": "app",
            }
            for i, r in enumerate(rows)
        ]

    return _cached("rankings:app", 60 * 15, fetch)


def ranking_rated() -> list[dict]:
    """Top 10 melhor avaliados pela comunidade do CineClub (dados internos)."""

    def fetch():
        rows = list(
            Rating.objects.values("tmdb_id", "media_type")
            .annotate(avg_score=Avg("score"), total_ratings=Count("id"))
            .order_by("-avg_score")[:10],
        )
        if not rows:
            data = _tmdb_get("/movie/top_rated", {"region": "BR"})
            items = (data.get("results") or [])[:10]
            return [
                {**_to_rank_item(m, i, "movie"), "total_ratings": 0}
                for i, m in enumerate(items)
            ]

        result = []
        for i, r in enumerate(rows):
            post = (
                Post.objects.filter(tmdb_id=r["tmdb_id"], media_type=r["media_type"])
                .order_by("-created_at")
                .first()
            )
            result.append(
                {
                    "rank": i + 1,
                    "tmdb_id": r["tmdb_id"],
                    "media_type": r["media_type"],
                    "title": post.title if post else f"#{r['tmdb_id']}",
                    "poster_url": post.poster_url if post else None,
                    "backdrop_url": None,
                    "overview": None,
                    "rating": round(r["avg_score"], 1),
                    "year": None,
                    "total_ratings": r["total_ratings"],
                    "source": "app",
                },
            )
        return result

    return _cached("rankings:rated", 60 * 15, fetch)


RANKINGS = {
    "movies": ("Top 10 Filmes 🇧🇷", ranking_movies),
    "series": ("Top 10 Séries 🇧🇷", ranking_series),
    "world": ("Top 10 Mundo 🌍", ranking_world),
    "upcoming": ("Lançamentos 🚀", ranking_upcoming),
    "app": ("Top 10 CineClub ⭐", ranking_app),
    "rated": ("Top 10 Avaliados 🏆", ranking_rated),
}


def get_ranking(category: str) -> dict:
    if category not in RANKINGS:
        raise ValueError(f"Categoria de ranking inválida: {category}")
    label, fn = RANKINGS[category]
    try:
        items = fn()
    except TMDBError as exc:
        logger.warning("Falha ao buscar ranking %s da TMDB: %s", category, exc)
        items = []
    return {"category": category, "label": label, "items": items}
