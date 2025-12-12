from __future__ import annotations

from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

from owl2vault.linkml_writer import write_linkml_yaml
from owl2vault.loader import load_owl
from owl2vault.obsidian_writer import write_obsidian_vault
from owl2vault.mkdocs_writer import write_mkdocs_docs


def _build_graph() -> Graph:
    g = Graph()
    ex = Namespace("http://example.org/")
    g.bind("ex", ex)

    cls_a = ex.ClassA
    cls_b = ex.ClassB
    g.add((cls_a, RDF.type, OWL.Class))
    g.add((cls_a, RDFS.label, Literal("Class A")))
    g.add((cls_b, RDF.type, OWL.Class))
    g.add((cls_b, RDFS.label, Literal("Class B")))
    g.add((cls_b, RDFS.subClassOf, cls_a))

    prop = ex.hasName
    g.add((prop, RDF.type, OWL.DatatypeProperty))
    restriction = BNode()
    g.add((cls_a, RDFS.subClassOf, restriction))
    g.add((restriction, RDF.type, OWL.Restriction))
    g.add((restriction, OWL.onProperty, prop))
    g.add((restriction, OWL.someValuesFrom, XSD.string))
    g.add((restriction, OWL.minCardinality, Literal(1)))

    ann_prop = ex.note
    g.add((ann_prop, RDF.type, OWL.AnnotationProperty))
    g.add((ann_prop, RDFS.domain, cls_a))
    g.add((ann_prop, RDFS.range, XSD.string))
    g.add((cls_a, ann_prop, Literal("Example note")))

    # Individual (not explicitly typed as NamedIndividual)
    ind = ex.Instance1
    g.add((ind, RDF.type, cls_a))
    g.add((ind, RDFS.label, Literal("Instance 1")))

    color = ex.Color
    g.add((color, RDF.type, OWL.Class))
    g.add((color, RDFS.label, Literal("Color")))
    one_of = BNode()
    members = [ex.Red, ex.Blue]
    Collection(g, one_of, members)
    g.add((color, OWL.oneOf, one_of))
    g.add((ex.Red, RDFS.label, Literal("Red")))
    g.add((ex.Blue, RDFS.label, Literal("Blue")))

    return g


def test_end_to_end(tmp_path: Path) -> None:
    graph = _build_graph()
    owl_file = tmp_path / "schema.owl"
    graph.serialize(destination=str(owl_file), format="turtle")

    model = load_owl(str(owl_file))
    assert model.classes
    assert model.enums

    linkml_path = tmp_path / "schema.yaml"
    write_linkml_yaml(model, str(linkml_path))
    assert linkml_path.exists()

    vault_dir = tmp_path / "vault"
    write_obsidian_vault(model, str(vault_dir))
    assert (vault_dir / "Classes").is_dir()
    assert (vault_dir / "Enums").is_dir()
    assert (vault_dir / "Object_Properties").is_dir()
    assert (vault_dir / "Data_Properties").is_dir()
    assert (vault_dir / "Annotation_Properties").is_dir()
    assert (vault_dir / "Datatypes").is_dir()
    assert (vault_dir / "Individuals").is_dir()
    assert (vault_dir / "00-Index" / "Index.md").exists()

    mkdocs_dir = tmp_path / "mkdocs"
    write_mkdocs_docs(model, str(mkdocs_dir))
    docs_root = mkdocs_dir / "docs"
    assert (docs_root / "index.md").exists()
    assert (mkdocs_dir / "mkdocs.yml").exists()
