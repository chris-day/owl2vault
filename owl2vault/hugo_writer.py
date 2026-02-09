"""Generate a Hugo-ready site from the intermediate model."""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import List

from .mkdocs_writer import _write_markdown_docs
from .model import OModel

log = logging.getLogger(__name__)


def _write_config(out_dir: Path, site_name: str) -> None:
    content = "\n".join(
        [
            f'title = "{site_name}"',
            'baseURL = "/"',
            'languageCode = "en-us"',
            "",
        ]
    )
    (out_dir / "hugo.toml").write_text(content, encoding="utf-8")


def _toml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\"", "\\\"")


def _write_section_indexes(nav: List[object], content_dir: Path) -> None:
    for entry in nav:
        if not isinstance(entry, dict):
            continue
        for section, items in entry.items():
            if not isinstance(items, list):
                continue
            first_path = None
            for item in items:
                if isinstance(item, dict):
                    first_path = next(iter(item.values()), None)
                    if first_path:
                        break
            if not first_path:
                continue
            section_dir = content_dir / Path(first_path).parent
            lines = [
                "+++",
                f'title = "{_toml_escape(section)}"',
                'type = "chapter"',
                "+++",
                "",
            ]
            for item in items:
                if not isinstance(item, dict):
                    continue
                for label, path in item.items():
                    rel = Path(path).as_posix()
                    lines.append(f"- [{label}]({{{{% relref \"{rel}\" %}}}})")
            (section_dir / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _add_front_matter(content_dir: Path) -> None:
    for md in content_dir.rglob("*.md"):
        if md.name == "_index.md":
            continue
        text = md.read_text(encoding="utf-8")
        if text.lstrip().startswith("+++"):
            continue
        title = md.stem
        lines = text.splitlines()
        body_lines: List[str] = []
        heading_consumed = False
        for line in lines:
            if not heading_consumed and line.startswith("# "):
                title = line[2:].strip()
                heading_consumed = True
                continue
            body_lines.append(line)
        front = "\n".join(
            [
                "+++",
                f'title = "{_toml_escape(title)}"',
                'type = "default"',
                "+++",
                "",
            ]
        )
        md.write_text(front + "\n".join(body_lines).lstrip(), encoding="utf-8")


def _rewrite_links_for_hugo(content_dir: Path) -> None:
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for md in content_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8")

        def _replace(match: re.Match[str]) -> str:
            label = match.group(1)
            target = match.group(2).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                return match.group(0)
            if target.startswith("#"):
                return match.group(0)
            target, anchor = (target.split("#", 1) + [""])[:2]
            target = target.split("?", 1)[0]
            if not target.endswith(".md"):
                return match.group(0)
            resolved = (md.parent / target).resolve()
            try:
                rel = resolved.relative_to(content_dir)
            except ValueError:
                rel = Path(os.path.relpath(resolved, content_dir))
            rel_str = rel.as_posix()
            if not rel_str.endswith(".md"):
                return match.group(0)
            repl = "[{}]({{{{% relref \"{}\" %}}}})".format(label, rel_str)
            if anchor:
                repl += f"#{anchor}"
            return repl

        updated = link_re.sub(_replace, text)
        if updated != text:
            md.write_text(updated, encoding="utf-8")


def write_hugo_site(om: OModel, out_dir: str) -> None:
    """Write a Hugo project with markdown docs for the ontology."""

    base = Path(out_dir)
    content_dir = base / "content"

    log.info(
        "Writing Hugo site to %s (%d classes, %d enums, %d properties, %d datatypes, %d individuals)",
        base,
        len(om.classes),
        len(om.enums),
        len(om.properties),
        len(om.datatypes),
        len(om.individuals),
    )

    nav = _write_markdown_docs(om, content_dir, index_filename="_index.md")
    _write_section_indexes(nav, content_dir)
    _add_front_matter(content_dir)
    _rewrite_links_for_hugo(content_dir)
    _write_config(base, om.ontology_iri or "owl2vault docs")


__all__ = ["write_hugo_site"]
