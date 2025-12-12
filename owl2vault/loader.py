"""OWL loader that builds the intermediate model using rdflib."""
from __future__ import annotations

import logging
from typing import Dict, Optional, Set

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.util import guess_format
from rdflib.namespace import OWL, RDF, RDFS, XSD

from .model import (
    OClass,
    ODatatype,
    OEnumValue,
    OEnumeration,
    OIndividual,
    OModel,
    OProperty,
    OSlot,
)


log = logging.getLogger(__name__)


_XSD_TYPE_INFO: Dict[str, tuple[str, str]] = {
    str(XSD.string): ("string", str(XSD.string)),
    str(XSD.decimal): ("decimal", str(XSD.decimal)),
    str(XSD.boolean): ("boolean", str(XSD.boolean)),
    str(XSD.date): ("date", str(XSD.date)),
    str(XSD.dateTime): ("datetime", str(XSD.dateTime)),
}


def _local_name(iri: URIRef) -> str:
    text = str(iri)
    for sep in ["#", "/"]:
        if sep in text:
            text = text.rsplit(sep, 1)[-1]
    return text or str(iri)


def _label_for(graph: Graph, node) -> str:
    labels = list(graph.objects(node, RDFS.label))
    if labels:
        # Prefer English labels if present
        for l in labels:
            if isinstance(l, Literal) and l.language and l.language.lower().startswith("en"):
                return str(l)
        return str(labels[0])
    if isinstance(node, URIRef):
        return _local_name(node)
    return str(node)


def _comment(graph: Graph, node) -> Optional[str]:
    comment = graph.value(node, RDFS.comment)
    return str(comment) if comment else None


def _collect_annotations(graph: Graph, model: OModel, subject: URIRef) -> Dict[str, list[tuple[str, bool]]]:
    annotations: Dict[str, list[tuple[str, bool]]] = {}
    for pred, obj in graph.predicate_objects(subject):
        if not isinstance(pred, URIRef):
            continue
        pred_iri = str(pred)
        if pred_iri in (str(RDFS.label), str(RDFS.comment)):
            continue
        is_annotation = (
            (pred, RDF.type, OWL.AnnotationProperty) in graph
            or pred_iri in model.properties and model.properties[pred_iri].is_annotation
        )
        if not is_annotation:
            continue
        is_iri = isinstance(obj, URIRef)
        val = str(obj)
        annotations.setdefault(pred_iri, []).append((val, is_iri))
    return annotations


def _int_or_none(value: Optional[Literal]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _sanitize_code(text: str) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_") or "value"


def _extract_enum(graph: Graph, cls: URIRef, one_of) -> OEnumeration:
    enum_label = _label_for(graph, cls)
    desc = _comment(graph, cls)
    values = []
    members = Collection(graph, one_of) if isinstance(one_of, BNode) else []
    for member in members:
        member_label = _label_for(graph, member)
        code = _sanitize_code(member_label or _local_name(member))
        values.append(
            OEnumValue(
                iri=str(member),
                code=code,
                label=member_label,
                description=_comment(graph, member),
            )
        )
    return OEnumeration(iri=str(cls), label=enum_label, description=desc, values=values)


def _ensure_datatype(model: OModel, iri: str) -> None:
    if iri in model.datatypes:
        return
    if iri in _XSD_TYPE_INFO:
        label, base = _XSD_TYPE_INFO[iri]
        model.datatypes[iri] = ODatatype(iri=iri, label=label, base_iri=base, description=None)


def _range_label(model: OModel, graph: Graph, node) -> str:
    iri = str(node)
    if iri in model.classes:
        return model.classes[iri].label
    if iri in model.enums:
        return model.enums[iri].label
    if iri in model.datatypes:
        return model.datatypes[iri].label
    return _label_for(graph, node)


def _collect_properties(graph: Graph, model: OModel) -> None:
    prop_kinds = [
        (OWL.ObjectProperty, "object"),
        (OWL.DatatypeProperty, "data"),
        (OWL.AnnotationProperty, "annotation"),
    ]
    for prop_type, kind in prop_kinds:
        for prop in graph.subjects(RDF.type, prop_type):
            iri = str(prop)
            label = _label_for(graph, prop)
            desc = _comment(graph, prop)
            domains = [str(d) for d in graph.objects(prop, RDFS.domain) if isinstance(d, URIRef)]
            ranges = [str(r) for r in graph.objects(prop, RDFS.range) if isinstance(r, URIRef)]
            for rng in ranges:
                _ensure_datatype(model, rng)
            inverses = {str(inv) for inv in graph.objects(prop, OWL.inverseOf) if isinstance(inv, URIRef)}
            inverses.update({str(s) for s in graph.subjects(OWL.inverseOf, prop) if isinstance(s, URIRef)})
            model.properties[iri] = OProperty(
                iri=iri,
                label=label,
                description=desc,
                domains=domains,
                ranges=ranges,
                kind=kind,
                inverse_iris=sorted(inverses),
                annotations=_collect_annotations(graph, model, prop),
            )


def _is_object_property(graph: Graph, prop: URIRef) -> bool:
    if (prop, RDF.type, OWL.ObjectProperty) in graph:
        return True
    if (prop, RDF.type, OWL.DatatypeProperty) in graph:
        return False
    return True


def _restriction_to_slot(model: OModel, graph: Graph, restriction: BNode) -> Optional[OSlot]:
    if (restriction, RDF.type, OWL.Restriction) not in graph:
        return None
    prop = graph.value(restriction, OWL.onProperty)
    if prop is None:
        return None
    range_node = graph.value(restriction, OWL.allValuesFrom) or graph.value(restriction, OWL.someValuesFrom)
    if range_node is None:
        return None

    min_card = _int_or_none(graph.value(restriction, OWL.minCardinality))
    max_card = _int_or_none(graph.value(restriction, OWL.maxCardinality))
    exact_card = _int_or_none(graph.value(restriction, OWL.cardinality))
    if exact_card is not None:
        min_card = exact_card
        max_card = exact_card

    range_iri = str(range_node)
    _ensure_datatype(model, range_iri)
    is_obj = _is_object_property(graph, prop)
    return OSlot(
        iri=str(prop),
        name=_label_for(graph, prop),
        description=_comment(graph, prop),
        range_iri=range_iri,
        range_label=_range_label(model, graph, range_node),
        is_object=is_obj,
        min_card=min_card,
        max_card=max_card,
    )


def _slot_from_property(model: OModel, graph: Graph, prop: OProperty) -> OSlot:
    if prop.ranges:
        range_iri = prop.ranges[0]
    elif prop.kind == "object":
        range_iri = str(OWL.Thing)
    elif prop.kind == "data":
        range_iri = str(XSD.string)
    else:
        range_iri = str(XSD.string)
    _ensure_datatype(model, range_iri)
    return OSlot(
        iri=prop.iri,
        name=prop.label,
        description=prop.description,
        range_iri=range_iri,
        range_label=_range_label(model, graph, URIRef(range_iri)),
        is_object=prop.kind == "object",
        min_card=None,
        max_card=None,
    )


def load_owl(path: str) -> OModel:
    """Load an OWL file into the intermediate :class:`OModel`."""

    log.info("Parsing OWL file %s", path)
    graph = Graph()
    fmt_candidates = []
    guessed = guess_format(path)
    if guessed:
        fmt_candidates.append(guessed)
    for fmt in ("turtle", "xml"):
        if fmt not in fmt_candidates:
            fmt_candidates.append(fmt)

    last_error: Exception | None = None
    for fmt in fmt_candidates:
        log.debug("Attempting to parse %s as %s", path, fmt)
        try:
            graph.parse(path, format=fmt)
            break
        except Exception as exc:  # pragma: no cover - executed only on parse failures
            log.warning("Failed to parse %s as %s: %s", path, fmt, exc)
            last_error = exc
            graph = Graph()
    else:  # pragma: no cover
        if last_error:
            raise last_error
        raise RuntimeError(f"Unable to parse OWL file: {path}")

    ontology_iri = next((str(s) for s in graph.subjects(RDF.type, OWL.Ontology)), None)
    model = OModel(ontology_iri=ontology_iri)
    model.prefixes = {prefix: str(uri) for prefix, uri in graph.namespace_manager.namespaces()}

    enum_class_iris: Set[str] = set()
    for cls in graph.subjects(RDF.type, OWL.Class):
        one_of = graph.value(cls, OWL.oneOf)
        if one_of:
            enum = _extract_enum(graph, cls, one_of)
            model.enums[enum.iri] = enum
            enum_class_iris.add(str(cls))
    # Also catch any node with owl:oneOf even if not typed as owl:Class
    for cls in graph.subjects(OWL.oneOf, None):
        if isinstance(cls, URIRef) and str(cls) not in enum_class_iris:
            one_of = graph.value(cls, OWL.oneOf)
            if one_of:
                enum = _extract_enum(graph, cls, one_of)
                model.enums[enum.iri] = enum
                enum_class_iris.add(str(cls))

    # Prepopulate datatype map for common XSD entries
    for iri, (label, base) in _XSD_TYPE_INFO.items():
        model.datatypes.setdefault(iri, ODatatype(iri=iri, label=label, base_iri=base, description=None))

    _collect_properties(graph, model)

    for dt in graph.subjects(RDF.type, RDFS.Datatype):
        iri = str(dt)
        if iri in model.datatypes:
            continue
        label = _label_for(graph, dt)
        desc = _comment(graph, dt)
        base_val = graph.value(dt, OWL.onDatatype) or graph.value(dt, RDFS.subClassOf)
        base_iri = str(base_val) if isinstance(base_val, URIRef) else str(XSD.string)
        model.datatypes[iri] = ODatatype(iri=iri, label=label, base_iri=base_iri, description=desc)

    for cls in graph.subjects(RDF.type, OWL.Class):
        cls_iri = str(cls)
        if cls_iri in enum_class_iris:
            continue
        label = _label_for(graph, cls)
        desc = _comment(graph, cls)
        model.classes[cls_iri] = OClass(
            iri=cls_iri,
            label=label,
            description=desc,
            annotations=_collect_annotations(graph, model, cls),
        )

    for cls_iri, oclass in model.classes.items():
        for sup in graph.objects(URIRef(cls_iri), RDFS.subClassOf):
            if isinstance(sup, URIRef):
                oclass.super_iris.append(str(sup))
            elif isinstance(sup, BNode):
                slot = _restriction_to_slot(model, graph, sup)
                if slot:
                    oclass.slots.append(slot)

    for prop in model.properties.values():
        slot = _slot_from_property(model, graph, prop)
        for dom in prop.domains:
            if dom in model.classes:
                cls = model.classes[dom]
                if all(existing.iri != slot.iri for existing in cls.slots):
                    cls.slots.append(slot)

    # Individuals
    individual_nodes: Set[URIRef] = set()
    for subj in graph.subjects(RDF.type, OWL.NamedIndividual):
        if isinstance(subj, URIRef):
            individual_nodes.add(subj)
    for subj, typ in graph.subject_objects(RDF.type):
        if not isinstance(subj, URIRef):
            continue
        if isinstance(typ, URIRef) and typ in model.classes:
            individual_nodes.add(subj)
    for subj in individual_nodes:
        types = [str(t) for t in graph.objects(subj, RDF.type) if isinstance(t, URIRef) and t != OWL.NamedIndividual]
        model.individuals[str(subj)] = OIndividual(
            iri=str(subj),
            label=_label_for(graph, subj),
            description=_comment(graph, subj),
            types=types,
            annotations=_collect_annotations(graph, model, subj),
        )

    log.info(
        "Loaded ontology %s (%d classes, %d enums, %d datatypes)",
        ontology_iri or "<unknown>",
        len(model.classes),
        len(model.enums),
        len(model.datatypes),
    )

    return model


__all__ = ["load_owl"]
