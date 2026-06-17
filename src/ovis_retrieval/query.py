# ---
# id: MODULE-RETRIEVAL-0004
# title: OVIS Retrieval Query Helpers
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: src/ovis_retrieval/query.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RETRIEVAL-0004.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
"""Dependency-free lexical query helpers."""

from __future__ import annotations

from collections import Counter
import re

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).lower() for match in TOKEN_PATTERN.finditer(text))


def lexical_score(query_text: str, candidate_text: str) -> int:
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return 0

    candidate_counts = Counter(tokenize(candidate_text))
    return sum(candidate_counts[token] for token in query_tokens)
