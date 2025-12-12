"""Command line interface for owl2vault."""
from __future__ import annotations

import argparse
import logging

from .linkml_writer import write_linkml_yaml
from .loader import load_owl
from .obsidian_writer import write_obsidian_vault
from .mkdocs_writer import write_mkdocs_docs


log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert OWL to LinkML and Obsidian vault")
    parser.add_argument("-i", "--input", required=True, help="Path to input OWL file")
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

    log.info("Loading OWL model from %s", args.input)
    model = load_owl(args.input)

    if args.linkml:
        log.info("Writing LinkML YAML to %s", args.linkml)
        write_linkml_yaml(model, args.linkml)
    if args.vault:
        log.info("Writing Obsidian vault to %s", args.vault)
        write_obsidian_vault(model, args.vault)
    if args.mkdocs:
        log.info("Writing MkDocs documentation to %s", args.mkdocs)
        write_mkdocs_docs(model, args.mkdocs)


if __name__ == "__main__":
    main()
