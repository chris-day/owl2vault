"""Convert the intermediate model into a LinkML schema."""
from __future__ import annotations

import logging
from typing import Dict

import yaml

from .model import OModel, OSlot


log = logging.getLogger(__name__)


_LINKML_DATATYPES = {
    "http://www.w3.org/2001/XMLSchema#string": "string",
    "http://www.w3.org/2001/XMLSchema#decimal": "decimal",
    "http://www.w3.org/2001/XMLSchema#boolean": "boolean",
    "http://www.w3.org/2001/XMLSchema#date": "date",
    "http://www.w3.org/2001/XMLSchema#dateTime": "datetime",
}


def _slot_entry(slot: OSlot, om: OModel) -> Dict:
    range_label = _range_for_slot(slot, om)
    entry: Dict[str, object] = {
        "description": slot.description,
        "range": range_label,
        "required": slot.min_card is not None and slot.min_card >= 1,
        "multivalued": slot.max_card is None or slot.max_card > 1,
    }
    if slot.min_card is not None:
        entry["minimum_cardinality"] = slot.min_card
    if slot.max_card is not None:
        entry["maximum_cardinality"] = slot.max_card
    return entry


def _range_for_slot(slot: OSlot, om: OModel) -> str:
    if slot.range_iri in om.classes:
        return om.classes[slot.range_iri].label
    if slot.range_iri in om.enums:
        return om.enums[slot.range_iri].label
    if slot.range_iri in om.datatypes:
        return om.datatypes[slot.range_iri].label
    return slot.range_label


def model_to_linkml(om: OModel) -> Dict:
    """Convert the model to a LinkML schema dictionary."""

    schema: Dict[str, object] = {
        "id": om.ontology_iri or "urn:generated:owl2vault",
        "name": "owl2vault_schema",
        "prefixes": om.prefixes,
        "default_prefix": next(iter(om.prefixes.keys()), "owl2vault"),
        "imports": ["linkml:types"],
        "types": {},
        "enums": {},
        "slots": {},
        "classes": {},
    }

    for dt in om.datatypes.values():
        base = _LINKML_DATATYPES.get(dt.iri, dt.label)
        dt_entry: Dict[str, object] = {
            "uri": dt.iri,
            "base": base,
            "description": dt.description,
        }
        if dt.pattern:
            dt_entry["pattern"] = dt.pattern
        schema["types"][dt.label] = dt_entry

    for enum in om.enums.values():
        enum_entry: Dict[str, object] = {
            "description": enum.description,
            "permissible_values": {},
        }
        for val in enum.values:
            enum_entry["permissible_values"][val.code] = {
                "text": val.label or val.code,
                "description": val.description,
            }
        schema["enums"][enum.label] = enum_entry

    slots: Dict[str, Dict[str, object]] = {}
    for prop in om.properties.values():
        range_iri = prop.ranges[0] if prop.ranges else "http://www.w3.org/2002/07/owl#Thing"
        if range_iri in om.classes:
            range_label = om.classes[range_iri].label
        elif range_iri in om.enums:
            range_label = om.enums[range_iri].label
        elif range_iri in om.datatypes:
            range_label = om.datatypes[range_iri].label
        else:
            range_label = prop.label
        slot_like = OSlot(
            iri=prop.iri,
            name=prop.label,
            description=prop.description,
            range_iri=range_iri,
            range_label=range_label,
            is_object=not prop.is_annotation,
        )
        slots.setdefault(slot_like.name, _slot_entry(slot_like, om))

    for cls in om.classes.values():
        for slot in cls.slots:
            slots.setdefault(slot.name, _slot_entry(slot, om))
    schema["slots"].update(slots)

    for cls in om.classes.values():
        cls_entry: Dict[str, object] = {
            "description": cls.description,
            "slots": [slot.name for slot in cls.slots],
        }
        if cls.super_iris:
            super_iri = cls.super_iris[0]
            if super_iri in om.classes:
                cls_entry["is_a"] = om.classes[super_iri].label
        schema["classes"][cls.label] = cls_entry

    return schema


def write_linkml_yaml(om: OModel, path: str) -> None:
    """Serialize the LinkML schema to YAML."""

    data = model_to_linkml(om)
    log.info("Writing LinkML schema with %d classes to %s", len(om.classes), path)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


__all__ = ["model_to_linkml", "write_linkml_yaml"]
