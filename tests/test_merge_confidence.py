"""Acceptance: confidence-weighted merge (issue #10).

Cases:
  (a) agreement: two facts asserting the same value with independent
      provenance should yield a merged confidence STRICTLY GREATER than
      either input.
  (b) contradiction: two facts asserting different values for the same
      (subject, predicate) must be preserved as a contradiction record
      per the active contradiction-handling rule (NOT silently dropped).
  (c) low-vs-high: a low-confidence claim must NOT displace a
      high-confidence claim without sufficient corroboration.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="session")
def merge_module(scripts_on_path):  # noqa: ARG001
    return importlib.import_module("merge")


def _fact(subject: str, predicate: str, value: str, confidence: float, source: str) -> dict:
    return {
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "confidence": {"value": confidence, "basis": "source-trust", "sources_count": 1},
        "provenance": [{"ref": f"knowledge-atoms://atoms/provenance-atom/{source}",
                        "captured_at": "2026-01-01T00:00:00Z"}],
    }


def test_agreement_increases_confidence(merge_module) -> None:
    left = [_fact("conv:1", "topic", "rag", 0.6, "document-source")]
    right = [_fact("conv:1", "topic", "rag", 0.6, "conversation-turn")]
    out = merge_module.merge(left, right)
    assert len(out) == 1
    merged_conf = out[0]["confidence"]["value"]
    assert merged_conf > 0.6, f"agreement must raise confidence above either input, got {merged_conf}"
    assert merged_conf <= 1.0


def test_contradiction_preserved(merge_module) -> None:
    left = [_fact("conv:1", "topic", "rag", 0.8, "document-source")]
    right = [_fact("conv:1", "topic", "embeddings", 0.7, "conversation-turn")]
    out = merge_module.merge(left, right)
    # Per contradiction-handling rule: both claims survive, marked as contradicting
    assert len(out) == 2, "contradiction must be preserved as two records, not silently merged"
    contradictions = [f for f in out if f.get("contradicts")]
    assert len(contradictions) == 2, "both sides of a contradiction must be marked"


def test_low_does_not_displace_high_without_corroboration(merge_module) -> None:
    high = [_fact("conv:1", "topic", "rag", 0.95, "document-source")]
    low = [_fact("conv:1", "topic", "embeddings", 0.2, "conversation-turn")]
    out = merge_module.merge(high, low, displacement_threshold=0.5)
    # The high-confidence claim must remain dominant — i.e., still present
    rag_records = [f for f in out if f["value"] == "rag"]
    assert rag_records, "high-confidence claim must not be displaced by single low-confidence claim"
    # And the low one is recorded but flagged as below threshold
    low_records = [f for f in out if f["value"] == "embeddings"]
    assert low_records, "low-confidence claim must still be preserved (no silent drop)"
    assert low_records[0].get("below_displacement_threshold") is True
