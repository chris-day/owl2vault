"""Command line interface for owl2vault."""
from __future__ import annotations

import argparse
import logging
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .linkml_writer import write_linkml_yaml
from .loader import load_owl
from .obsidian_writer import write_obsidian_vault
from .mkdocs_writer import write_mkdocs_docs
from .docsify_writer import write_docsify_docs
from .hugo_writer import write_hugo_site


log = logging.getLogger(__name__)


def _prepare_output_paths(args: argparse.Namespace) -> None:
    missing: list[tuple[Path, str]] = []

    def _check_dir(path_value: str | None, label: str) -> None:
        if not path_value:
            return
        path = Path(path_value)
        if path.exists():
            if not path.is_dir():
                raise SystemExit(f"{label} must be a directory: {path}")
            return
        missing.append((path, label))

    if args.linkml:
        linkml_path = Path(args.linkml)
        args.linkml = str(linkml_path)
        parent = linkml_path.parent if str(linkml_path.parent) else Path(".")
        if parent.exists():
            if not parent.is_dir():
                raise SystemExit(f"--linkml parent must be a directory: {parent}")
        else:
            missing.append((parent, "--linkml parent directory"))

    _check_dir(args.vault, "--vault")
    _check_dir(args.mkdocs, "--mkdocs")
    _check_dir(args.docsify, "--docsify")
    _check_dir(args.hugo, "--hugo")

    if not missing:
        return

    for path, label in missing:
        log.warning("%s does not exist: %s", label, path)

    if not args.create_dirs:
        raise SystemExit(
            "One or more output directories do not exist. "
            "Create them manually or re-run with --create-dirs."
        )

    for path, label in missing:
        path.mkdir(parents=True, exist_ok=True)
        log.info("Created missing directory for %s: %s", label, path)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert OWL to LinkML and Obsidian vault")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("-i", "--input", help="Path to input OWL file")
    src_group.add_argument("--url", help="URL to download OWL file from")
    parser.add_argument("--linkml", help="Output path for LinkML YAML")
    parser.add_argument("--vault", help="Output directory for Obsidian vault")
    parser.add_argument("--mkdocs", help="Output directory for MkDocs project")
    parser.add_argument("--docsify", help="Output directory for Docsify project")
    parser.add_argument("--hugo", help="Output directory for Hugo project")
    parser.add_argument(
        "--create-dirs",
        action="store_true",
        help="Create missing output directories before writing results",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    _prepare_output_paths(args)

    owl_path = args.input
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.url:
        temp_dir = tempfile.TemporaryDirectory()
        target_name = Path(urlparse(args.url).path).name or "ontology.owl"
        target_path = Path(temp_dir.name) / target_name
        log.info("Downloading OWL from %s", args.url)
        urllib.request.urlretrieve(args.url, target_path)
        owl_path = str(target_path)

    log.info("Loading OWL model from %s", owl_path)
    model = load_owl(owl_path)

    if args.linkml:
        log.info("Writing LinkML YAML to %s", args.linkml)
        write_linkml_yaml(model, args.linkml)
    if args.vault:
        log.info("Writing Obsidian vault to %s", args.vault)
        write_obsidian_vault(model, args.vault)
    if args.mkdocs:
        log.info("Writing MkDocs documentation to %s", args.mkdocs)
        write_mkdocs_docs(model, args.mkdocs)
    if args.docsify:
        log.info("Writing Docsify documentation to %s", args.docsify)
        write_docsify_docs(model, args.docsify)
    if args.hugo:
        log.info("Writing Hugo site to %s", args.hugo)
        write_hugo_site(model, args.hugo)

    if temp_dir:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
