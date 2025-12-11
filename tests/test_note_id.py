from __future__ import annotations

import re

from owl2vault.note_id import iri_to_note_id


def test_same_iri_same_id() -> None:
    iri = "http://example.org/Thing#A"
    assert iri_to_note_id(iri) == iri_to_note_id(iri)


def test_different_namespaces_yield_different_ids() -> None:
    iri1 = "http://example.org/ns1#Item"
    iri2 = "http://example.org/ns2#Item"
    assert iri_to_note_id(iri1) != iri_to_note_id(iri2)


def test_output_characters() -> None:
    iri = "http://example.org/some path/Item#Fragment"
    note_id = iri_to_note_id(iri)
    assert re.fullmatch(r"[A-Za-z0-9_]+__[0-9a-f]+", note_id)
