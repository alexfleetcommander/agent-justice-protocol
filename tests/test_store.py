"""Tests for store.py — JSONL persistence."""

import os
import tempfile
import pytest
from agent_justice_protocol.schema import (
    AgentReference,
    ArbitrationDecision,
    DisputeClaim,
    ForensicFinding,
    RiskProfile,
)
from agent_justice_protocol.store import JusticeStore


@pytest.fixture
def tmp_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield JusticeStore(os.path.join(tmpdir, "ajp"))


def _make_finding():
    f = ForensicFinding(
        investigation_id="inv-001",
        incident_type="service_failure",
        severity="high",
        reported_by=AgentReference(agent_id="reporter"),
        description="Test",
        subjects=[AgentReference(agent_id="suspect-01")],
    )
    f.compute_hash()
    return f


def _make_claim():
    c = DisputeClaim(
        claimant=AgentReference(agent_id="claimant-01"),
        respondent=AgentReference(agent_id="respondent-01"),
        finding_id="f-001",
        finding_hash="h",
        harm_type="financial",
        harm_description="Lost revenue",
        requested_remediation_type="compensation",
    )
    c.compute_hash()
    return c


def _make_decision():
    d = ArbitrationDecision(
        dispute_id="d-001",
        claim_id="c-001",
        resolution_tier="automated",
        respondent_fault_pct=100,
        claimant_fault_pct=0,
        no_fault_pct=0,
    )
    d.compute_hash()
    return d


def _make_profile():
    p = RiskProfile(
        subject=AgentReference(agent_id="agent-01"),
        overall_score=250,
    )
    p.compute_hash()
    return p


class TestJusticeStore:
    def test_empty_store(self, tmp_store):
        assert tmp_store.get_findings() == []
        assert tmp_store.get_claims() == []
        assert tmp_store.get_decisions() == []
        assert tmp_store.get_profiles() == []

    def test_append_and_get_finding(self, tmp_store):
        f = _make_finding()
        fid = tmp_store.append_finding(f)
        assert fid == f.finding_id
        findings = tmp_store.get_findings()
        assert len(findings) == 1
        assert findings[0].finding_id == f.finding_id

    def test_get_finding_by_id(self, tmp_store):
        f = _make_finding()
        tmp_store.append_finding(f)
        found = tmp_store.get_finding(f.finding_id)
        assert found is not None
        assert found.finding_id == f.finding_id

    def test_get_finding_not_found(self, tmp_store):
        assert tmp_store.get_finding("nonexistent") is None

    def test_get_findings_for_agent(self, tmp_store):
        f = _make_finding()
        tmp_store.append_finding(f)
        results = tmp_store.get_findings_for("suspect-01")
        assert len(results) == 1
        results2 = tmp_store.get_findings_for("other-agent")
        assert len(results2) == 0

    def test_append_and_get_claim(self, tmp_store):
        c = _make_claim()
        cid = tmp_store.append_claim(c)
        assert cid == c.claim_id
        claims = tmp_store.get_claims()
        assert len(claims) == 1

    def test_claims_by_and_against(self, tmp_store):
        c = _make_claim()
        tmp_store.append_claim(c)
        assert len(tmp_store.get_claims_by("claimant-01")) == 1
        assert len(tmp_store.get_claims_against("respondent-01")) == 1
        assert len(tmp_store.get_claims_by("respondent-01")) == 0

    def test_append_and_get_decision(self, tmp_store):
        d = _make_decision()
        did = tmp_store.append_decision(d)
        assert did == d.decision_id
        decisions = tmp_store.get_decisions()
        assert len(decisions) == 1

    def test_decisions_for_dispute(self, tmp_store):
        d = _make_decision()
        tmp_store.append_decision(d)
        results = tmp_store.get_decisions_for_dispute("d-001")
        assert len(results) == 1

    def test_append_and_get_profile(self, tmp_store):
        p = _make_profile()
        pid = tmp_store.append_profile(p)
        assert pid == p.profile_id
        profiles = tmp_store.get_profiles()
        assert len(profiles) == 1

    def test_latest_profile(self, tmp_store):
        p1 = RiskProfile(
            subject=AgentReference(agent_id="agent-01"),
            overall_score=200,
            generated_at="2026-03-20T10:00:00.000000Z",
        )
        p1.compute_hash()
        p2 = RiskProfile(
            subject=AgentReference(agent_id="agent-01"),
            overall_score=300,
            generated_at="2026-03-21T10:00:00.000000Z",
        )
        p2.compute_hash()
        tmp_store.append_profile(p1)
        tmp_store.append_profile(p2)
        latest = tmp_store.get_latest_profile("agent-01")
        assert latest is not None
        assert latest.overall_score == 300

    def test_stats(self, tmp_store):
        tmp_store.append_finding(_make_finding())
        tmp_store.append_claim(_make_claim())
        stats = tmp_store.stats()
        assert stats["investigations"]["count"] == 1
        assert stats["disputes"]["count"] == 1
        assert stats["decisions"]["count"] == 0
        assert stats["risk_profiles"]["count"] == 0
        assert stats["investigations"]["file_size_bytes"] > 0

    def test_persistence_across_instances(self, tmp_store):
        f = _make_finding()
        tmp_store.append_finding(f)
        # Create new store pointing to same directory
        store2 = JusticeStore(str(tmp_store.directory))
        findings = store2.get_findings()
        assert len(findings) == 1
