"""Tests for forensics.py — investigation engine."""

import pytest
from agent_justice_protocol.schema import (
    AgentReference,
    EvidenceRecord,
    FaultAllocation,
)
from agent_justice_protocol.forensics import (
    ForensicInvestigation,
    IncidentReport,
)


def _make_report():
    return IncidentReport(
        reporter=AgentReference(agent_id="monitor-01"),
        incident_type="service_failure",
        severity="high",
        description="Agent failed to respond to request",
        subjects=[AgentReference(agent_id="suspect-01")],
    )


def _make_evidence(agent_id, content, tier=2, etype="interaction_log", timestamp=None):
    ev = EvidenceRecord(
        evidence_type=etype,
        provenance_tier=tier,
        source_agent_id=agent_id,
        content=content,
    )
    if timestamp:
        ev.source_timestamp = timestamp
    return ev


class TestForensicInvestigation:
    def test_basic_investigation(self):
        report = _make_report()
        inv = ForensicInvestigation(report)
        assert inv.investigation_id
        assert inv.phase == "initiation"

    def test_add_evidence(self):
        inv = ForensicInvestigation(_make_report())
        ev = _make_evidence("suspect-01", {"action": "timeout"})
        inv.add_evidence(ev)
        assert len(inv.evidence) == 1
        assert inv.phase == "evidence_collection"
        # Chain of custody should have an entry
        assert len(ev.chain_of_custody) >= 1

    def test_add_evidence_batch(self):
        inv = ForensicInvestigation(_make_report())
        records = [
            _make_evidence("a1", {"action": "request"}),
            _make_evidence("a2", {"action": "response"}),
            _make_evidence("a3", {"action": "timeout"}),
        ]
        count = inv.add_evidence_batch(records)
        assert count == 3
        assert len(inv.evidence) == 3

    def test_reconstruct_timeline(self):
        inv = ForensicInvestigation(_make_report())
        inv.add_evidence(_make_evidence(
            "a1", {"action": "request_sent"},
            timestamp="2026-03-20T10:00:00.000000Z",
        ))
        inv.add_evidence(_make_evidence(
            "a2", {"action": "request_received"},
            timestamp="2026-03-20T10:00:01.000000Z",
        ))
        inv.add_evidence(_make_evidence(
            "a1", {"action": "timeout_detected"},
            timestamp="2026-03-20T10:05:00.000000Z",
        ))
        timeline = inv.reconstruct_timeline()
        assert len(timeline) == 3
        assert timeline[0].sequence == 1
        assert timeline[2].sequence == 3
        assert inv.phase == "timeline_reconstruction"

    def test_causal_indicators(self):
        report = _make_report()
        report.incident_time = "2026-03-20T10:10:00.000000Z"
        inv = ForensicInvestigation(report)
        # Add evidence with violation keyword
        inv.add_evidence(_make_evidence(
            "suspect-01",
            {"action": "unauthorized access to database"},
            timestamp="2026-03-20T10:09:00.000000Z",
        ))
        indicators = inv.generate_causal_indicators()
        # Should have temporal correlation and policy violation
        types = {ci.indicator_type for ci in indicators}
        assert "temporal_correlation" in types
        assert "policy_violation" in types

    def test_produce_finding(self):
        report = _make_report()
        report.incident_time = "2026-03-20T10:10:00.000000Z"
        inv = ForensicInvestigation(report)
        inv.add_evidence(_make_evidence(
            "suspect-01",
            {"action": "deleted production data"},
            tier=1,
            timestamp="2026-03-20T10:09:30.000000Z",
        ))
        inv.add_evidence(_make_evidence(
            "monitor-01",
            {"action": "alert triggered"},
            tier=2,
            timestamp="2026-03-20T10:10:00.000000Z",
        ))

        finding = inv.produce_finding(
            fault_allocation=[
                FaultAllocation(agent_id="suspect-01", fault_percentage=100),
            ],
        )
        assert finding.finding_id
        assert finding.finding_hash
        assert finding.verify_hash()
        assert finding.total_evidence_items == 2
        assert finding.tier_1_count == 1
        assert finding.tier_2_count == 1
        assert len(finding.timeline) == 2
        assert inv.phase == "finding_generation"

    def test_evidence_by_tier(self):
        inv = ForensicInvestigation(_make_report())
        inv.add_evidence(_make_evidence("a", "x", tier=1))
        inv.add_evidence(_make_evidence("a", "y", tier=1))
        inv.add_evidence(_make_evidence("a", "z", tier=3))
        by_tier = inv.evidence_by_tier
        assert len(by_tier[1]) == 2
        assert len(by_tier[3]) == 1
        assert len(by_tier[2]) == 0

    def test_create_evidence_request(self):
        inv = ForensicInvestigation(_make_report())
        req = inv.create_evidence_request(
            target_agent_id="suspect-01",
            evidence_types=["chain_entry", "interaction_log"],
            relevance="Direct evidence of the service failure",
        )
        assert req.investigation_id == inv.investigation_id
        assert req.target_agent_id == "suspect-01"
