# Data Model

The intermediate model (`OModel`) is defined in `owl2vault/model.py` and acts as the contract between parsing and rendering.

## Core Entities

- `OModel`
- `OClass`
- `OSlot`
- `OProperty`
- `OEnumeration`
- `OEnumValue`
- `ODatatype`
- `OIndividual`

## Relationship Overview

```mermaid
classDiagram
  class OModel {
    +ontology_iri
    +prefixes
    +classes
    +enums
    +datatypes
    +properties
    +individuals
  }

  class OClass {
    +iri
    +label
    +super_iris
    +equivalent_iris
    +disjoint_iris
    +slots
    +annotations
  }

  class OSlot {
    +iri
    +name
    +range_iri
    +range_label
    +is_object
    +min_card
    +max_card
  }

  class OProperty {
    +iri
    +label
    +domains
    +ranges
    +kind
    +equivalent_iris
    +inverse_iris
    +characteristics
    +annotations
  }

  class OEnumeration {
    +iri
    +label
    +values
  }

  class OEnumValue {
    +iri
    +code
    +label
  }

  class ODatatype {
    +iri
    +label
    +base_iri
    +pattern
  }

  class OIndividual {
    +iri
    +label
    +types
    +same_as
    +annotations
  }

  OModel --> OClass
  OModel --> OProperty
  OModel --> OEnumeration
  OModel --> ODatatype
  OModel --> OIndividual
  OClass --> OSlot
  OEnumeration --> OEnumValue
```

## Notes

- Annotation values are modeled as `(value, is_iri)` tuples so writers can render either literal text or links.
- Writer modules use IRI-derived stable note/page IDs from `owl2vault/note_id.py`.
