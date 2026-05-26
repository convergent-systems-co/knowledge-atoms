# Cross-Base Reference Resolution

## What it is

Cross-base reference resolution allows a fact or relationship in one knowledge-base composition to reference entities defined in a different knowledge-base. Resolution is the process of following those references to retrieve the canonical atom definition.

## Reference format

A cross-base reference uses the full atom ID:
```
knowledge-atoms/entity-type/convergent-systems-co
```

When a fact-type atom in `knowledge-base/olympus` references `knowledge-atoms/entity-type/convergent-systems-co`, the runtime resolver must:
1. Parse the catalog and entity-type segments from the ID
2. Fetch the entity-type atom from the knowledge-atoms catalog
3. Validate the reference resolves to an existing, non-historic atom

## Resolution algorithm

```
resolve(ref: string) → Atom | ResolutionError
  1. Split ref by "/" into (catalog, type, slug)
  2. Look up catalog in the federation registry
  3. Fetch atom at: <catalog_domain>/exports/catalog.json
  4. Filter atoms where id == ref
  5. If found and lifecycle != "historic": return atom
  6. Else: return ResolutionError(NOT_FOUND | HISTORIC)
```

## Failure modes

- **NOT_FOUND**: atom was never published
- **HISTORIC**: atom exists but has been superseded — consumers should update to the replacement
- **UNREACHABLE**: the catalog domain is offline — use cached last-known state

## Cross-catalog validation rule

A composition that references atoms across catalogs must declare those cross-references in a `references` block for static validation at CI time.
