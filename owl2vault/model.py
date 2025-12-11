"""Intermediate model for OWL to LinkML/Obsidian conversion."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OEnumValue:
    """Single permissible value for an enumeration."""

    iri: str
    code: str
    label: Optional[str] = None
    description: Optional[str] = None


@dataclass
class OEnumeration:
    """Enumeration definition derived from owl:oneOf."""

    iri: str
    label: str
    description: Optional[str]
    values: List[OEnumValue] = field(default_factory=list)


@dataclass
class OProperty:
    """Property definition for object or annotation properties."""

    iri: str
    label: str
    description: Optional[str]
    domains: List[str] = field(default_factory=list)
    ranges: List[str] = field(default_factory=list)
    is_annotation: bool = False
    inverse_iris: List[str] = field(default_factory=list)
    annotations: Dict[str, List[tuple[str, bool]]] = field(default_factory=dict)


@dataclass
class OSlot:
    """Slot/property definition attached to a class."""

    iri: str
    name: str
    description: Optional[str]
    range_iri: str
    range_label: str
    is_object: bool
    min_card: Optional[int] = None
    max_card: Optional[int] = None


@dataclass
class OClass:
    """Class definition."""

    iri: str
    label: str
    description: Optional[str]
    super_iris: List[str] = field(default_factory=list)
    slots: List[OSlot] = field(default_factory=list)
    annotations: Dict[str, List[tuple[str, bool]]] = field(default_factory=dict)


@dataclass
class ODatatype:
    """Datatype definition for primitive types."""

    iri: str
    label: str
    base_iri: str
    description: Optional[str]
    pattern: Optional[str] = None


@dataclass
class OModel:
    """Container for ontology content."""

    ontology_iri: Optional[str]
    prefixes: Dict[str, str] = field(default_factory=dict)
    classes: Dict[str, OClass] = field(default_factory=dict)
    enums: Dict[str, OEnumeration] = field(default_factory=dict)
    datatypes: Dict[str, ODatatype] = field(default_factory=dict)
    properties: Dict[str, OProperty] = field(default_factory=dict)


__all__ = [
    "OEnumValue",
    "OEnumeration",
    "OProperty",
    "OSlot",
    "OClass",
    "ODatatype",
    "OModel",
]
