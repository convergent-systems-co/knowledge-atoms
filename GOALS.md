# knowledge-atoms — Goals

> Knowledge graph primitives as a foundation for RAG, semantic memory, and AI knowledge bases — entity types, relationship types, provenance, fact types, confidence primitives.

*This document is derived from `aish/ARCHITECTURE.md` (now `xdao/xdao/ARCHITECTURE.md` §The *-Atoms Catalogs). Sections marked **Generated** are pattern-based and are intended as a starting point for revision, not as decided plan.*

---

## What this catalog makes civilization-grade

RAG systems and AI memory stores each invent their own entity model, relationship semantics, and provenance tracking. There's no canonical primitive vocabulary, so knowledge bases don't compose, federate, or transfer.

By cataloging the primitives, `knowledge-atoms` turns this domain from opaque-and-ephemeral to typed, versioned, composable, machine-readable, and open — the civilization-grade properties the ecosystem requires.

## What it catalogs

### Atom types

- **`entity-type`** — What kinds of things exist in the knowledge graph (Person, Organization, Document, Concept).
- **`relationship-type`** — How entities relate (authored-by, mentions, supersedes, contradicts).
- **`provenance-atom`** — Where a fact came from (source URL, document ID, conversation turn, sensor reading) with timestamp.
- **`fact-type`** — Categorization of facts (assertion, observation, inference, hypothesis).
- **`confidence-primitive`** — Calibrated confidence (probability, evidence count, source-trust score).

### Compositions: `knowledge-bases`

A knowledge-base composition is an ontology — entity types + relationship types + permitted compositions — that constrains what can be stored. Domain knowledge graphs (medical-knowledge-base, legal-knowledge-base) specialize the base ontology.

### Rule types

- **`relationship-constraint`** — Which entity types can participate in which relationships (only Person can authored-by, etc.).
- **`provenance-requirement`** — Every fact must have at least one provenance atom; high-confidence facts require multiple independent sources.
- **`contradiction-handling`** — How to represent and resolve contradictory facts (versioned, side-by-side, confidence-weighted).

## Runtime consumers

- **olympus** — Mnemosyne (cross-session semantic memory) already implements knowledge graph primitives locally. Formalizing them as a catalog makes shared memory possible across Mnemosyne instances and other RAG systems.

## Status & priority

**Current status:** `proposed`

**Priority tier:** Tier 2 — Highest priority to build next (runtime pull immediate)

**Trigger / activation condition:** Olympus Mnemosyne formalization. Cross-system semantic memory becomes possible once a shared vocabulary exists.

## Roadmap *(Generated — milestone shapes mirror aish's roadmap pattern; revise as actual work begins)*

### v0.1 — Bootstrap & spec acceptance

**Goal:** Schema accepted. Mnemosyne instances can exchange knowledge fragments using knowledge-atoms primitives.

**Success criterion:** Two Mnemosyne instances merge knowledge bases via export/import without loss of provenance or contradiction information.

**Kill criterion:** Provenance and contradiction handling proves intractable at scale — pivot to a simpler, lossy interchange format.

**Work:**

- [ ] XAIP: ontology composition schema
- [ ] Define 5 atom type schemas with provenance and confidence primitives
- [ ] Express Mnemosyne's internal model in knowledge-atoms
- [ ] Round-trip export/import test

### v0.2 — Adoption & expansion

**Goal:** Federation across knowledge bases.

**Work:**

- [ ] Federation protocol for distributed knowledge graphs
- [ ] Cross-base reference resolution
- [ ] Confidence-weighted merge

### v1.0 — Operational

**Goal:** Knowledge-atoms is the interchange layer for RAG and AI memory systems generally.

## Concrete atom example *(Generated — illustrative, not seed content)*

```yaml
knowledge-bases/aish-shell-history/definition.yml
---
id: aish-shell-history
type: composition
version: 0.1.0
entities:
  - { ref: atoms/entity-type/command }
  - { ref: atoms/entity-type/file }
  - { ref: atoms/entity-type/intent }
relationships:
  - { ref: atoms/relationship-type/operates-on, from: Command, to: File }
  - { ref: atoms/relationship-type/resolves-to, from: Intent, to: Command }
provenance_required: true
contradiction_handling: { ref: atoms/contradiction-handling/timestamped-supersession }
```

## Adoption strategy *(Generated)*

Olympus Mnemosyne anchors it. Reference exporters/importers for popular RAG stacks (LlamaIndex, LangChain memory) drive broader adoption.

## Civilization-grade property checklist

Every catalog must satisfy these before v1.0. Failing any blocks a release.

| Property | Mechanism in this catalog |
|---|---|
| Typed | JSON Schema in `schemas/` validates every atom, composition, rule |
| Versioned | Every atom has a semver `version` field; compositions reference atoms by version-pinned ID |
| Machine-readable | `exports/catalog.json` published on every release |
| Composable | Compositions reference atoms by ID; CI verifies references resolve and no circular dependencies |
| Open | Apache-2.0 licensed; LICENSE file present |
| Durable | No external dependencies for primary content (no remote image URLs, no vendor APIs in the hot path) |

## Related

- **Spec:** [atoms-spec](https://github.com/convergent-systems-co/atoms-spec) — the canonical structure every catalog conforms to
- **Tools:** [atoms-tools](https://github.com/convergent-systems-co/atoms-tools) — CLI for validate / export / bootstrap / resolve
- **Federation:** [xdao](https://github.com/convergent-systems-co/xdao) — ecosystem directory and discovery
- **Umbrella:** [atoms](https://github.com/convergent-systems-co/atoms) — every catalog as a git submodule
- **Manifest:** [`ATOMS.yml`](./ATOMS.yml) — this catalog's machine-readable manifest
- **Standard:** [`README.md`](./README.md) — catalog overview and contribution flow
