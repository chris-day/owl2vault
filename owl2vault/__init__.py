"""OWL to LinkML/Obsidian conversion toolkit."""
from .model import (
    OEnumValue,
    OEnumeration,
    OProperty,
    OSlot,
    OClass,
    ODatatype,
    OIndividual,
    OModel,
)
from .note_id import iri_to_note_id
from .loader import load_owl
from .linkml_writer import model_to_linkml, write_linkml_yaml
from .obsidian_writer import write_obsidian_vault
from .mkdocs_writer import write_mkdocs_docs
from .docsify_writer import write_docsify_docs
from .hugo_writer import write_hugo_site

__all__ = [
    "OEnumValue",
    "OEnumeration",
    "OSlot",
    "OProperty",
    "OClass",
    "ODatatype",
    "OIndividual",
    "OModel",
    "iri_to_note_id",
    "load_owl",
    "model_to_linkml",
    "write_linkml_yaml",
    "write_obsidian_vault",
    "write_mkdocs_docs",
    "write_docsify_docs",
    "write_hugo_site",
]

__version__ = "0.1.18"
