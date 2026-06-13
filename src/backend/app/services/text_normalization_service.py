from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    without_diacritics = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return without_diacritics.lower()


def tokenize_text(text: str) -> set[str]:
    normalized = normalize_text(text)
    return {token for token in re.split(r"[^a-z0-9_]+", normalized) if token}


def score_token_overlap(
    query_tokens: set[str],
    candidate_tokens: set[str],
    *,
    exact_weight: int,
    prefix_weight: int,
    min_prefix_length: int = 4,
) -> int:
    if not query_tokens or not candidate_tokens:
        return 0

    exact_matches = query_tokens & candidate_tokens
    score = len(exact_matches) * exact_weight
    if prefix_weight <= 0:
        return score

    prefix_matches = 0
    for query_token in query_tokens - exact_matches:
        if len(query_token) < min_prefix_length:
            continue
        for candidate_token in candidate_tokens:
            if candidate_token in exact_matches:
                continue
            if len(candidate_token) < min_prefix_length:
                continue
            if query_token.startswith(candidate_token) or candidate_token.startswith(
                query_token
            ):
                prefix_matches += 1
                break

    return score + prefix_matches * prefix_weight


def best_matching_excerpt(query: str, text: str, fallback: str | None = None) -> str | None:
    chunks = [
        chunk.strip()
        for chunk in re.split(r"(?<=[\.\!\?])\s+|\n+", text or "")
        if chunk.strip()
    ]
    if not chunks:
        return fallback

    query_tokens = tokenize_text(query)
    ranked: list[tuple[int, int, str]] = []
    for chunk in chunks:
        chunk_tokens = tokenize_text(chunk)
        score = score_token_overlap(
            query_tokens,
            chunk_tokens,
            exact_weight=3,
            prefix_weight=2,
        )
        if score <= 0:
            continue
        ranked.append((score, len(chunk), chunk))

    if not ranked:
        return fallback or chunks[0]

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]
