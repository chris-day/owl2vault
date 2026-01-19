from __future__ import annotations

from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD
import yaml

from owl2vault.linkml_writer import write_linkml_yaml
from owl2vault.loader import load_owl
from owl2vault.obsidian_writer import write_obsidian_vault
from owl2vault.mkdocs_writer import write_mkdocs_docs
from owl2vault.docsify_writer import write_docsify_docs
from owl2vault.hugo_writer import write_hugo_site


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
    g.add((prop, RDFS.label, Literal("Has Name")))
    restriction = BNode()
    g.add((cls_a, RDFS.subClassOf, restriction))
    g.add((restriction, RDF.type, OWL.Restriction))
    g.add((restriction, OWL.onProperty, prop))
    g.add((restriction, OWL.someValuesFrom, XSD.string))
    g.add((restriction, OWL.minCardinality, Literal(1)))

    ann_prop = ex.note
    g.add((ann_prop, RDF.type, OWL.AnnotationProperty))
    g.add((ann_prop, RDFS.label, Literal("Note")))
    g.add((ann_prop, RDFS.domain, cls_a))
    g.add((ann_prop, RDFS.range, XSD.string))
    g.add((cls_a, ann_prop, Literal("Example note")))
    g.add((cls_a, ann_prop, prop))

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
    class_a_note = ""
    for note in (vault_dir / "Classes").glob("*.md"):
        text = note.read_text()
        if "# Class A" in text:
            class_a_note = text
            break
    assert class_a_note
    assert "## Properties" in class_a_note
    assert "- Note: Example note" in class_a_note
    assert "Note: [[hasName" in class_a_note and "Has Name]]" in class_a_note

    mkdocs_dir = tmp_path / "mkdocs"
    write_mkdocs_docs(model, str(mkdocs_dir))
    docs_root = mkdocs_dir / "docs"
    assert (docs_root / "index.md").exists()
    assert (mkdocs_dir / "mkdocs.yml").exists()
    cfg = yaml.safe_load((mkdocs_dir / "mkdocs.yml").read_text())
    assert cfg.get("theme", {}).get("name") == "material"
    assert cfg.get("plugins") == ["graph", "search", "optimize"]
    class_docs = list((docs_root / "classes").glob("*.md"))
    content = ""
    for doc in class_docs:
        text = doc.read_text()
        if text.startswith("# Class A"):
            content = text
            break
    assert content
    assert "## Properties" in content
    assert "- Note: [Has Name]" in content

    docsify_dir = tmp_path / "docsify"
    write_docsify_docs(model, str(docsify_dir))
    docsify_docs = docsify_dir / "docs"
    assert (docsify_dir / "index.html").exists()
    assert (docsify_docs / "README.md").exists()
    assert (docsify_docs / "_sidebar.md").exists()

    hugo_dir = tmp_path / "hugo"
    write_hugo_site(model, str(hugo_dir))
    hugo_content = hugo_dir / "content"
    assert (hugo_dir / "hugo.toml").exists()
    assert (hugo_content / "_index.md").exists()
    assert "{{% relref" in (hugo_content / "_index.md").read_text()
    assert (hugo_content / "classes" / "_index.md").exists()
    classes_index = (hugo_content / "classes" / "_index.md").read_text()
    assert 'type = "chapter"' in classes_index
    assert not classes_index.lstrip().startswith("# ")
    class_page = next((hugo_content / "classes").glob("*.md"))
    class_text = class_page.read_text()
    assert 'type = "default"' in class_text
    assert not class_text.lstrip().startswith("# ")
