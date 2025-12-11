"""Helpers for converting IRIs to Obsidian-friendly note identifiers."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse


def iri_to_note_id(iri: str, max_base_len: int = 64, hash_len: int = 8) -> str:
    """Convert an IRI into a stable Obsidian note identifier.

    The identifier uses a readable base derived from the fragment, path segment,
    or netloc and appends a short hash to avoid collisions.
    """

    parsed = urlparse(iri)
    base_candidate = parsed.fragment or (parsed.path.rstrip("/").split("/")[-1] if parsed.path else "")
    if not base_candidate:
        base_candidate = parsed.netloc or iri
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", base_candidate).strip("_")
    if not normalized:
        normalized = "node"
    if max_base_len > 0:
        normalized = normalized[:max_base_len]

    digest = hashlib.sha1(iri.encode("utf-8")).hexdigest()
    hash_part = digest if hash_len <= 0 else digest[:hash_len]
    return f"{normalized}__{hash_part}"


__all__ = ["iri_to_note_id"]
