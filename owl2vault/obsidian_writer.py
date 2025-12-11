"""Generate an Obsidian vault from the intermediate model."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

from .model import OModel
from .note_id import iri_to_note_id


log = logging.getLogger(__name__)


def _iri_to_curie(iri: str, prefixes: Dict[str, str]) -> Optional[str]:
    best_prefix = None
    best_base = ""
    for prefix, base in prefixes.items():
        if iri.startswith(base) and len(base) > len(best_base):
            best_prefix = prefix
            best_base = base
    if best_prefix is None:
        return None
    suffix = iri[len(best_base) :]
    return f"{best_prefix}:{suffix}"


def _format_cardinality(min_card: Optional[int], max_card: Optional[int]) -> str:
    if min_card is None and max_card is None:
        return ""
    if min_card is not None and max_card is not None and min_card == max_card:
        return str(min_card)
    min_part = "0" if min_card is None else str(min_card)
    max_part = "*" if max_card is None else str(max_card)
    return f"{min_part}..{max_part}"


def _range_display(range_iri: str, range_label: str, class_ids: Dict[str, str], enum_ids: Dict[str, str], prefixes: Dict[str, str]) -> str:
    if range_iri in class_ids:
        return f"[[{class_ids[range_iri]}|{range_label}]]"
    if range_iri in enum_ids:
        return f"[[{enum_ids[range_iri]}|{range_label}]]"
    curie = _iri_to_curie(range_iri, prefixes)
    return curie or range_label


def _annotation_lines(
    annotations: Dict[str, list[tuple[str, bool]]],
    prop_ids: Dict[str, str],
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    prefixes: Dict[str, str],
) -> list[str]:
    lines: list[str] = []
    for pred_iri, values in annotations.items():
        display_pred = _iri_to_curie(pred_iri, prefixes) or pred_iri
        for val, is_iri in values:
            display_val = val
            if is_iri:
                if val in class_ids:
                    display_val = f"[[{class_ids[val]}|{display_val}]]"
                elif val in enum_ids:
                    display_val = f"[[{enum_ids[val]}|{display_val}]]"
                elif val in prop_ids:
                    display_val = f"[[{prop_ids[val]}|{display_val}]]"
                else:
                    curie = _iri_to_curie(val, prefixes)
                    display_val = curie or val
            lines.append(f"- {display_pred}: {display_val}")
    if not lines:
        lines.append("- None")
    return lines


def _write_note(path: Path, front_matter: Dict[str, object], body_lines: list[str]) -> None:
    fm_text = yaml.safe_dump(front_matter, sort_keys=False).rstrip()
    content = "---\n" + fm_text + "\n---\n\n" + "\n".join(body_lines) + "\n"
    path.write_text(content, encoding="utf-8")


def _write_class_notes(om: OModel, base_dir: Path, class_ids: Dict[str, str], enum_ids: Dict[str, str]) -> None:
    class_dir = base_dir / "Classes"
    class_dir.mkdir(parents=True, exist_ok=True)

    for cls in om.classes.values():
        note_id = class_ids[cls.iri]
        log.debug("Writing class note %s -> %s", cls.label, note_id)
        curie = _iri_to_curie(cls.iri, om.prefixes)
        front = {
            "iri": cls.iri,
            "curie": curie,
            "label": cls.label,
            "note_id": note_id,
            "type": "class",
            "tags": ["class"],
        }

        body: list[str] = [f"# {cls.label}", "", "## Summary", f"- Label: {cls.label}", f"- CURIE: {curie or ''}", f"- IRI: {cls.iri}"]
        body.extend(["", "## Superclasses"])
        if cls.super_iris:
            for sup in cls.super_iris:
                sup_label = om.classes.get(sup).label if sup in om.classes else sup
                if sup in class_ids:
                    body.append(f"- [[{class_ids[sup]}|{sup_label}]]")
                else:
                    body.append(f"- {sup_label}")
        else:
            body.append("- None")

        body.extend(["", "## Slots", "| Slot | Range | Card. | Description |", "| --- | --- | --- | --- |"])
        for slot in cls.slots:
            range_disp = _range_display(slot.range_iri, slot.range_label, class_ids, enum_ids, om.prefixes)
            card_disp = _format_cardinality(slot.min_card, slot.max_card)
            body.append(
                f"| {slot.name} | {range_disp} | {card_disp} | {slot.description or ''} |"
            )

        body.extend(["", "## Annotations"])
        body.extend(
            _annotation_lines(
                cls.annotations,
                prop_ids={},
                class_ids=class_ids,
                enum_ids=enum_ids,
                prefixes=om.prefixes,
            )
        )

        _write_note(class_dir / f"{note_id}.md", front, body)


def _write_enum_notes(om: OModel, base_dir: Path, enum_ids: Dict[str, str]) -> None:
    enum_dir = base_dir / "Enums"
    enum_dir.mkdir(parents=True, exist_ok=True)

    for enum in om.enums.values():
        note_id = enum_ids[enum.iri]
        log.debug("Writing enum note %s -> %s", enum.label, note_id)
        curie = _iri_to_curie(enum.iri, om.prefixes)
        front = {
            "iri": enum.iri,
            "curie": curie,
            "label": enum.label,
            "note_id": note_id,
            "type": "enum",
            "tags": ["enum"],
        }

        body: list[str] = [f"# {enum.label}", "", "## Summary", f"- Label: {enum.label}", f"- CURIE: {curie or ''}", f"- IRI: {enum.iri}"]
        body.extend(["", "## Permissible Values", "| Code | Label | Description |", "| --- | --- | --- |"])
        for val in enum.values:
            body.append(
                f"| {val.code} | {val.label or ''} | {val.description or ''} |"
            )

        _write_note(enum_dir / f"{note_id}.md", front, body)


def _write_property_notes(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    prop_ids: Dict[str, str],
) -> None:
    prop_dir = base_dir / "Properties"
    prop_dir.mkdir(parents=True, exist_ok=True)

    for prop in om.properties.values():
        note_id = prop_ids[prop.iri]
        curie = _iri_to_curie(prop.iri, om.prefixes)
        front = {
            "iri": prop.iri,
            "curie": curie,
            "label": prop.label,
            "note_id": note_id,
            "type": "annotation_property" if prop.is_annotation else "property",
            "tags": ["annotation_property" if prop.is_annotation else "property"],
        }

        body: list[str] = [
            f"# {prop.label}",
            "",
            "## Summary",
            f"- Label: {prop.label}",
            f"- CURIE: {curie or ''}",
            f"- IRI: {prop.iri}",
        ]
        body.extend(["", "## Domains"])
        if prop.domains:
            for dom in prop.domains:
                label = om.classes.get(dom).label if dom in om.classes else dom
                if dom in class_ids:
                    body.append(f"- [[{class_ids[dom]}|{label}]]")
                else:
                    body.append(f"- {label}")
        else:
            body.append("- (unspecified)")

        body.extend(["", "## Ranges"])
        if prop.ranges:
            for rng in prop.ranges:
                if rng in class_ids:
                    label = om.classes[rng].label
                    body.append(f"- [[{class_ids[rng]}|{label}]]")
                elif rng in enum_ids:
                    label = om.enums[rng].label
                    body.append(f"- [[{enum_ids[rng]}|{label}]]")
                else:
                    curie_rng = _iri_to_curie(rng, om.prefixes)
                    body.append(f"- {curie_rng or rng}")
        else:
            body.append("- (unspecified)")

        body.extend(["", "## Inverse Properties"])
        if prop.inverse_iris:
            for inv in prop.inverse_iris:
                if inv in prop_ids:
                    label = om.properties[inv].label
                    body.append(f"- [[{prop_ids[inv]}|{label}]]")
                else:
                    body.append(f"- {inv}")
        else:
            body.append("- None")

        body.extend(["", "## Annotations"])
        body.extend(
            _annotation_lines(
                prop.annotations,
                prop_ids=prop_ids,
                class_ids=class_ids,
                enum_ids=enum_ids,
                prefixes=om.prefixes,
            )
        )

        _write_note(prop_dir / f"{note_id}.md", front, body)


def _write_index(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    prop_ids: Dict[str, str],
) -> None:
    index_dir = base_dir / "00-Index"
    index_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# Index", "", "## Classes"]
    if om.classes:
        for cls in sorted(om.classes.values(), key=lambda c: c.label.lower()):
            lines.append(f"- [[{class_ids[cls.iri]}|{cls.label}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Enumerations"])
    if om.enums:
        for enum in sorted(om.enums.values(), key=lambda e: e.label.lower()):
            lines.append(f"- [[{enum_ids[enum.iri]}|{enum.label}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Properties"])
    if om.properties:
        for prop in sorted(om.properties.values(), key=lambda p: p.label.lower()):
            lines.append(f"- [[{prop_ids[prop.iri]}|{prop.label}]]")
    else:
        lines.append("- None")

    _write_note(index_dir / "Index.md", {"type": "index", "label": "Index", "tags": ["index"]}, lines)


def write_obsidian_vault(om: OModel, out_dir: str) -> None:
    """Write an Obsidian-ready vault from the model."""

    base_dir = Path(out_dir)
    log.info(
        "Rendering Obsidian vault to %s (%d classes, %d enums, %d properties)",
        base_dir,
        len(om.classes),
        len(om.enums),
        len(om.properties),
    )
    class_ids = {iri: iri_to_note_id(iri) for iri in om.classes}
    enum_ids = {iri: iri_to_note_id(iri) for iri in om.enums}
    prop_ids = {iri: iri_to_note_id(iri) for iri in om.properties}

    _write_class_notes(om, base_dir, class_ids, enum_ids)
    _write_enum_notes(om, base_dir, enum_ids)
    _write_property_notes(om, base_dir, class_ids, enum_ids, prop_ids)
    _write_index(om, base_dir, class_ids, enum_ids, prop_ids)


__all__ = ["write_obsidian_vault"]
