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


def _range_display(
    range_iri: str,
    range_label: str,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
    prefixes: Dict[str, str],
) -> str:
    if range_iri in class_ids:
        return f"[[{class_ids[range_iri]}|{range_label}]]"
    if range_iri in enum_ids:
        return f"[[{enum_ids[range_iri]}|{range_label}]]"
    if range_iri in datatype_ids:
        return f"[[{datatype_ids[range_iri]}|{range_label}]]"
    if range_iri in individual_ids:
        return f"[[{individual_ids[range_iri]}|{range_label}]]"
    curie = _iri_to_curie(range_iri, prefixes)
    return curie or range_label


def _annotation_lines(
    annotations: Dict[str, list[tuple[str, bool]]],
    prop_ids: Dict[str, str],
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
    label_map: Dict[str, str],
    prefixes: Dict[str, str],
) -> list[str]:
    lines: list[str] = []
    for pred_iri, values in annotations.items():
        display_pred = label_map.get(pred_iri) or _iri_to_curie(pred_iri, prefixes) or pred_iri
        for val, is_iri in values:
            display_val = val
            if is_iri:
                if val in class_ids:
                    display_val = f"[[{class_ids[val]}|{label_map.get(val, display_val)}]]"
                elif val in enum_ids:
                    display_val = f"[[{enum_ids[val]}|{label_map.get(val, display_val)}]]"
                elif val in datatype_ids:
                    display_val = f"[[{datatype_ids[val]}|{label_map.get(val, display_val)}]]"
                elif val in individual_ids:
                    display_val = f"[[{individual_ids[val]}|{label_map.get(val, display_val)}]]"
                elif val in prop_ids:
                    display_val = f"[[{prop_ids[val]}|{label_map.get(val, display_val)}]]"
                else:
                    display_val = label_map.get(val) or _iri_to_curie(val, prefixes) or val
            lines.append(f"- {display_pred}: {display_val}")
    if not lines:
        lines.append("- None")
    return lines


def _write_note(path: Path, front_matter: Dict[str, object], body_lines: list[str]) -> None:
    fm_text = yaml.safe_dump(front_matter, sort_keys=False).rstrip()
    content = "---\n" + fm_text + "\n---\n\n" + "\n".join(body_lines) + "\n"
    path.write_text(content, encoding="utf-8")


def _write_class_notes(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
    prop_ids: Dict[str, str],
    label_map: Dict[str, str],
) -> None:
    class_dir = base_dir / "Classes"
    class_dir.mkdir(parents=True, exist_ok=True)

    for cls in om.classes.values():
        note_id = class_ids[cls.iri]
        log.debug("Writing class note %s -> %s", cls.label, note_id)
        curie = _iri_to_curie(cls.iri, om.prefixes)
        heading = cls.label or cls.iri
        front = {
            "iri": cls.iri,
            "curie": curie,
            "label": cls.label,
            "note_id": note_id,
            "type": "class",
            "tags": ["class"],
        }

        body: list[str] = [
            f"# {heading}",
            "",
            "## Summary",
            f"- Label: {cls.label or cls.iri}",
            f"- CURIE: {curie or ''}",
            f"- IRI: {cls.iri}",
        ]
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

        body.extend(["", "## Properties", "| Property | Range | Card. | Description |", "| --- | --- | --- | --- |"])
        for slot in cls.slots:
            range_disp = _range_display(
                slot.range_iri, slot.range_label, class_ids, enum_ids, datatype_ids, individual_ids, om.prefixes
            )
            card_disp = _format_cardinality(slot.min_card, slot.max_card)
            body.append(
                f"| {slot.name} | {range_disp} | {card_disp} | {slot.description or ''} |"
            )

        body.extend(["", "## Annotations"])
        body.extend(
            _annotation_lines(
                cls.annotations,
                prop_ids=prop_ids,
                class_ids=class_ids,
                enum_ids=enum_ids,
                datatype_ids=datatype_ids,
                individual_ids=individual_ids,
                label_map=label_map,
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
        heading = enum.label or enum.iri
        front = {
            "iri": enum.iri,
            "curie": curie,
            "label": enum.label,
            "note_id": note_id,
            "type": "enum",
            "tags": ["enum"],
        }

        body: list[str] = [
            f"# {heading}",
            "",
            "## Summary",
            f"- Label: {enum.label or enum.iri}",
            f"- CURIE: {curie or ''}",
            f"- IRI: {enum.iri}",
        ]
        body.extend(["", "## Permissible Values", "| Code | Label | Description |", "| --- | --- | --- |"])
        for val in enum.values:
            body.append(
                f"| {val.code} | {val.label or ''} | {val.description or ''} |"
            )

        _write_note(enum_dir / f"{note_id}.md", front, body)


def _write_datatype_notes(om: OModel, base_dir: Path, datatype_ids: Dict[str, str]) -> None:
    dt_dir = base_dir / "Datatypes"
    dt_dir.mkdir(parents=True, exist_ok=True)

    for dt in om.datatypes.values():
        note_id = datatype_ids[dt.iri]
        curie = _iri_to_curie(dt.iri, om.prefixes)
        heading = dt.label or dt.iri
        front = {
            "iri": dt.iri,
            "curie": curie,
            "label": dt.label,
            "note_id": note_id,
            "type": "datatype",
            "tags": ["datatype"],
        }
        body: list[str] = [
            f"# {heading}",
            "",
            "## Summary",
            f"- Label: {dt.label or dt.iri}",
            f"- CURIE: {curie or ''}",
            f"- IRI: {dt.iri}",
            f"- Base: {dt.base_iri}",
        ]
        _write_note(dt_dir / f"{note_id}.md", front, body)


def _write_property_notes(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
    prop_ids: Dict[str, str],
    label_map: Dict[str, str],
) -> None:
    prop_dirs = {
        "object": base_dir / "Object_Properties",
        "data": base_dir / "Data_Properties",
        "annotation": base_dir / "Annotation_Properties",
    }
    for path in prop_dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    for prop in om.properties.values():
        note_id = prop_ids[prop.iri]
        curie = _iri_to_curie(prop.iri, om.prefixes)
        heading = prop.label or prop.iri
        front = {
            "iri": prop.iri,
            "curie": curie,
            "label": prop.label,
            "note_id": note_id,
            "type": f"{prop.kind}_property",
            "tags": [f"{prop.kind}_property"],
        }

        body: list[str] = [
            f"# {heading}",
            "",
            "## Summary",
            f"- Label: {prop.label or prop.iri}",
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
                elif rng in datatype_ids:
                    label = om.datatypes[rng].label
                    body.append(f"- [[{datatype_ids[rng]}|{label}]]")
                elif rng in individual_ids:
                    label = om.individuals[rng].label
                    body.append(f"- [[{individual_ids[rng]}|{label}]]")
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
                datatype_ids=datatype_ids,
                individual_ids=individual_ids,
                label_map=label_map,
                prefixes=om.prefixes,
            )
        )

        _write_note(prop_dirs[prop.kind] / f"{note_id}.md", front, body)


def _write_individual_notes(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
    prop_ids: Dict[str, str],
    label_map: Dict[str, str],
) -> None:
    ind_dir = base_dir / "Individuals"
    ind_dir.mkdir(parents=True, exist_ok=True)

    for ind in om.individuals.values():
        note_id = individual_ids[ind.iri]
        curie = _iri_to_curie(ind.iri, om.prefixes)
        heading = ind.label or ind.iri
        front = {
            "iri": ind.iri,
            "curie": curie,
            "label": ind.label,
            "note_id": note_id,
            "type": "individual",
            "tags": ["individual"],
        }
        body: list[str] = [
            f"# {heading}",
            "",
            "## Summary",
            f"- Label: {ind.label or ind.iri}",
            f"- CURIE: {curie or ''}",
            f"- IRI: {ind.iri}",
        ]
        body.extend(["", "## Types"])
        if ind.types:
            for t in ind.types:
                if t in class_ids:
                    body.append(f"- [[{class_ids[t]}|{om.classes[t].label}]]")
                else:
                    curie_t = _iri_to_curie(t, om.prefixes)
                    body.append(f"- {curie_t or t}")
        else:
            body.append("- None")

        body.extend(["", "## Annotations"])
        body.extend(
            _annotation_lines(
                ind.annotations,
                prop_ids=prop_ids,
                class_ids=class_ids,
                enum_ids=enum_ids,
                datatype_ids=datatype_ids,
                individual_ids=individual_ids,
                label_map=label_map,
                prefixes=om.prefixes,
            )
        )
        _write_note(ind_dir / f"{note_id}.md", front, body)


def _write_index(
    om: OModel,
    base_dir: Path,
    class_ids: Dict[str, str],
    enum_ids: Dict[str, str],
    datatype_ids: Dict[str, str],
    individual_ids: Dict[str, str],
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

    lines.extend(["", "## Object Properties"])
    obj_props = [p for p in om.properties.values() if p.kind == "object"]
    if obj_props:
        for prop in sorted(obj_props, key=lambda p: (p.label or p.iri).lower()):
            lines.append(f"- [[{prop_ids[prop.iri]}|{prop.label or prop.iri}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Data Properties"])
    data_props = [p for p in om.properties.values() if p.kind == "data"]
    if data_props:
        for prop in sorted(data_props, key=lambda p: (p.label or p.iri).lower()):
            lines.append(f"- [[{prop_ids[prop.iri]}|{prop.label or prop.iri}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Annotation Properties"])
    ann_props = [p for p in om.properties.values() if p.kind == "annotation"]
    if ann_props:
        for prop in sorted(ann_props, key=lambda p: (p.label or p.iri).lower()):
            lines.append(f"- [[{prop_ids[prop.iri]}|{prop.label or prop.iri}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Datatypes"])
    if om.datatypes:
        for dt in sorted(om.datatypes.values(), key=lambda d: d.label.lower()):
            lines.append(f"- [[{datatype_ids[dt.iri]}|{dt.label}]]")
    else:
        lines.append("- None")

    lines.extend(["", "## Individuals"])
    if om.individuals:
        for ind in sorted(om.individuals.values(), key=lambda i: (i.label or i.iri).lower()):
            lines.append(f"- [[{individual_ids[ind.iri]}|{ind.label or ind.iri}]]")
    else:
        lines.append("- None")

    _write_note(index_dir / "Index.md", {"type": "index", "label": "Index", "tags": ["index"]}, lines)


def write_obsidian_vault(om: OModel, out_dir: str) -> None:
    """Write an Obsidian-ready vault from the model."""

    base_dir = Path(out_dir)
    log.info(
        "Rendering Obsidian vault to %s (%d classes, %d enums, %d properties, %d datatypes, %d individuals)",
        base_dir,
        len(om.classes),
        len(om.enums),
        len(om.properties),
        len(om.datatypes),
        len(om.individuals),
    )
    class_ids = {iri: iri_to_note_id(iri) for iri in om.classes}
    enum_ids = {iri: iri_to_note_id(iri) for iri in om.enums}
    datatype_ids = {iri: iri_to_note_id(iri) for iri in om.datatypes}
    prop_ids = {iri: iri_to_note_id(iri) for iri in om.properties}
    individual_ids = {iri: iri_to_note_id(iri) for iri in om.individuals}

    label_map: Dict[str, str] = {}
    label_map.update({iri: cls.label or iri for iri, cls in om.classes.items()})
    label_map.update({iri: en.label or iri for iri, en in om.enums.items()})
    label_map.update({iri: prop.label or iri for iri, prop in om.properties.items()})
    label_map.update({iri: dt.label or iri for iri, dt in om.datatypes.items()})
    label_map.update({iri: ind.label or iri for iri, ind in om.individuals.items()})

    _write_class_notes(om, base_dir, class_ids, enum_ids, datatype_ids, individual_ids, prop_ids, label_map)
    _write_enum_notes(om, base_dir, enum_ids)
    _write_property_notes(om, base_dir, class_ids, enum_ids, datatype_ids, individual_ids, prop_ids, label_map)
    _write_datatype_notes(om, base_dir, datatype_ids)
    _write_individual_notes(om, base_dir, class_ids, enum_ids, datatype_ids, individual_ids, prop_ids, label_map)
    _write_index(om, base_dir, class_ids, enum_ids, datatype_ids, individual_ids, prop_ids)


__all__ = ["write_obsidian_vault"]
