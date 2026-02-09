# CLI Reference

Entry point: `owl2vault = owl2vault.cli:main`

## Command

```bash
owl2vault [OPTIONS]
```

## Input Source (required, mutually exclusive)

- `-i, --input PATH`: local OWL file.
- `--url URL`: remote OWL resource (downloaded to temp file before parsing).

## Output Options

- `--linkml PATH`: write LinkML YAML.
- `--vault DIR`: write Obsidian vault.
- `--mkdocs DIR`: write MkDocs project.
- `--docsify DIR`: write Docsify project.
- `--hugo DIR`: write Hugo project.
- `--create-dirs`: create missing output directories (and `--linkml` parent directory) before writing.

## Logging

- `--log-level {ERROR,WARNING,INFO,DEBUG}` (default: `INFO`).

## Behavior

- Multiple outputs can be requested in one run.
- If `--url` is used, temporary files are cleaned up automatically.
- Without `--create-dirs`, the CLI warns and exits if required output directories do not exist.
