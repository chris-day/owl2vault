# Examples

## Single Output

```bash
# LinkML only
owl2vault -i input/schema.owl --linkml output/schema.yaml

# Obsidian vault only
owl2vault -i input/schema.owl --vault output/vault

# MkDocs only
owl2vault -i input/schema.owl --mkdocs output/mkdocs

# Docsify only
owl2vault -i input/schema.owl --docsify output/docsify

# Hugo only
owl2vault -i input/schema.owl --hugo output/hugo
```

## Multi-Output

```bash
owl2vault -i input/schema.owl \
  --linkml output/schema.yaml \
  --vault output/vault \
  --mkdocs output/mkdocs \
  --docsify output/docsify \
  --hugo output/hugo
```

## URL Input

```bash
owl2vault --url https://ekgf.github.io/dprod/dprod.ttl \
  --mkdocs output/mkdocs \
  --hugo output/hugo
```

## Serve Generated Sites

```bash
# MkDocs
cd output/mkdocs
mkdocs serve --dev-addr 0.0.0.0:8000

# Docsify (using Python HTTP server)
cd output/docsify
python -m http.server 8000

# Hugo
cd output/hugo
hugo serve --bind 0.0.0.0 --port 8000
```
