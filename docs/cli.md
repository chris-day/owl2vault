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

## Logging

- `--log-level {ERROR,WARNING,INFO,DEBUG}` (default: `INFO`).

## Behavior

- Multiple outputs can be requested in one run.
- If `--url` is used, temporary files are cleaned up automatically.
