# Confidence-Weighted Merge

## What it is

When multiple knowledge-base compositions assert the same fact with different confidence scores, confidence-weighted merge produces a single canonical fact with an aggregated confidence.

## Merge formula

Given N independent fact assertions about the same entity+predicate pair:

```
merged_confidence = 1 - ∏(1 - cᵢ)   [independent evidence]
```

Where cᵢ is the confidence of each source. This is the Bayesian complement product — if two independent sources each believe the fact with 0.8 confidence, the merged confidence is `1 - (0.2 × 0.2) = 0.96`.

## Conflict resolution

When assertions **contradict** each other (same predicate, different values):
1. Select the assertion with highest confidence as the canonical value
2. Record all contradicting assertions in the `alternatives` field
3. Set merged confidence = max(cᵢ) × (1 - 0.1 × N) where N is the number of contradicting sources

## Atom representation

The merged fact-type atom carries:
```yaml
confidence: 0.96          # merged confidence
confidence_method: bayesian_complement_product
sources:
  - ref: knowledge-atoms/fact-type/atoms-spec-version
    confidence: 0.95
  - ref: knowledge-atoms/fact-type/schema-atoms-atom-count
    confidence: 0.95
alternatives: []          # empty if no contradictions
```
