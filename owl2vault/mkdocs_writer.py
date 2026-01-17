"""Generate MkDocs-ready markdown from the intermediate model."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

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


def _link(label: str, path: str) -> str:
    return f"[{label}]({path})"


def _annotation_lines(
    annotations: Dict[str, list[tuple[str, bool]]],
    link_for: Dict[str, str],
    label_for: Dict[str, str],
    prefixes: Dict[str, str],
    docs_dir: Path,
    current_dir: Path,
) -> List[str]:
    lines: List[str] = []
    for pred_iri, values in annotations.items():
        pred_label = label_for.get(pred_iri) or _iri_to_curie(pred_iri, prefixes) or pred_iri
        for val, is_iri in values:
            display = val
            if is_iri and val in link_for:
                display = label_for.get(val) or val
                rel = os.path.relpath(docs_dir / link_for[val], start=current_dir)
                display = _link(display, rel)
            elif is_iri:
                display = label_for.get(val) or _iri_to_curie(val, prefixes) or val
            lines.append(f"- {pred_label}: {display}")
    if not lines:
        lines.append("- None")
    return lines


def _write_file(path: Path, heading: str, lines: List[str]) -> None:
    content = "\n".join([f"# {heading}", "", *lines])
    path.write_text(content + "\n", encoding="utf-8")


def _ensure_dirs(base: Path) -> Dict[str, Path]:
    dirs = {
        "classes": base / "classes",
        "enums": base / "enums",
        "object_properties": base / "object_properties",
        "data_properties": base / "data_properties",
        "annotation_properties": base / "annotation_properties",
        "datatypes": base / "datatypes",
        "individuals": base / "individuals",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    return dirs


def write_mkdocs_docs(om: OModel, out_dir: str) -> None:
    """Write MkDocs project with markdown docs for the ontology."""

    base = Path(out_dir)
    docs_dir = base / "docs"
    dirs = _ensure_dirs(docs_dir)

    log.info(
        "Writing MkDocs docs to %s (%d classes, %d enums, %d properties, %d datatypes, %d individuals)",
        base,
        len(om.classes),
        len(om.enums),
        len(om.properties),
        len(om.datatypes),
        len(om.individuals),
    )

    class_ids = {iri: iri_to_note_id(iri) for iri in om.classes}
    enum_ids = {iri: iri_to_note_id(iri) for iri in om.enums}
    prop_ids = {iri: iri_to_note_id(iri) for iri in om.properties}
    datatype_ids = {iri: iri_to_note_id(iri) for iri in om.datatypes}
    individual_ids = {iri: iri_to_note_id(iri) for iri in om.individuals}

    link_map: Dict[str, str] = {}
    link_map.update({iri: f"classes/{nid}.md" for iri, nid in class_ids.items()})
    link_map.update({iri: f"enums/{nid}.md" for iri, nid in enum_ids.items()})
    link_map.update({iri: f"object_properties/{nid}.md" for iri, nid in prop_ids.items() if om.properties[iri].kind == "object"})
    link_map.update({iri: f"data_properties/{nid}.md" for iri, nid in prop_ids.items() if om.properties[iri].kind == "data"})
    link_map.update({iri: f"annotation_properties/{nid}.md" for iri, nid in prop_ids.items() if om.properties[iri].kind == "annotation"})
    link_map.update({iri: f"datatypes/{nid}.md" for iri, nid in datatype_ids.items()})
    link_map.update({iri: f"individuals/{nid}.md" for iri, nid in individual_ids.items()})

    label_map: Dict[str, str] = {}
    label_map.update({iri: cls.label or iri for iri, cls in om.classes.items()})
    label_map.update({iri: en.label or iri for iri, en in om.enums.items()})
    label_map.update({iri: prop.label or iri for iri, prop in om.properties.items()})
    label_map.update({iri: dt.label or iri for iri, dt in om.datatypes.items()})
    label_map.update({iri: ind.label or iri for iri, ind in om.individuals.items()})

    # build subclass and instance lookup
    subclasses: Dict[str, Set[str]] = {iri: set() for iri in om.classes}
    for cls in om.classes.values():
        for sup in cls.super_iris:
            if sup in subclasses:
                subclasses[sup].add(cls.iri)

    class_instances: Dict[str, Set[str]] = {iri: set() for iri in om.classes}
    for ind in om.individuals.values():
        for t in ind.types:
            if t in class_instances:
                class_instances[t].add(ind.iri)

    # Classes
    for cls in om.classes.values():
        heading = cls.label or cls.iri
        lines: List[str] = ["## Summary", f"- Label: {cls.label or cls.iri}", f"- IRI: {cls.iri}"]
        curie = _iri_to_curie(cls.iri, om.prefixes)
        if curie:
            lines.append(f"- CURIE: {curie}")

        lines.extend(["", "## Superclasses"])
        if cls.super_iris:
            for sup in cls.super_iris:
                sup_label = om.classes.get(sup).label if sup in om.classes else sup
                if sup in link_map:
                    rel = os.path.relpath(docs_dir / link_map[sup], start=dirs["classes"])
                    lines.append(f"- {_link(sup_label, rel)}")
                else:
                    lines.append(f"- {sup_label}")
        else:
            lines.append("- None")

        lines.extend(["", "## Subclasses"])
        subs = subclasses.get(cls.iri, set())
        if subs:
            for sub in sorted(subs, key=lambda s: (om.classes[s].label or s).lower()):
                label = om.classes[sub].label
                rel = os.path.relpath(docs_dir / link_map[sub], start=dirs["classes"])
                lines.append(f"- {_link(label, rel)}")
        else:
            lines.append("- None")

        lines.extend(["", "## Properties", "| Property | Range | Card. | Description |", "| --- | --- | --- | --- |"])
        for slot in cls.slots:
            range_label = slot.range_label
            if slot.range_iri in link_map:
                rel = os.path.relpath(docs_dir / link_map[slot.range_iri], start=dirs["classes"])
                range_display = _link(range_label, rel)
            else:
                curie_range = _iri_to_curie(slot.range_iri, om.prefixes)
                range_display = curie_range or range_label
            card_disp = ""
            if slot.min_card is not None or slot.max_card is not None:
                if slot.min_card is not None and slot.max_card is not None and slot.min_card == slot.max_card:
                    card_disp = str(slot.min_card)
                else:
                    min_part = slot.min_card if slot.min_card is not None else 0
                    max_part = slot.max_card if slot.max_card is not None else "*"
                    card_disp = f"{min_part}..{max_part}"
            lines.append(f"| {slot.name} | {range_display} | {card_disp} | {slot.description or ''} |")

        lines.extend(["", "## Equivalent Classes"])
        if cls.equivalent_iris:
            for eq in cls.equivalent_iris:
                label = om.classes.get(eq).label if eq in om.classes else eq
                if eq in link_map:
                    rel = os.path.relpath(docs_dir / link_map[eq], start=dirs["classes"])
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("- None")

        lines.extend(["", "## Disjoint Classes"])
        if cls.disjoint_iris:
            for dj in cls.disjoint_iris:
                label = om.classes.get(dj).label if dj in om.classes else dj
                if dj in link_map:
                    rel = os.path.relpath(docs_dir / link_map[dj], start=dirs["classes"])
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("- None")

        lines.extend(["", "## Annotations"])
        lines.extend(_annotation_lines(cls.annotations, link_map, label_map, om.prefixes, docs_dir, dirs["classes"]))

        lines.extend(["", "## Instances"])
        insts = class_instances.get(cls.iri, set())
        if insts:
            for inst in sorted(insts, key=lambda i: (om.individuals[i].label or i).lower()):
                label = om.individuals[inst].label or inst
                if inst in link_map:
                    rel = os.path.relpath(docs_dir / link_map[inst], start=dirs["classes"])
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("- None")

        _write_file(dirs["classes"] / f"{class_ids[cls.iri]}.md", heading, lines)

    # Enums
    for enum in om.enums.values():
        heading = enum.label or enum.iri
        lines = [
            "## Summary",
            f"- Label: {enum.label or enum.iri}",
            f"- IRI: {enum.iri}",
        ]
        curie = _iri_to_curie(enum.iri, om.prefixes)
        if curie:
            lines.append(f"- CURIE: {curie}")
        lines.extend(["", "## Permissible Values", "| Code | Label | Description |", "| --- | --- | --- |"])
        for val in enum.values:
            lines.append(f"| {val.code} | {val.label or ''} | {val.description or ''} |")
        _write_file(dirs["enums"] / f"{enum_ids[enum.iri]}.md", heading, lines)

    # Datatypes
    for dt in om.datatypes.values():
        heading = dt.label or dt.iri
        lines = [
            "## Summary",
            f"- Label: {dt.label or dt.iri}",
            f"- IRI: {dt.iri}",
            f"- Base: {dt.base_iri}",
        ]
        _write_file(dirs["datatypes"] / f"{datatype_ids[dt.iri]}.md", heading, lines)

    # Properties
    for prop in om.properties.values():
        heading = prop.label or prop.iri
        target_dir = dirs["object_properties"]
        if prop.kind == "data":
            target_dir = dirs["data_properties"]
        elif prop.kind == "annotation":
            target_dir = dirs["annotation_properties"]
        lines = [
            "## Summary",
            f"- Label: {prop.label or prop.iri}",
            f"- IRI: {prop.iri}",
            f"- Kind: {prop.kind}",
        ]
        curie = _iri_to_curie(prop.iri, om.prefixes)
        if curie:
            lines.append(f"- CURIE: {curie}")
        if prop.inverse_iris:
            inv_links = []
            for inv in prop.inverse_iris:
                if inv in link_map:
                    label = om.properties[inv].label or inv
                    rel = os.path.relpath(docs_dir / link_map[inv], start=target_dir)
                    inv_links.append(_link(label, rel))
                else:
                    inv_links.append(inv)
            lines.append("- Inverse: " + ", ".join(inv_links))

        lines.extend(["", "## Domains"])
        if prop.domains:
            for dom in prop.domains:
                label = om.classes.get(dom).label if dom in om.classes else dom
                if dom in link_map:
                    rel = os.path.relpath(docs_dir / link_map[dom], start=target_dir)
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("- (unspecified)")

        lines.extend(["", "## Ranges"])
        if prop.ranges:
            for rng in prop.ranges:
                if rng in om.classes:
                    label = om.classes[rng].label
                elif rng in om.enums:
                    label = om.enums[rng].label
                elif rng in om.datatypes:
                    label = om.datatypes[rng].label
                else:
                    label = rng
                if rng in link_map:
                    rel = os.path.relpath(docs_dir / link_map[rng], start=target_dir)
                    lines.append(f"- {_link(label, rel)}")
                else:
                    curie_rng = _iri_to_curie(rng, om.prefixes)
                    lines.append(f"- {curie_rng or rng}")
        else:
            lines.append("- (unspecified)")

        lines.extend(["", "## Inverse Properties"])
        if prop.inverse_iris:
            for inv in prop.inverse_iris:
                if inv in link_map:
                    label = om.properties[inv].label or inv
                    rel = os.path.relpath(docs_dir / link_map[inv], start=target_dir)
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {inv}")
        else:
            lines.append("- None")

        lines.extend(["", "## Annotations"])
        lines.extend(_annotation_lines(prop.annotations, link_map, label_map, om.prefixes, docs_dir, target_dir))

        lines.extend(["", "## Equivalent Properties"])
        if prop.equivalent_iris:
            for eq in prop.equivalent_iris:
                label = om.properties.get(eq).label if eq in om.properties else eq
                if eq in link_map:
                    rel = os.path.relpath(docs_dir / link_map[eq], start=target_dir)
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {label}")
        else:
            lines.append("- None")

        lines.extend(["", "## Characteristics"])
        if prop.characteristics:
            for ch in prop.characteristics:
                lines.append(f"- {ch}")
        else:
            lines.append("- None")

        target_dir = dirs["object_properties"]
        if prop.kind == "data":
            target_dir = dirs["data_properties"]
        elif prop.kind == "annotation":
            target_dir = dirs["annotation_properties"]
        _write_file(target_dir / f"{prop_ids[prop.iri]}.md", heading, lines)

    # Individuals
    for ind in om.individuals.values():
        heading = ind.label or ind.iri
        lines = [
            "## Summary",
            f"- Label: {ind.label or ind.iri}",
            f"- IRI: {ind.iri}",
        ]
        curie = _iri_to_curie(ind.iri, om.prefixes)
        if curie:
            lines.append(f"- CURIE: {curie}")
        lines.extend(["", "## Types"])
        if ind.types:
            for t in ind.types:
                label = om.classes.get(t).label if t in om.classes else t
                if t in link_map:
                    rel = os.path.relpath(docs_dir / link_map[t], start=dirs["individuals"])
                    lines.append(f"- {_link(label, rel)}")
                else:
                    curie_t = _iri_to_curie(t, om.prefixes)
                    lines.append(f"- {curie_t or t}")
        else:
            lines.append("- None")
        lines.extend(["", "## Annotations"])
        lines.extend(_annotation_lines(ind.annotations, link_map, label_map, om.prefixes, docs_dir, dirs["individuals"]))

        lines.extend(["", "## Same As"])
        if ind.same_as:
            for sa in ind.same_as:
                if sa in link_map:
                    label = om.individuals.get(sa, ind).label or sa
                    rel = os.path.relpath(docs_dir / link_map[sa], start=dirs["individuals"])
                    lines.append(f"- {_link(label, rel)}")
                else:
                    lines.append(f"- {sa}")
        else:
            lines.append("- None")

        _write_file(dirs["individuals"] / f"{individual_ids[ind.iri]}.md", heading, lines)

    # Index
    index_lines: List[str] = ["# Index", "", "## Classes"]
    if om.classes:
        for cls in sorted(om.classes.values(), key=lambda c: (c.label or c.iri).lower()):
            index_lines.append(f"- {_link(cls.label or cls.iri, link_map[cls.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Enumerations"])
    if om.enums:
        for enum in sorted(om.enums.values(), key=lambda e: (e.label or e.iri).lower()):
            index_lines.append(f"- {_link(enum.label or enum.iri, link_map[enum.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Object Properties"])
    obj_props = [p for p in om.properties.values() if p.kind == "object"]
    if obj_props:
        for prop in sorted(obj_props, key=lambda p: (p.label or p.iri).lower()):
            index_lines.append(f"- {_link(prop.label or prop.iri, link_map[prop.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Data Properties"])
    data_props = [p for p in om.properties.values() if p.kind == "data"]
    if data_props:
        for prop in sorted(data_props, key=lambda p: (p.label or p.iri).lower()):
            index_lines.append(f"- {_link(prop.label or prop.iri, link_map[prop.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Annotation Properties"])
    ann_props = [p for p in om.properties.values() if p.kind == "annotation"]
    if ann_props:
        for prop in sorted(ann_props, key=lambda p: (p.label or p.iri).lower()):
            index_lines.append(f"- {_link(prop.label or prop.iri, link_map[prop.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Datatypes"])
    if om.datatypes:
        for dt in sorted(om.datatypes.values(), key=lambda d: (d.label or d.iri).lower()):
            index_lines.append(f"- {_link(dt.label or dt.iri, link_map[dt.iri])}")
    else:
        index_lines.append("- None")

    index_lines.extend(["", "## Individuals"])
    if om.individuals:
        for ind in sorted(om.individuals.values(), key=lambda i: (i.label or i.iri).lower()):
            index_lines.append(f"- {_link(ind.label or ind.iri, link_map[ind.iri])}")
    else:
        index_lines.append("- None")

    (docs_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    # mkdocs.yml
    nav: List[object] = [{"Home": "index.md"}]
    def _nav_section(name: str, items: List[tuple[str, str]]) -> None:
        if not items:
            return
        nav.append({name: [{label: path} for label, path in items]})

    _nav_section("Classes", [(c.label or c.iri, link_map[c.iri]) for c in sorted(om.classes.values(), key=lambda c: (c.label or c.iri).lower())])
    _nav_section("Enumerations", [(e.label or e.iri, link_map[e.iri]) for e in sorted(om.enums.values(), key=lambda e: (e.label or e.iri).lower())])
    _nav_section("Object Properties", [(p.label or p.iri, link_map[p.iri]) for p in sorted(obj_props, key=lambda p: (p.label or p.iri).lower())])
    _nav_section("Data Properties", [(p.label or p.iri, link_map[p.iri]) for p in sorted(data_props, key=lambda p: (p.label or p.iri).lower())])
    _nav_section("Annotation Properties", [(p.label or p.iri, link_map[p.iri]) for p in sorted(ann_props, key=lambda p: (p.label or p.iri).lower())])
    _nav_section("Datatypes", [(d.label or d.iri, link_map[d.iri]) for d in sorted(om.datatypes.values(), key=lambda d: (d.label or d.iri).lower())])
    _nav_section("Individuals", [(i.label or i.iri, link_map[i.iri]) for i in sorted(om.individuals.values(), key=lambda i: (i.label or i.iri).lower())])

    mkdocs_cfg = {
        "site_name": om.ontology_iri or "owl2vault docs",
        "theme": {"name": "material"},
        "plugins": ["graph", "search", "optimize"],
        "nav": nav,
    }
    with open(base / "mkdocs.yml", "w", encoding="utf-8") as fh:
        yaml.safe_dump(mkdocs_cfg, fh, sort_keys=False)


__all__ = ["write_mkdocs_docs"]
