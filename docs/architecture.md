# Architecture

## High-Level Flow

```mermaid
flowchart LR
  A[OWL File or URL] --> B[cli.py]
  B --> C[loader.py\nload_owl]
  C --> D[OModel]
  D --> E[linkml_writer.py]
  D --> F[obsidian_writer.py]
  D --> G[mkdocs_writer.py]
  D --> H[docsify_writer.py]
  D --> I[hugo_writer.py]
  E --> E1[LinkML YAML]
  F --> F1[Obsidian Vault]
  G --> G1[MkDocs Project]
  H --> H1[Docsify Project]
  I --> I1[Hugo Project]
```

## Module Responsibilities

- `owl2vault/cli.py`: argument parsing, URL download support, orchestration.
- `owl2vault/loader.py`: OWL parsing and extraction into `OModel`.
- `owl2vault/model.py`: dataclasses used by all renderers.
- `owl2vault/linkml_writer.py`: LinkML schema generation.
- `owl2vault/obsidian_writer.py`: Obsidian markdown + front matter generation.
- `owl2vault/mkdocs_writer.py`: MkDocs markdown content + `mkdocs.yml` in output targets.
- `owl2vault/docsify_writer.py`: Docsify wrapper around shared markdown generation.
- `owl2vault/hugo_writer.py`: Hugo content + `hugo.toml`, relref rewriting, front matter.

## Loader Extraction Pipeline

```mermaid
flowchart TD
  A[rdflib Graph parse] --> B[Discover classes]
  B --> C[Extract owl:oneOf enums]
  C --> D[Collect object/data/annotation properties]
  D --> E[Collect datatypes]
  E --> F[Build classes + restrictions -> slots]
  F --> G[Collect individuals]
  G --> H[Collect annotations]
  H --> I[Assemble OModel]
```

## Writer Reuse Strategy

`mkdocs_writer._write_markdown_docs` is the shared markdown backbone used by:

- MkDocs output directly
- Docsify output (`README.md` home + `_sidebar.md`)
- Hugo output (`_index.md` home + post-processing for front matter/relref)

This keeps entity-page structure and link targets consistent across static-site outputs.
