# Development

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run Tests

```bash
pytest -q
```

## Build This Documentation

```bash
mkdocs build
mkdocs serve --dev-addr 0.0.0.0:8000
```

## Repo Layout

- `owl2vault/`: library and CLI code.
- `tests/`: unit and smoke tests.
- `docs/`: project documentation for MkDocs Material.
- `README.md`: install/usage overview.
