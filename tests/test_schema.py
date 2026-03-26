"""Tests for schema.py — data structures and serialization."""

import pytest
from agent_justice_protocol.schema import (
    AgentReference,
    ArbitrationDecision,
    ArbitratorVote,
    CausalIndicator,
    CustodyEntry,
    DisputeClaim,
    EvidenceRecord,
    FaultAllocation,
    ForensicFinding,
    RiskProfile,
    TimelineEvent,
    risk_level_for_score,
    PROVENANCE_TIERS,
)


class TestAgentReference:
    def test_create_basic(self):
        ref = AgentReference(agent_id="agent-001")
        assert ref.agent_id == "agent-001"
        assert ref.identity_system == "uri"

    def test_roundtrip(self):
        ref = AgentReference(
            agent_id="agent-001",
            identity_system="coc",
            identity_proof="proof-123",
            operational_age_days=90,
            arp_composite=0.85,
            arp_confidence=0.92,
        )
        d = ref.to_dict()
        ref2 = AgentReference.from_dict(d)
        assert ref2.agent_id == "agent-001"
        assert ref2.identity_system == "coc"
        assert ref2.arp_composite == 0.85

    def test_invalid_identity_system(self):
        with pytest.raises(ValueError, match="identity_system"):
            AgentReference(agent_id="a", identity_system="invalid")


class TestEvidenceRecord:
    def test_create_and_weight(self):
        ev = EvidenceRecord(
            evidence_type="chain_entry",
            provenance_tier=1,
            source_agent_id="agent-001",
            content={"action": "test"},
        )
        assert ev.weight == 1.0
        assert ev.evidence_id  # auto-generated

    def test_tier_weights(self):
        for tier, info in PROVENANCE_TIERS.items():
            ev = EvidenceRecord(
                evidence_type="telemetry",
                provenance_tier=tier,
                source_agent_id="a",
                content="x",
            )
            assert ev.weight == info["weight"]

    def test_verify_content_hash(self):
        ev = EvidenceRecord(
            evidence_type="self_report",
            provenance_tier=4,
            source_agent_id="a",
            content="original content",
        )
        assert ev.verify_content_hash()

    def test_roundtrip(self):
        ev = EvidenceRecord(
            evidence_type="interaction_log",
            provenance_tier=2,
            source_agent_id="agent-001",
            content={"msg": "hello"},
            chain_of_custody=[CustodyEntry(custodian="investigator-1")],
        )
        d = ev.to_dict()
        ev2 = EvidenceRecord.from_dict(d)
        assert ev2.evidence_id == ev.evidence_id
        assert ev2.provenance_tier == 2
        assert len(ev2.chain_of_custody) == 1

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="evidence_type"):
            EvidenceRecord(
                evidence_type="invalid",
                provenance_tier=1,
                source_agent_id="a",
                content="x",
            )

    def test_invalid_tier(self):
        with pytest.raises(ValueError, match="provenance_tier"):
            EvidenceRecord(
                evidence_type="telemetry",
                provenance_tier=5,
                source_agent_id="a",
                content="x",
            )


class TestForensicFinding:
    def _make_finding(self):
        return ForensicFinding(
            investigation_id="inv-001",
            incident_type="service_failure",
            severity="high",
            reported_by=AgentReference(agent_id="reporter-01"),
            description="Test incident",
            subjects=[AgentReference(agent_id="suspect-01")],
            total_evidence_items=5,
            tier_1_count=2,
        )

    def test_create(self):
        f = self._make_finding()
        assert f.finding_id
        assert f.incident_type == "service_failure"

    def test_hash_roundtrip(self):
        f = self._make_finding()
        f.compute_hash()
        assert f.finding_hash
        assert f.verify_hash()

    def test_serialization(self):
        f = self._make_finding()
        f.compute_hash()
        d = f.to_dict()
        f2 = ForensicFinding.from_dict(d)
        assert f2.finding_id == f.finding_id
        assert f2.finding_hash == f.finding_hash

    def test_invalid_incident_type(self):
        with pytest.raises(ValueError, match="incident_type"):
            ForensicFinding(
                investigation_id="inv",
                incident_type="invalid",
                severity="high",
                reported_by=AgentReference(agent_id="a"),
                description="x",
            )


class TestDisputeClaim:
    def test_create_and_tier_selection(self):
        claim = DisputeClaim(
            claimant=AgentReference(agent_id="claimant-01"),
            respondent=AgentReference(agent_id="respondent-01"),
            finding_id="finding-001",
            finding_hash="abc123",
            harm_type="financial",
            harm_description="Lost revenue",
            requested_remediation_type="compensation",
            quantified_amount=500.0,
            asa_id="asa-001",
        )
        assert claim.select_tier() == "automated"  # <$1K with ASA

    def test_tier_peer(self):
        claim = DisputeClaim(
            claimant=AgentReference(agent_id="c"),
            respondent=AgentReference(agent_id="r"),
            finding_id="f",
            finding_hash="h",
            harm_type="financial",
            harm_description="x",
            requested_remediation_type="compensation",
            quantified_amount=5000.0,
        )
        assert claim.select_tier() == "peer_arbitration"

    def test_tier_human(self):
        claim = DisputeClaim(
            claimant=AgentReference(agent_id="c"),
            respondent=AgentReference(agent_id="r"),
            finding_id="f",
            finding_hash="h",
            harm_type="financial",
            harm_description="x",
            requested_remediation_type="human_escalation",
            quantified_amount=100000.0,
        )
        assert claim.select_tier() == "human_escalation"

    def test_hash(self):
        claim = DisputeClaim(
            claimant=AgentReference(agent_id="c"),
            respondent=AgentReference(agent_id="r"),
            finding_id="f",
            finding_hash="h",
            harm_type="financial",
            harm_description="x",
            requested_remediation_type="compensation",
        )
        claim.compute_hash()
        assert claim.verify_hash()


class TestArbitrationDecision:
    def test_create(self):
        decision = ArbitrationDecision(
            dispute_id="d-001",
            claim_id="c-001",
            resolution_tier="peer_arbitration",
            claimant_fault_pct=20,
            respondent_fault_pct=80,
            no_fault_pct=0,
        )
        assert decision.decision_id

    def test_fault_must_sum_100(self):
        with pytest.raises(ValueError, match="sum to 100"):
            ArbitrationDecision(
                dispute_id="d",
                claim_id="c",
                resolution_tier="automated",
                claimant_fault_pct=50,
                respondent_fault_pct=30,
                no_fault_pct=10,
            )

    def test_majority_vote(self):
        decision = ArbitrationDecision(
            dispute_id="d",
            claim_id="c",
            resolution_tier="peer_arbitration",
            claimant_fault_pct=0,
            respondent_fault_pct=100,
            no_fault_pct=0,
            arbitrators=[
                ArbitratorVote(agent_id="a1", vote="for_claimant"),
                ArbitratorVote(agent_id="a2", vote="for_claimant"),
                ArbitratorVote(agent_id="a3", vote="for_respondent"),
            ],
        )
        assert decision.majority_vote == "for_claimant"

    def test_hash(self):
        decision = ArbitrationDecision(
            dispute_id="d",
            claim_id="c",
            resolution_tier="automated",
            claimant_fault_pct=0,
            respondent_fault_pct=100,
            no_fault_pct=0,
        )
        decision.compute_hash()
        assert decision.verify_hash()


class TestRiskProfile:
    def test_risk_level(self):
        profile = RiskProfile(
            subject=AgentReference(agent_id="a"),
            overall_score=250,
        )
        assert profile.risk_level == "low"

    def test_risk_levels_mapping(self):
        cases = [
            (50, "minimal"), (200, "low"), (400, "moderate"),
            (600, "elevated"), (800, "high"), (950, "critical"),
        ]
        for score, expected in cases:
            assert risk_level_for_score(score) == expected


class TestCausalIndicator:
    def test_invalid_type(self):
        with pytest.raises(ValueError):
            CausalIndicator(
                indicator_type="invalid",
                description="x",
                agent_id="a",
            )

class TestFaultAllocation:
    def test_invalid_percentage(self):
        with pytest.raises(ValueError, match="fault_percentage"):
            FaultAllocation(agent_id="a", fault_percentage=101)

    def test_invalid_basis(self):
        with pytest.raises(ValueError, match="basis"):
            FaultAllocation(agent_id="a", fault_percentage=50, basis="invalid")
