"""OWL to LinkML/Obsidian conversion toolkit."""
from .model import OEnumValue, OEnumeration, OProperty, OSlot, OClass, ODatatype, OModel
from .note_id import iri_to_note_id
from .loader import load_owl
from .linkml_writer import model_to_linkml, write_linkml_yaml
from .obsidian_writer import write_obsidian_vault

__all__ = [
    "OEnumValue",
    "OEnumeration",
    "OSlot",
    "OProperty",
    "OClass",
    "ODatatype",
    "OModel",
    "iri_to_note_id",
    "load_owl",
    "model_to_linkml",
    "write_linkml_yaml",
    "write_obsidian_vault",
]

__version__ = "0.1.3"
