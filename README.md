# owl2vault

Generate a LinkML schema and an Obsidian-ready Markdown vault from an OWL ontology.

## Quick start

- On Ubuntu LTS with a managed Python, avoid system-wide `pip` (PEP 668). Use a venv:
  - `sudo apt-get install -y python3-venv python3-pip`
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -e .`
  - Run `owl2vault ...` while the venv is active (or use `.venv/bin/owl2vault`).

## CLI options

- `-i / --input` (required): path to the OWL file to load.
- `--linkml`: path to write the generated LinkML YAML.
- `--vault`: directory to write the Obsidian vault (creates `Classes/`, `Enums/`, `Properties/`, `00-Index/`).
- `--log-level`: `ERROR|WARNING|INFO|DEBUG` (default: `INFO`).

## Usage examples

- Generate LinkML YAML only:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml`
- Generate an Obsidian vault only:
  - `owl2vault -i path/to/schema.owl --vault output/vault`
- Do both with verbose logging:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml --vault output/vault --log-level DEBUG`
- Generate LinkML YAML, then build markdown docs with linkml’s generator:
  - `owl2vault -i path/to/schema.owl --linkml output/schema.yaml`
  - `gen-doc --format markdown --output docs/ output/schema.yaml`

## Outputs

- LinkML: YAML schema with classes, slots, enums, and properties.
- Obsidian vault: per-entity markdown notes under `Classes/`, `Enums/`, `Object_Properties/`, `Data_Properties/`, `Annotation_Properties/`, `Datatypes/`, `Individuals/`, plus `00-Index/Index.md` linking everything. Notes use stable IRI-derived IDs and headings use labels when available (IRI fallback).

## Version

- Current version: 0.1.3
