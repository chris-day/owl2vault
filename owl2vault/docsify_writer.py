"""Generate a Docsify-ready site from the intermediate model."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from .mkdocs_writer import _write_markdown_docs
from .model import OModel

log = logging.getLogger(__name__)


def _write_sidebar(nav: List[object], docs_dir: Path) -> None:
    lines: List[str] = []
    for entry in nav:
        if not isinstance(entry, dict):
            continue
        for label, value in entry.items():
            if isinstance(value, list):
                lines.append(f"- {label}")
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    for item_label, item_path in item.items():
                        lines.append(f"  - [{item_label}]({item_path})")
            else:
                lines.append(f"- [{label}]({value})")
    (docs_dir / "_sidebar.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_index_html(out_dir: Path, site_name: str) -> None:
    content = "\n".join(
        [
            "<!doctype html>",
            "<html>",
            "<head>",
            "  <meta charset=\"utf-8\" />",
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
            f"  <title>{site_name}</title>",
            "  <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/docsify@4/themes/vue.css\" />",
            "</head>",
            "<body>",
            "  <div id=\"app\"></div>",
            "  <script>",
            "    window.$docsify = {",
            f"      name: '{site_name}',",
            "      loadSidebar: true,",
            "    };",
            "  </script>",
            "  <script src=\"https://cdn.jsdelivr.net/npm/docsify@4\"></script>",
            "</body>",
            "</html>",
            "",
        ]
    )
    (out_dir / "index.html").write_text(content, encoding="utf-8")


def write_docsify_docs(om: OModel, out_dir: str) -> None:
    """Write a Docsify project with markdown docs for the ontology."""

    base = Path(out_dir)
    docs_dir = base / "docs"

    log.info(
        "Writing Docsify docs to %s (%d classes, %d enums, %d properties, %d datatypes, %d individuals)",
        base,
        len(om.classes),
        len(om.enums),
        len(om.properties),
        len(om.datatypes),
        len(om.individuals),
    )

    nav = _write_markdown_docs(om, docs_dir, index_filename="README.md")
    _write_sidebar(nav, docs_dir)
    _write_index_html(base, om.ontology_iri or "owl2vault docs")


__all__ = ["write_docsify_docs"]
