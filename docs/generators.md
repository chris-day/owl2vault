# Output Generators

## LinkML

- Module: `owl2vault/linkml_writer.py`
- Produces a LinkML schema dictionary and serializes YAML.
- Maps OWL/XSD datatypes to LinkML base types when possible.

## Obsidian

- Module: `owl2vault/obsidian_writer.py`
- Produces markdown notes with YAML front matter.
- Structure includes `Classes/`, `Enums/`, `Object_Properties/`, `Data_Properties/`, `Annotation_Properties/`, `Datatypes/`, `Individuals/`, and `00-Index/Index.md`.

## MkDocs

- Module: `owl2vault/mkdocs_writer.py`
- Produces `docs/` markdown content and `mkdocs.yml` in the chosen output directory.
- Uses section folders: `classes/`, `enums/`, `object_properties/`, `data_properties/`, `annotation_properties/`, `datatypes/`, `individuals/`.

## Docsify

- Module: `owl2vault/docsify_writer.py`
- Reuses shared markdown generation and writes:
  - `index.html`
  - `docs/README.md`
  - `docs/_sidebar.md`

## Hugo

- Module: `owl2vault/hugo_writer.py`
- Reuses shared markdown generation and adapts for Hugo:
  - `hugo.toml`
  - `content/_index.md`
  - per-section `content/<section>/_index.md`
  - TOML front matter (`type = "chapter"` for section index, `type = "default"` for entity pages)
  - markdown links rewritten as `{{% relref "..." %}}`
