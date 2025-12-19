# owl2vault

Generate a LinkML schema, an Obsidian-ready Markdown vault and MkDocs from an OWL ontology.

## Quick start

- On Ubuntu LTS with a managed Python, avoid system-wide `pip` (PEP 668). Use a venv:
  - `sudo apt-get install -y python3-venv python3-pip`
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -e .`
  - Run `owl2vault ...` while the venv is active (or use `.venv/bin/owl2vault`).

## CLI options

- `-i / --input`: path to the OWL file to load.
- `--url`: URL to download an OWL file to use as input.
- `--linkml`: path to write the generated LinkML YAML.
- `--vault`: directory to write the Obsidian vault (creates `Classes/`, `Enums/`, `Object_Properties/`, `Data_Properties/`, `Annotation_Properties/`, `00-Index/`).
- `--mkdocs`: directory to write a MkDocs project (`mkdocs.yml` + `docs/` with markdown).
- `--log-level`: `ERROR|WARNING|INFO|DEBUG` (default: `INFO`).

## Usage examples

- Generate LinkML YAML only:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml`
- Generate an Obsidian vault only:
  - `owl2vault -i path/to/schema.owl --vault output/vault`
- Generate MkDocs docs only:
  - `owl2vault -i path/to/schema.owl --mkdocs output/mkdocs`
- Pull OWL from a URL then generate everything:
  - `owl2vault --url https://ekgf.github.io/dprod/dprod.ttl --linkml output/schema.yaml --vault output/vault --mkdocs output/mkdocs`
- Build and serve MkDocs docs after generation:
  - `cd output/mkdocs && mkdocs build && mkdocs serve` (serve at http://127.0.0.1:8000 by default)
- MkDocs dependencies for theming/graphs:
  - `pip install mkdocs-material`
  - `pip install "mkdocs-material[imaging]"`
  - `pip install mkdocs-network-graph-plugin`
- Do both with verbose logging:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml --vault output/vault --log-level DEBUG`
- Generate LinkML YAML, then build markdown docs with linkml’s generator:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml`
  - `gen-doc --format markdown --output docs/ output/schema.yaml`

## Outputs

- LinkML: YAML schema with classes, slots, enums, and properties.
- Obsidian vault: per-entity markdown notes under `Classes/`, `Enums/`, `Object_Properties/`, `Data_Properties/`, `Annotation_Properties/`, `Datatypes/`, `Individuals/`, plus `00-Index/Index.md` linking everything. Notes use stable IRI-derived IDs and headings use labels when available (IRI fallback). Class sections list “Properties” (not “Slots”), and annotation predicates/IRI-valued annotations display resolved labels where available.
- MkDocs: `mkdocs.yml` (uses the `material` theme with `graph`, `search`, and `optimize` plugins) plus `docs/` with markdown grouped into `classes/`, `enums/`, `object_properties/`, `data_properties/`, `annotation_properties/`, `datatypes/`, `individuals/`, and an `index.md` linking everything. Use `mkdocs build` to generate a site. Annotation predicates/IRI-valued annotations are rendered with their labels when present.

## Version

- Current version: 0.1.8
