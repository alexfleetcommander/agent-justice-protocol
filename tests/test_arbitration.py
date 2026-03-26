"""Tests for arbitration.py — panel selection and vote aggregation."""

import pytest
from agent_justice_protocol.schema import AgentReference, ArbitratorVote
from agent_justice_protocol.arbitration import (
    ArbitratorCandidate,
    ArbitratorPool,
    aggregate_votes,
    render_decision,
)


def _make_candidate(agent_id, age=120, compliance=85.0, arbs=10, operator="op1"):
    return ArbitratorCandidate(
        agent=AgentReference(agent_id=agent_id),
        operational_age_days=age,
        protocol_compliance=compliance,
        completed_arbitrations=arbs,
        operator_id=operator,
    )


class TestArbitratorCandidate:
    def test_arbweight(self):
        c = _make_candidate("arb-01", age=120, compliance=85.0, arbs=10)
        w = c.arbweight
        assert w > 0
        # log2(121) * log2(11) * 0.85 ≈ 6.92 * 3.46 * 0.85 ≈ 20.3
        assert 15 < w < 25

    def test_zero_arbitrations(self):
        c = _make_candidate("arb-01", arbs=0)
        # log2(1) = 0, so arbweight should be 0
        assert c.arbweight == 0.0


class TestArbitratorPool:
    def _build_pool(self, n=10, bootstrapping=False):
        pool = ArbitratorPool(bootstrapping=bootstrapping, seed=42)
        for i in range(n):
            pool.add_candidate(_make_candidate(
                f"arb-{i:02d}",
                age=100 + i * 10,
                compliance=75.0 + i,
                arbs=5 + i,
                operator=f"op-{i}",
            ))
        return pool

    def test_eligible_basic(self):
        pool = self._build_pool()
        eligible = pool.eligible_candidates("claimant-01", "respondent-01")
        assert len(eligible) == 10

    def test_conflict_of_interest(self):
        pool = self._build_pool(5)
        # Add a candidate that has rated one of the parties
        c = _make_candidate("arb-conflict", operator="op-unique")
        c.rating_partners = ["claimant-01"]
        pool.add_candidate(c)
        eligible = pool.eligible_candidates("claimant-01", "respondent-01")
        assert all(e.agent.agent_id != "arb-conflict" for e in eligible)

    def test_same_operator_excluded(self):
        pool = self._build_pool(5)
        eligible = pool.eligible_candidates(
            "claimant-01", "respondent-01",
            claimant_operator="op-0",
        )
        assert all(e.operator_id != "op-0" for e in eligible)

    def test_party_excluded(self):
        pool = self._build_pool(5)
        eligible = pool.eligible_candidates("arb-00", "respondent-01")
        assert all(e.agent.agent_id != "arb-00" for e in eligible)

    def test_select_panel(self):
        pool = self._build_pool(10)
        panel = pool.select_panel("claimant-01", "respondent-01")
        assert len(panel) == 3
        # All different
        ids = [c.agent.agent_id for c in panel]
        assert len(set(ids)) == 3

    def test_insufficient_candidates(self):
        pool = ArbitratorPool()
        pool.add_candidate(_make_candidate("arb-01"))
        with pytest.raises(ValueError, match="Insufficient"):
            pool.select_panel("claimant", "respondent")

    def test_bootstrapping_mode(self):
        pool = ArbitratorPool(bootstrapping=True, seed=42)
        # Add candidates with 0 completed arbitrations (normally ineligible)
        for i in range(5):
            pool.add_candidate(_make_candidate(
                f"arb-{i}", age=100, compliance=80.0, arbs=0,
                operator=f"op-{i}",
            ))
        # Should work in bootstrapping mode
        panel = pool.select_panel("claimant", "respondent")
        assert len(panel) == 3

    def test_bootstrapping_off_rejects_low_arbs(self):
        pool = ArbitratorPool(bootstrapping=False)
        for i in range(5):
            pool.add_candidate(_make_candidate(
                f"arb-{i}", age=100, compliance=80.0, arbs=2,
                operator=f"op-{i}",
            ))
        with pytest.raises(ValueError, match="Insufficient"):
            pool.select_panel("claimant", "respondent")

    def test_age_requirement(self):
        pool = ArbitratorPool(seed=42)
        for i in range(5):
            pool.add_candidate(_make_candidate(
                f"arb-{i}", age=30, compliance=80.0, arbs=10,
                operator=f"op-{i}",
            ))
        eligible = pool.eligible_candidates("c", "r")
        assert len(eligible) == 0


class TestVoteAggregation:
    def test_majority(self):
        votes = [
            ArbitratorVote(agent_id="a1", vote="for_claimant"),
            ArbitratorVote(agent_id="a2", vote="for_claimant"),
            ArbitratorVote(agent_id="a3", vote="for_respondent"),
        ]
        result = aggregate_votes(votes)
        assert result["majority_vote"] == "for_claimant"
        assert not result["unanimous"]
        assert "a3" in result["dissenting"]

    def test_unanimous(self):
        votes = [
            ArbitratorVote(agent_id="a1", vote="for_respondent"),
            ArbitratorVote(agent_id="a2", vote="for_respondent"),
            ArbitratorVote(agent_id="a3", vote="for_respondent"),
        ]
        result = aggregate_votes(votes)
        assert result["unanimous"]
        assert result["dissenting"] == []

    def test_empty_votes(self):
        result = aggregate_votes([])
        assert result["majority_vote"] == "abstain"


class TestRenderDecision:
    def test_basic_decision(self):
        votes = [
            ArbitratorVote(agent_id="a1", vote="for_claimant", arbweight_at_decision=5.0),
            ArbitratorVote(agent_id="a2", vote="for_claimant", arbweight_at_decision=4.0),
            ArbitratorVote(agent_id="a3", vote="for_respondent", arbweight_at_decision=3.0),
        ]
        decision = render_decision(
            dispute_id="d-001",
            claim_id="c-001",
            votes=votes,
            findings_of_fact=[{"statement": "Agent failed", "confidence": 0.9}],
            claimant_fault_pct=0,
            respondent_fault_pct=100,
            no_fault_pct=0,
            fault_basis="Respondent clearly at fault",
            remediation_type="compensation",
            compensation_amount=5000.0,
        )
        assert decision.decision_id
        assert decision.decision_hash
        assert decision.verify_hash()
        assert decision.resolution_tier == "peer_arbitration"
        assert len(decision.dissenting_opinions) == 1
