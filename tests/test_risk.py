"""Tests for risk.py — risk scoring engine."""

import pytest
from agent_justice_protocol.schema import (
    AgentReference,
    ArbitrationDecision,
    ForensicFinding,
    RiskProfile,
)
from agent_justice_protocol.risk import (
    RiskEngine,
    population_risk_summary,
    _confidence,
    _loading_factor,
    _temporal_weight,
)


def _make_finding(severity="medium", incident_type="service_failure"):
    f = ForensicFinding(
        investigation_id="inv-001",
        incident_type=incident_type,
        severity=severity,
        reported_by=AgentReference(agent_id="reporter"),
        description="Test incident",
        subjects=[AgentReference(agent_id="suspect-01")],
    )
    f.compute_hash()
    return f


def _make_decision(respondent_fault=80, amount=1000.0):
    return ArbitrationDecision(
        dispute_id="d-001",
        claim_id="c-001",
        resolution_tier="peer_arbitration",
        respondent_fault_pct=respondent_fault,
        claimant_fault_pct=100 - respondent_fault,
        no_fault_pct=0,
        compensation_amount=amount,
    )


class TestConfidence:
    def test_floor(self):
        assert _confidence(0) == 0.05

    def test_growth(self):
        c20 = _confidence(20)
        c100 = _confidence(100)
        c1000 = _confidence(1000)
        assert 0.45 < c20 < 0.55
        assert 0.80 < c100 < 0.90
        assert c1000 > 0.95

    def test_monotonic(self):
        prev = 0.0
        for n in range(0, 1001, 10):
            c = _confidence(n)
            assert c >= prev
            prev = c


class TestLoadingFactor:
    def test_max_loading(self):
        # At minimum confidence (0.05), loading = 10.0
        assert _loading_factor(0.05) == 10.0

    def test_moderate(self):
        # At confidence ~0.5, loading ≈ 1.0
        lf = _loading_factor(0.5)
        assert 0.9 < lf < 1.1


class TestTemporalWeight:
    def test_zero_days(self):
        assert _temporal_weight(0) == 1.0

    def test_decay(self):
        w231 = _temporal_weight(231)
        # Half-life is ~231 days, so weight should be ~0.5
        assert 0.45 < w231 < 0.55

    def test_old(self):
        assert _temporal_weight(1000) < 0.1


class TestRiskEngine:
    def test_clean_agent(self):
        engine = RiskEngine()
        agent = AgentReference(agent_id="clean-agent")
        profile = engine.compute_profile(
            agent=agent,
            findings=[],
            decisions=[],
            total_interactions=100,
        )
        assert profile.overall_score == 0
        assert profile.risk_level == "minimal"
        assert profile.confidence > 0.8

    def test_risky_agent(self):
        engine = RiskEngine()
        agent = AgentReference(agent_id="risky-agent")
        findings = [
            _make_finding(severity="critical"),
            _make_finding(severity="high"),
            _make_finding(severity="high"),
        ]
        decisions = [
            _make_decision(respondent_fault=90, amount=5000),
            _make_decision(respondent_fault=80, amount=3000),
        ]
        profile = engine.compute_profile(
            agent=agent,
            findings=findings,
            decisions=decisions,
            total_interactions=10,
            evidence_provision_rate=0.5,
            adverse_inferences=2,
        )
        assert profile.overall_score > 200
        assert profile.risk_level in ("low", "moderate", "elevated", "high")
        assert profile.findings_count == 3
        assert profile.disputes_count == 2

    def test_actuarial_outputs(self):
        engine = RiskEngine()
        agent = AgentReference(agent_id="agent-x")
        decisions = [
            _make_decision(respondent_fault=100, amount=1000),
            _make_decision(respondent_fault=100, amount=2000),
            _make_decision(respondent_fault=100, amount=5000),
        ]
        profile = engine.compute_profile(
            agent=agent,
            findings=[_make_finding()],
            decisions=decisions,
            total_interactions=100,
        )
        assert profile.expected_loss_rate > 0
        assert profile.loss_p50 > 0
        assert profile.recommended_premium_basis > 0

    def test_profile_hash(self):
        engine = RiskEngine()
        agent = AgentReference(agent_id="agent-hash")
        profile = engine.compute_profile(
            agent=agent,
            findings=[],
            decisions=[],
            total_interactions=50,
        )
        assert profile.profile_hash
        assert profile.verify_hash()

    def test_custom_weights(self):
        custom_weights = {
            "incident_frequency": 0.5,
            "severity_profile": 0.2,
            "fault_history": 0.1,
            "cooperation_score": 0.1,
            "recovery_capability": 0.1,
        }
        engine = RiskEngine(weights=custom_weights)
        agent = AgentReference(agent_id="agent-w")
        profile = engine.compute_profile(
            agent=agent,
            findings=[_make_finding(severity="critical")],
            decisions=[],
            total_interactions=10,
        )
        assert profile.overall_score >= 0

    def test_trend_stable(self):
        engine = RiskEngine()
        agent = AgentReference(agent_id="a")
        profile = engine.compute_profile(agent, [], [], 50)
        assert profile.trend == "stable"


class TestPopulationAnalytics:
    def test_basic_summary(self):
        profiles = [
            RiskProfile(subject=AgentReference(agent_id=f"a{i}"),
                        overall_score=i * 100, agent_class="llm")
            for i in range(5)
        ]
        summary = population_risk_summary(profiles)
        assert summary["total_agents"] == 5
        assert summary["average_score"] == 200.0
        assert summary["median_score"] == 200.0
        assert "llm" in summary["class_averages"]

    def test_empty(self):
        summary = population_risk_summary([])
        assert summary["total_agents"] == 0

    def test_distribution(self):
        profiles = [
            RiskProfile(subject=AgentReference(agent_id="a1"), overall_score=50),
            RiskProfile(subject=AgentReference(agent_id="a2"), overall_score=250),
            RiskProfile(subject=AgentReference(agent_id="a3"), overall_score=950),
        ]
        summary = population_risk_summary(profiles)
        assert summary["risk_distribution"]["minimal"] == 1
        assert summary["risk_distribution"]["low"] == 1
        assert summary["risk_distribution"]["critical"] == 1
