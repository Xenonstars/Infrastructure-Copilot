"""Pure-Python lexical similarity (no external ML deps).

Production swaps this for embeddings + Azure AI Search hybrid retrieval.
For the MVP this gives real, deterministic relevance scoring so RAG and
similar-incident search actually work offline with zero API keys.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or",
    "in", "on", "for", "with", "at", "by", "from", "this", "that", "it",
    "as", "be", "has", "have", "had", "not", "no", "we", "i", "you",
}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in _STOP]


def vectorize(text: str) -> Counter:
    return Counter(tokenize(text))


def cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return round(dot / (na * nb), 4)
