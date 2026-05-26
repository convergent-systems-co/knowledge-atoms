# XAIP: Ontology Composition Schema

**Atom type:** `knowledge-base`
**Version:** 0.1
**Audience:** Knowledge engineers, domain modelers, platform integrators

---

## 1. Purpose

A knowledge-base composition is an ontology: a set of `entity-type` atoms, `relationship-type` atoms, and permitted-composition rules that together constrain what can be stored in a knowledge base and how stored facts relate to one another. The ontology is the schema layer; facts stored in the knowledge base must conform to it.

---

## 2. Composition Structure

A knowledge-base composition is a JSON document at the path `ontologies/<slug>/v<version>/ontology.json` within the knowledge-atoms catalog.

```json
{
  "atom_type": "knowledge-base",
  "ontology_id": "general-knowledge-base",
  "version": "1",
  "display_name": "General Knowledge Base",
  "entity_types": [
    {
      "entity_type_ref": "entity-type:concept",
      "display_name": "Concept",
      "attributes": [
        { "name": "label", "type": "string", "required": true },
        { "name": "definition", "type": "string", "required": false },
        { "name": "aliases", "type": "string[]", "required": false }
      ]
    },
    {
      "entity_type_ref": "entity-type:document",
      "display_name": "Document",
      "attributes": [
        { "name": "title", "type": "string", "required": true },
        { "name": "content_hash", "type": "sha256", "required": true },
        { "name": "source_uri", "type": "uri", "required": false }
      ]
    }
  ],
  "relationship_types": [
    {
      "relationship_type_ref": "relationship-type:references",
      "display_name": "References",
      "domain": "entity-type:document",
      "range": "entity-type:concept",
      "cardinality": "many-to-many"
    },
    {
      "relationship_type_ref": "relationship-type:is-a",
      "display_name": "Is-a (subtype)",
      "domain": "entity-type:concept",
      "range": "entity-type:concept",
      "cardinality": "many-to-one",
      "acyclic": true
    }
  ],
  "constraints": [
    {
      "constraint_id": "no-self-reference",
      "description": "An entity cannot reference itself via is-a.",
      "applies_to": "relationship-type:is-a",
      "rule": "domain_entity != range_entity"
    }
  ],
  "metadata": {
    "catalog_ref": "knowledge-atoms.convergent-systems.co"
  }
}
```

### 2.1 Required fields

| Field | Type | Description |
|---|---|---|
| `ontology_id` | string | Stable, slug-form identifier |
| `version` | string | Semantic version string |
| `entity_types` | array | Entity type atoms included in this ontology |
| `relationship_types` | array | Relationship type atoms and their domain/range constraints |
| `constraints` | array | Integrity rules applied at write time |

### 2.2 Entity type object fields

| Field | Type | Required | Description |
|---|---|---|---|
| `entity_type_ref` | URI | yes | Stable reference to an `entity-type` atom |
| `attributes` | array | yes | Attribute schema for instances of this entity type |
| `extends` | URI | no | Parent entity-type ref (for domain specialization, see §3) |

### 2.3 Relationship type object fields

| Field | Type | Required | Description |
|---|---|---|---|
| `relationship_type_ref` | URI | yes | Stable reference to a `relationship-type` atom |
| `domain` | URI or `"*"` | yes | Entity type(s) permitted as the relationship source |
| `range` | URI or `"*"` | yes | Entity type(s) permitted as the relationship target |
| `cardinality` | enum | yes | One of: `one-to-one`, `one-to-many`, `many-to-one`, `many-to-many` |
| `acyclic` | boolean | no | If `true`, the relationship graph must be a DAG (no cycles) |

---

## 3. Domain Ontology Specialization

Domain ontologies extend the general knowledge base with domain-specific entity and relationship types. They do not replace the base ontology; they add to it.

### 3.1 Extension declaration

A domain ontology declares its base via `extends_ontology_ref`:

```json
{
  "ontology_id": "medical-knowledge-base",
  "version": "1",
  "extends_ontology_ref": "https://knowledge-atoms.convergent-systems.co/ontologies/general-knowledge-base/v1/ontology.json",
  "entity_types": [
    {
      "entity_type_ref": "entity-type:medical/diagnosis",
      "display_name": "Diagnosis",
      "extends": "entity-type:concept",
      "attributes": [
        { "name": "icd_code", "type": "string", "required": true },
        { "name": "snomed_ct_id", "type": "string", "required": false },
        { "name": "severity", "type": "enum:low|moderate|high|critical", "required": false }
      ]
    },
    {
      "entity_type_ref": "entity-type:medical/procedure",
      "display_name": "Medical Procedure",
      "extends": "entity-type:concept",
      "attributes": [
        { "name": "cpt_code", "type": "string", "required": true }
      ]
    }
  ],
  "relationship_types": [
    {
      "relationship_type_ref": "relationship-type:medical/indicated-for",
      "display_name": "Indicated For",
      "domain": "entity-type:medical/procedure",
      "range": "entity-type:medical/diagnosis",
      "cardinality": "many-to-many"
    }
  ]
}
```

### 3.2 Specialization rules

- A domain ontology inherits all entity types, relationship types, and constraints from its base.
- Domain entity types that declare `extends` inherit the parent entity type's attributes. Attribute names MUST be unique within the extended type.
- Domain relationship types may use either domain-specific entity types or base entity types as domain/range.
- A domain ontology MUST NOT remove or relax constraints from its base. It may add new constraints.
- Specialization is single-inheritance only; a domain entity type may extend one parent entity type.

---

## 4. Cross-Base Federation

When two knowledge bases need to share entities (e.g., a medical knowledge base referencing a drug knowledge base), federation is achieved via cross-base entity references rather than merging ontologies.

### 4.1 Cross-base entity reference

```json
{
  "relationship_types": [
    {
      "relationship_type_ref": "relationship-type:medical/treated-with",
      "domain": "entity-type:medical/diagnosis",
      "range": {
        "remote_entity_type_ref": "https://knowledge-atoms.convergent-systems.co/ontologies/drug-knowledge-base/v1/ontology.json#entity-type:drug/medication"
      },
      "cardinality": "many-to-many",
      "federation_mode": "reference-only"
    }
  ]
}
```

### 4.2 Federation modes

| Mode | Behavior |
|---|---|
| `reference-only` | Only the remote entity's identifier is stored locally. Attribute resolution requires a query to the remote knowledge base. |
| `snapshot` | A point-in-time copy of the remote entity's attributes is stored locally. Staleness risk applies; a `snapshot_ttl_seconds` field governs refresh. |
| `live` | Attribute reads are proxied to the remote knowledge base at query time. Network dependency applies. |

---

## 5. Integration with fact-type atoms

Facts stored in a knowledge base must conform to the ontology. Each fact carries a `fact_type_ref` that maps to a `fact-type` atom, which in turn declares which entity types and relationship types the fact involves.

### 5.1 Fact conformance check

At write time, the knowledge base engine performs:

```
1. Read the incoming fact's fact_type_ref.
2. Resolve the fact-type atom.
3. Verify the fact's entity references are instances of the declared entity types.
4. Verify the fact's relationship is of the declared relationship type.
5. Evaluate all ontology constraints that apply to the relationship type.
6. If all checks pass: write the fact. Emit a fact_written event.
7. If any check fails: reject the fact. Return a ConformanceError with the violated rule.
```

### 5.2 Fact type atom reference

```json
{
  "fact_type_ref": "fact-type:medical/procedure-indicated-for-diagnosis",
  "entity_type_refs": [
    "entity-type:medical/procedure",
    "entity-type:medical/diagnosis"
  ],
  "relationship_type_ref": "relationship-type:medical/indicated-for",
  "ontology_ref": "https://knowledge-atoms.convergent-systems.co/ontologies/medical-knowledge-base/v1/ontology.json"
}
```

---

## 6. Catalog Conventions

| Convention | Value |
|---|---|
| Ontology path | `ontologies/<slug>/v<version>/ontology.json` |
| Entity-type atom path | `atoms/entity-types/<slug>/v<version>/atom.json` |
| Relationship-type atom path | `atoms/relationship-types/<slug>/v<version>/atom.json` |
| Fact-type atom path | `atoms/fact-types/<slug>/v<version>/atom.json` |
| Cross-base ref format | Fully-qualified HTTPS URI with `#<fragment>` for named element |

---

## 7. Related Atoms and Docs

- `entity-type` atom — schema and attributes for a class of entities
- `relationship-type` atom — domain, range, cardinality, and acyclicity rules for a relationship
- `fact-type` atom — declares which entity + relationship combination a fact represents
- `constraint` atom — integrity rule applied at write time across entity and relationship instances
- knowledge-base: cross-base federation conventions (§4 of this document)
