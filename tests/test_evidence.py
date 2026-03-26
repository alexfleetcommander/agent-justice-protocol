"""Tests for evidence.py — scoping, filtering, redaction."""

import pytest
from agent_justice_protocol.evidence import (
    EvidenceRequest,
    RedactionEntry,
    RedactionManifest,
    filter_relevant_evidence,
    DEFAULT_WINDOW_HOURS,
    MAX_WINDOW_HOURS,
)
from agent_justice_protocol.schema import EvidenceRecord


class TestEvidenceRequest:
    def test_default_window(self):
        req = EvidenceRequest(
            investigation_id="inv-001",
            target_agent_id="target-01",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=["chain_entry"],
            incident_relevance="Direct evidence",
        )
        assert req.window_hours == DEFAULT_WINDOW_HOURS
        # Check window boundaries
        assert "2026-03-19" in req.time_window_start
        assert "2026-03-21" in req.time_window_end

    def test_extended_window_requires_justification(self):
        with pytest.raises(ValueError, match="justification"):
            EvidenceRequest(
                investigation_id="inv-001",
                target_agent_id="target-01",
                incident_time="2026-03-20T12:00:00.000000Z",
                evidence_types_requested=["chain_entry"],
                incident_relevance="x",
                window_hours=48,
            )

    def test_extended_window_with_justification(self):
        req = EvidenceRequest(
            investigation_id="inv-001",
            target_agent_id="target-01",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=["chain_entry"],
            incident_relevance="x",
            window_hours=48,
            justification="Complex multi-day incident",
        )
        assert req.window_hours == 48

    def test_max_window_exceeded(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            EvidenceRequest(
                investigation_id="inv",
                target_agent_id="t",
                incident_time="2026-03-20T12:00:00.000000Z",
                evidence_types_requested=[],
                incident_relevance="x",
                window_hours=MAX_WINDOW_HOURS + 1,
                justification="doesn't matter",
            )

    def test_is_within_scope(self):
        req = EvidenceRequest(
            investigation_id="inv",
            target_agent_id="t",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=[],
            incident_relevance="x",
        )
        assert req.is_within_scope("2026-03-20T10:00:00.000000Z")
        assert not req.is_within_scope("2026-03-18T10:00:00.000000Z")

    def test_roundtrip(self):
        req = EvidenceRequest(
            investigation_id="inv-001",
            target_agent_id="target-01",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=["chain_entry", "telemetry"],
            incident_relevance="Testing",
            approved_by="investigator-01",
        )
        d = req.to_dict()
        req2 = EvidenceRequest.from_dict(d)
        assert req2.investigation_id == "inv-001"
        assert req2.target_agent_id == "target-01"


class TestFilterEvidence:
    def test_temporal_filtering(self):
        req = EvidenceRequest(
            investigation_id="inv",
            target_agent_id="t",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=[],
            incident_relevance="x",
        )
        evidence = [
            EvidenceRecord(
                evidence_type="telemetry", provenance_tier=2,
                source_agent_id="a",
                content="in-scope",
                source_timestamp="2026-03-20T10:00:00.000000Z",
            ),
            EvidenceRecord(
                evidence_type="telemetry", provenance_tier=2,
                source_agent_id="a",
                content="out-of-scope",
                source_timestamp="2026-03-15T10:00:00.000000Z",
            ),
        ]
        # Manually set timestamps
        evidence[0].source_timestamp = "2026-03-20T10:00:00.000000Z"
        evidence[1].source_timestamp = "2026-03-15T10:00:00.000000Z"
        filtered = filter_relevant_evidence(evidence, req)
        assert len(filtered) == 1
        assert filtered[0].content == "in-scope"

    def test_type_filtering(self):
        req = EvidenceRequest(
            investigation_id="inv",
            target_agent_id="t",
            incident_time="2026-03-20T12:00:00.000000Z",
            evidence_types_requested=["chain_entry"],
            incident_relevance="x",
        )
        evidence = [
            EvidenceRecord(
                evidence_type="chain_entry", provenance_tier=1,
                source_agent_id="a", content="yes",
                source_timestamp="2026-03-20T12:00:00.000000Z",
            ),
            EvidenceRecord(
                evidence_type="telemetry", provenance_tier=2,
                source_agent_id="a", content="no",
                source_timestamp="2026-03-20T12:00:00.000000Z",
            ),
        ]
        filtered = filter_relevant_evidence(evidence, req)
        assert len(filtered) == 1
        assert filtered[0].evidence_type == "chain_entry"


class TestRedaction:
    def test_manifest_creation(self):
        manifest = RedactionManifest(
            evidence_id="ev-001",
            agent_id="agent-01",
        )
        entry = manifest.add_redaction(
            segment_id="seg-1",
            justification="Unrelated internal discussion",
            original_content="secret content",
        )
        assert entry.unredacted_hash
        assert len(manifest.redactions) == 1

    def test_roundtrip(self):
        manifest = RedactionManifest(
            evidence_id="ev-001",
            agent_id="agent-01",
        )
        manifest.add_redaction("seg-1", "Unrelated", "content")
        d = manifest.to_dict()
        m2 = RedactionManifest.from_dict(d)
        assert m2.evidence_id == "ev-001"
        assert len(m2.redactions) == 1
