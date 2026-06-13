from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import httpx

from app.config import settings
from app.models import (
    UzbKnowledgeHit,
    UzbKnowledgeSyncItem,
    UzbKnowledgeSyncResponse,
)
from app.services.storage_service import read_json, write_json
from app.services.text_normalization_service import (
    best_matching_excerpt,
    score_token_overlap,
    tokenize_text,
)

_CACHE_FILE = "ubz-knowledge-cache.json"


@lru_cache(maxsize=1)
def _load_seed_documents() -> list[dict]:
    path = settings.knowledge_dir / "ubz-documents.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.notion_api_token}",
        "Notion-Version": settings.notion_version,
        "Content-Type": "application/json",
    }


def _normalize_notion_id(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.replace("-", "").strip()
    if len(compact) != 32:
        return value
    return (
        f"{compact[:8]}-{compact[8:12]}-{compact[12:16]}-"
        f"{compact[16:20]}-{compact[20:]}"
    )


def _cache() -> dict[str, dict]:
    payload = read_json(_CACHE_FILE, default={})
    return payload if isinstance(payload, dict) else {}


def _save_cache(payload: dict[str, dict]) -> None:
    write_json(_CACHE_FILE, payload)


def _search_page_id(title: str) -> str | None:
    if not settings.notion_api_token:
        return None

    response = httpx.post(
        "https://api.notion.com/v1/search",
        headers=_headers(),
        json={
            "query": title,
            "filter": {
                "property": "object",
                "value": "page",
            },
            "page_size": 10,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    for item in results:
        title_property = item.get("properties", {}).get("title", {})
        plain_title = "".join(
            segment.get("plain_text", "")
            for segment in title_property.get("title", [])
        )
        if plain_title.lower() == title.lower():
            return _normalize_notion_id(item["id"])
    if results:
        return _normalize_notion_id(results[0]["id"])
    return None


def _extract_block_text(block: dict) -> str:
    block_type = block.get("type")
    if not block_type:
        return ""
    payload = block.get(block_type, {})
    rich_text = payload.get("rich_text", [])
    return " ".join(part.get("plain_text", "") for part in rich_text).strip()


def _fetch_block_children(block_id: str, depth: int = 0, max_depth: int = 1) -> list[str]:
    response = httpx.get(
        f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100",
        headers=_headers(),
        timeout=30.0,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    texts: list[str] = []
    for block in results:
        text = _extract_block_text(block)
        if text:
            texts.append(text)
        if block.get("has_children") and depth < max_depth:
            texts.extend(_fetch_block_children(block["id"], depth + 1, max_depth))
    return texts


def _merged_documents() -> list[dict]:
    cache = _cache()
    documents: list[dict] = []
    for item in _load_seed_documents():
        merged = dict(item)
        cached = cache.get(item["id"], {})
        if cached:
            merged.update(cached)
        documents.append(merged)
    return documents


def list_ubz_documents() -> list[UzbKnowledgeHit]:
    hits: list[UzbKnowledgeHit] = []
    for item in _merged_documents():
        hits.append(
            UzbKnowledgeHit(
                id=item["id"],
                title=item["title"],
                notionPath=item["notionPath"],
                summary=item.get("liveSummary") or item["summary"],
                guidance=item.get("liveGuidance") or item["guidance"],
                themes=item["themes"],
                score=0,
                excerpt=item.get("liveExcerpt"),
                sourceMode=item.get("sourceMode", "seed"),
                notionPageId=item.get("notionPageId"),
                authorityTier=item.get("authorityTier", "ubz_primary"),
            )
        )
    return hits


def search_ubz_knowledge(query: str, limit: int = 3) -> list[UzbKnowledgeHit]:
    query_tokens = {token for token in tokenize_text(query) if len(token) > 2}
    ranked: list[UzbKnowledgeHit] = []

    for item in _merged_documents():
        score = 0
        keywords = {token for token in tokenize_text(" ".join(item.get("keywords", []))) if len(token) > 2}
        themes = {token for token in tokenize_text(" ".join(item.get("themes", []))) if len(token) > 2}
        title_tokens = {token for token in tokenize_text(item["title"]) if len(token) > 2}
        summary_tokens = {
            token
            for token in tokenize_text(item.get("liveSummary") or item["summary"])
            if len(token) > 2
        }
        live_tokens = {
            token for token in tokenize_text(item.get("liveText", "")) if len(token) > 2
        }

        score += score_token_overlap(
            query_tokens, keywords, exact_weight=4, prefix_weight=3
        )
        score += score_token_overlap(
            query_tokens, themes, exact_weight=3, prefix_weight=2
        )
        score += score_token_overlap(
            query_tokens, title_tokens, exact_weight=2, prefix_weight=2
        )
        score += score_token_overlap(
            query_tokens, summary_tokens, exact_weight=1, prefix_weight=1
        )
        score += score_token_overlap(
            query_tokens, live_tokens, exact_weight=2, prefix_weight=2
        )

        if score <= 0:
            continue

        excerpt = best_matching_excerpt(
            query,
            item.get("liveText", ""),
            fallback=item.get("liveExcerpt"),
        )

        ranked.append(
            UzbKnowledgeHit(
                id=item["id"],
                title=item["title"],
                notionPath=item["notionPath"],
                summary=item.get("liveSummary") or item["summary"],
                guidance=item.get("liveGuidance") or item["guidance"],
                themes=item["themes"],
                score=score,
                excerpt=excerpt,
                sourceMode=item.get("sourceMode", "seed"),
                notionPageId=item.get("notionPageId"),
                authorityTier=item.get("authorityTier", "ubz_primary"),
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]


def build_ubz_context(query: str) -> tuple[str, list[UzbKnowledgeHit]]:
    hits = search_ubz_knowledge(query)
    if not hits:
        fallback = (
            "UBZ vrstva zatim doporucuje drzet jednoduchy rytmus, klidny dech a "
            "cist telesne signaly v sirsich souvislostech."
        )
        return fallback, []

    first = hits[0]
    content = f"{first.title}: {first.guidance}"
    if first.summary:
        content += f" Tematicky fokus: {first.summary}"
    if first.excerpt:
        content += f" Notion highlight: {first.excerpt}"
    if len(hits) > 1:
        related = ", ".join(hit.title for hit in hits[1:])
        content += f" Dalsi souvisejici uzly: {related}."
    return content, hits


def sync_ubz_documents_from_notion() -> UzbKnowledgeSyncResponse:
    cache = _cache()
    items: list[UzbKnowledgeSyncItem] = []
    synced_count = 0

    for document in _load_seed_documents():
        current = dict(cache.get(document["id"], {}))
        page_id = _normalize_notion_id(
            current.get("notionPageId") or document.get("notionPageId")
        )
        if not page_id and document.get("notionSearchTitle") and settings.notion_api_token:
            try:
                page_id = _search_page_id(document["notionSearchTitle"])
            except httpx.HTTPError as exc:
                items.append(
                    UzbKnowledgeSyncItem(
                        id=document["id"],
                        title=document["title"],
                        notionPath=document["notionPath"],
                        notionPageId=None,
                        synced=False,
                        sourceMode="seed",
                        authorityTier=document.get("authorityTier", "ubz_primary"),
                        error=str(exc),
                    )
                )
                continue

        if not page_id or not settings.notion_api_token:
            items.append(
                UzbKnowledgeSyncItem(
                    id=document["id"],
                    title=document["title"],
                    notionPath=document["notionPath"],
                    notionPageId=page_id,
                    synced=False,
                    sourceMode="seed",
                    authorityTier=document.get("authorityTier", "ubz_primary"),
                    error="Missing page access or Notion token.",
                )
            )
            continue

        try:
            texts = _fetch_block_children(page_id)
            live_text = " ".join(texts).strip()
            live_excerpt = " ".join(texts[:2]).strip() if texts else None
            current.update(
                {
                    "notionPageId": page_id,
                    "liveText": live_text,
                    "liveExcerpt": live_excerpt,
                    "liveSummary": live_excerpt or document["summary"],
                    "liveGuidance": document["guidance"],
                    "sourceMode": "notion_live",
                    "syncedAt": _now_iso(),
                }
            )
            cache[document["id"]] = current
            synced_count += 1
            items.append(
                UzbKnowledgeSyncItem(
                    id=document["id"],
                    title=document["title"],
                    notionPath=document["notionPath"],
                    notionPageId=page_id,
                    synced=True,
                    sourceMode="notion_live",
                    authorityTier=document.get("authorityTier", "ubz_primary"),
                    excerpt=live_excerpt,
                )
            )
        except httpx.HTTPError as exc:
            items.append(
                UzbKnowledgeSyncItem(
                    id=document["id"],
                    title=document["title"],
                    notionPath=document["notionPath"],
                    notionPageId=page_id,
                    synced=False,
                    sourceMode="seed",
                    authorityTier=document.get("authorityTier", "ubz_primary"),
                    error=str(exc),
                )
            )

    _save_cache(cache)
    return UzbKnowledgeSyncResponse(
        syncedAt=_now_iso(),
        syncedCount=synced_count,
        items=items,
    )
