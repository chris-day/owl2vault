# owl2vault

`owl2vault` converts OWL ontologies into multiple documentation and modeling outputs:

- LinkML schema YAML
- Obsidian vault markdown
- MkDocs markdown project
- Docsify project
- Hugo project

## What It Does

The tool parses an OWL ontology into a normalized in-memory model (`OModel`) and then renders that model into different output formats.

Core stages:

1. Load ontology with `rdflib`.
2. Build `OModel` entities (classes, properties, enums, datatypes, individuals).
3. Render selected output(s) via writer modules.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

owl2vault -i path/to/schema.owl \
  --linkml out/schema.yaml \
  --vault out/vault \
  --mkdocs out/mkdocs \
  --docsify out/docsify \
  --hugo out/hugo
```

See [CLI Reference](cli.md) and [Examples](examples.md) for complete command patterns.

## Documentation Map

- [Architecture](architecture.md)
- [Data Model](model.md)
- [CLI Reference](cli.md)
- [Examples](examples.md)
- [SPARQL Extraction Templates](sparql.md)
- [Output Generators](generators.md)
- [Development](development.md)
