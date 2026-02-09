# SPARQL Templates for owl2vault

This document provides SPARQL 1.1 templates aligned with the owl2vault model and generation logic. Replace `<TARGET_IRI>` with the entity IRI you are rendering. Queries are scoped to the fields owl2vault actually extracts (labels, comments, domains, ranges, slots via restrictions, etc.).

Unless noted, labels are `rdfs:label`, descriptions are `rdfs:comment`, and annotations are limited to properties typed as `owl:AnnotationProperty` (excluding `rdfs:label` and `rdfs:comment`).

## Prefixes

```sparql
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
```

## Classes

### Summary (label + comment)

```sparql
SELECT ?label ?comment WHERE {
  BIND(<TARGET_IRI> AS ?c)
  OPTIONAL { ?c rdfs:label ?label }
  OPTIONAL { ?c rdfs:comment ?comment }
}
```

### Superclasses (rdfs:subClassOf IRIs only)

```sparql
SELECT ?super ?superLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?c rdfs:subClassOf ?super .
  FILTER(isIRI(?super))
  OPTIONAL { ?super rdfs:label ?superLabel }
}
```

### Subclasses

```sparql
SELECT ?sub ?subLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?sub rdfs:subClassOf ?c .
  OPTIONAL { ?sub rdfs:label ?subLabel }
}
```

### Equivalent classes

```sparql
SELECT ?eq ?eqLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?c owl:equivalentClass ?eq .
  FILTER(isIRI(?eq))
  OPTIONAL { ?eq rdfs:label ?eqLabel }
}
```

### Disjoint classes

```sparql
SELECT ?dj ?djLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?c owl:disjointWith ?dj .
  FILTER(isIRI(?dj))
  OPTIONAL { ?dj rdfs:label ?djLabel }
}
```

### Properties (Slots) inferred from restrictions

owl2vault only turns `owl:Restriction` nodes in `rdfs:subClassOf` into slots. The restriction must include `owl:onProperty` and either `owl:someValuesFrom` or `owl:allValuesFrom`. Cardinalities are picked from `owl:minCardinality`, `owl:maxCardinality`, or `owl:cardinality`.

```sparql
SELECT ?prop ?propLabel ?range ?rangeLabel ?minCard ?maxCard ?exactCard WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?c rdfs:subClassOf ?r .
  ?r a owl:Restriction ;
     owl:onProperty ?prop .
  OPTIONAL { ?prop rdfs:label ?propLabel }
  OPTIONAL { ?r owl:someValuesFrom ?range }
  OPTIONAL { ?r owl:allValuesFrom ?range }
  OPTIONAL { ?range rdfs:label ?rangeLabel }
  OPTIONAL { ?r owl:minCardinality ?minCard }
  OPTIONAL { ?r owl:maxCardinality ?maxCard }
  OPTIONAL { ?r owl:cardinality ?exactCard }
}
```

### Annotations (annotation properties only)

```sparql
SELECT ?pred ?predLabel ?val ?valLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?c ?pred ?val .
  ?pred a owl:AnnotationProperty .
  FILTER(?pred NOT IN (rdfs:label, rdfs:comment))
  OPTIONAL { ?pred rdfs:label ?predLabel }
  OPTIONAL { ?val rdfs:label ?valLabel }
}
```

### Instances

```sparql
SELECT ?inst ?instLabel WHERE {
  BIND(<TARGET_IRI> AS ?c)
  ?inst rdf:type ?c .
  OPTIONAL { ?inst rdfs:label ?instLabel }
}
```

## Enumerations

owl2vault treats a class as an enum if it has `owl:oneOf`. Each member becomes a permissible value.

### Summary

```sparql
SELECT ?label ?comment WHERE {
  BIND(<TARGET_IRI> AS ?e)
  OPTIONAL { ?e rdfs:label ?label }
  OPTIONAL { ?e rdfs:comment ?comment }
}
```

### Permissible values (owl:oneOf list)

```sparql
SELECT ?member ?memberLabel ?memberComment WHERE {
  BIND(<TARGET_IRI> AS ?e)
  ?e owl:oneOf/rdf:rest*/rdf:first ?member .
  OPTIONAL { ?member rdfs:label ?memberLabel }
  OPTIONAL { ?member rdfs:comment ?memberComment }
}
```

## Properties (Object/Data/Annotation)

owl2vault discovers properties by type (`owl:ObjectProperty`, `owl:DatatypeProperty`, `owl:AnnotationProperty`) and reads label, comment, domains, ranges, inverse, equivalent, characteristics.

### Summary (label + kind)

```sparql
SELECT ?label ?comment ?kind WHERE {
  BIND(<TARGET_IRI> AS ?p)
  OPTIONAL { ?p rdfs:label ?label }
  OPTIONAL { ?p rdfs:comment ?comment }
  OPTIONAL {
    ?p rdf:type ?kind .
    FILTER(?kind IN (owl:ObjectProperty, owl:DatatypeProperty, owl:AnnotationProperty))
  }
}
```

### Domains

```sparql
SELECT ?domain ?domainLabel WHERE {
  BIND(<TARGET_IRI> AS ?p)
  ?p rdfs:domain ?domain .
  OPTIONAL { ?domain rdfs:label ?domainLabel }
}
```

### Ranges

```sparql
SELECT ?range ?rangeLabel WHERE {
  BIND(<TARGET_IRI> AS ?p)
  ?p rdfs:range ?range .
  OPTIONAL { ?range rdfs:label ?rangeLabel }
}
```

### Inverse properties (both directions)

```sparql
SELECT ?inv ?invLabel WHERE {
  BIND(<TARGET_IRI> AS ?p)
  { ?p owl:inverseOf ?inv }
  UNION
  { ?inv owl:inverseOf ?p }
  OPTIONAL { ?inv rdfs:label ?invLabel }
}
```

### Equivalent properties

```sparql
SELECT ?eq ?eqLabel WHERE {
  BIND(<TARGET_IRI> AS ?p)
  ?p owl:equivalentProperty ?eq .
  OPTIONAL { ?eq rdfs:label ?eqLabel }
}
```

### Characteristics

```sparql
SELECT ?char WHERE {
  BIND(<TARGET_IRI> AS ?p)
  ?p rdf:type ?char .
  FILTER(?char IN (
    owl:FunctionalProperty,
    owl:InverseFunctionalProperty,
    owl:SymmetricProperty,
    owl:TransitiveProperty
  ))
}
```

### Annotations (annotation properties only)

```sparql
SELECT ?pred ?predLabel ?val ?valLabel WHERE {
  BIND(<TARGET_IRI> AS ?p)
  ?p ?pred ?val .
  ?pred a owl:AnnotationProperty .
  FILTER(?pred NOT IN (rdfs:label, rdfs:comment))
  OPTIONAL { ?pred rdfs:label ?predLabel }
  OPTIONAL { ?val rdfs:label ?valLabel }
}
```

## Datatypes

owl2vault preloads common XSD datatypes and treats `rdfs:Datatype` as custom datatypes.

### Summary

```sparql
SELECT ?label ?comment WHERE {
  BIND(<TARGET_IRI> AS ?d)
  OPTIONAL { ?d rdfs:label ?label }
  OPTIONAL { ?d rdfs:comment ?comment }
}
```

### Base datatype (owl:onDatatype or subclass)

```sparql
SELECT ?base WHERE {
  BIND(<TARGET_IRI> AS ?d)
  OPTIONAL { ?d owl:onDatatype ?base }
  OPTIONAL { ?d rdfs:subClassOf ?base }
}
```

## Individuals

owl2vault treats nodes typed as `owl:NamedIndividual` or any instance of a known class as individuals.

### Summary

```sparql
SELECT ?label ?comment WHERE {
  BIND(<TARGET_IRI> AS ?i)
  OPTIONAL { ?i rdfs:label ?label }
  OPTIONAL { ?i rdfs:comment ?comment }
}
```

### Types

```sparql
SELECT ?type ?typeLabel WHERE {
  BIND(<TARGET_IRI> AS ?i)
  ?i rdf:type ?type .
  FILTER(?type != owl:NamedIndividual)
  OPTIONAL { ?type rdfs:label ?typeLabel }
}
```

### sameAs

```sparql
SELECT ?sameAs WHERE {
  BIND(<TARGET_IRI> AS ?i)
  ?i owl:sameAs ?sameAs .
}
```

### Annotations (annotation properties only)

```sparql
SELECT ?pred ?predLabel ?val ?valLabel WHERE {
  BIND(<TARGET_IRI> AS ?i)
  ?i ?pred ?val .
  ?pred a owl:AnnotationProperty .
  FILTER(?pred NOT IN (rdfs:label, rdfs:comment))
  OPTIONAL { ?pred rdfs:label ?predLabel }
  OPTIONAL { ?val rdfs:label ?valLabel }
}
```
