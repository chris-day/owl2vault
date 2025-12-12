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


log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert OWL to LinkML and Obsidian vault")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("-i", "--input", help="Path to input OWL file")
    src_group.add_argument("--url", help="URL to download OWL file from")
    parser.add_argument("--linkml", help="Output path for LinkML YAML")
    parser.add_argument("--vault", help="Output directory for Obsidian vault")
    parser.add_argument("--mkdocs", help="Output directory for MkDocs project")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

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

    if temp_dir:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
