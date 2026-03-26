"""Tests for dispute.py — dispute lifecycle."""

import pytest
from agent_justice_protocol.schema import (
    AgentReference,
    ArbitrationDecision,
    DisputeClaim,
    ForensicFinding,
)
from agent_justice_protocol.dispute import (
    Dispute,
    DisputePhase,
    DisputeResponse,
    ResponseType,
    SettlementOffer,
    create_commitment,
    verify_commitment,
)


def _make_finding():
    f = ForensicFinding(
        investigation_id="inv-001",
        incident_type="service_failure",
        severity="high",
        reported_by=AgentReference(agent_id="reporter-01"),
        description="Test",
    )
    f.compute_hash()
    return f


def _make_claim(finding):
    return DisputeClaim(
        claimant=AgentReference(agent_id="claimant-01"),
        respondent=AgentReference(agent_id="respondent-01"),
        finding_id=finding.finding_id,
        finding_hash=finding.finding_hash,
        harm_type="financial",
        harm_description="Lost revenue",
        requested_remediation_type="compensation",
        quantified_amount=5000.0,
    )


class TestCommitReveal:
    def test_create_and_verify(self):
        content = {"evidence": ["e1", "e2"]}
        nonce = "random-nonce-123"
        commitment = create_commitment(content, nonce)
        assert verify_commitment(commitment, content, nonce)

    def test_wrong_nonce_fails(self):
        content = {"evidence": ["e1"]}
        commitment = create_commitment(content, "correct-nonce")
        assert not verify_commitment(commitment, content, "wrong-nonce")

    def test_wrong_content_fails(self):
        commitment = create_commitment("original", "nonce")
        assert not verify_commitment(commitment, "tampered", "nonce")


class TestDispute:
    def test_create_dispute(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        assert dispute.dispute_id
        assert dispute.phase == DisputePhase.CLAIM_FILED
        assert dispute.is_active

    def test_finding_mismatch_rejected(self):
        finding = _make_finding()
        claim = DisputeClaim(
            claimant=AgentReference(agent_id="c"),
            respondent=AgentReference(agent_id="r"),
            finding_id="wrong-id",
            finding_hash="wrong-hash",
            harm_type="financial",
            harm_description="x",
            requested_remediation_type="compensation",
        )
        with pytest.raises(ValueError, match="finding"):
            Dispute(claim, finding)

    def test_submit_response_contest(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        response = DisputeResponse(
            dispute_id=dispute.dispute_id,
            respondent=AgentReference(agent_id="respondent-01"),
            response_type="contest",
            explanation="We did nothing wrong",
        )
        dispute.submit_response(response)
        assert dispute.phase == DisputePhase.EVIDENCE_EXCHANGE

    def test_submit_response_accept(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        response = DisputeResponse(
            dispute_id=dispute.dispute_id,
            respondent=AgentReference(agent_id="respondent-01"),
            response_type="accept",
        )
        dispute.submit_response(response)
        assert dispute.phase == DisputePhase.TIER_SELECTION

    def test_select_tier(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        tier = dispute.select_tier()
        assert tier == "peer_arbitration"  # $5000, no ASA

    def test_commit_reveal_evidence(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        content = {"my_evidence": "important"}
        nonce = "secret-nonce"
        commitment = dispute.submit_commitment("claimant-01", content, nonce)
        assert commitment.commitment_hash
        assert dispute.reveal_commitment("claimant-01", content, nonce)
        assert not dispute.reveal_commitment("claimant-01", content, "wrong")

    def test_settlement(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        offer = SettlementOffer(
            dispute_id=dispute.dispute_id,
            proposer=AgentReference(agent_id="respondent-01"),
            terms="Pay $2000 and apologize",
            compensation_amount=2000.0,
        )
        dispute.propose_settlement(offer)
        assert len(dispute.settlement_offers) == 1
        accepted = dispute.accept_settlement(offer.offer_id)
        assert accepted is not None
        assert dispute.phase == DisputePhase.SETTLED
        assert not dispute.is_active

    def test_withdrawal(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        phase = dispute.withdraw()
        assert phase == DisputePhase.WITHDRAWN
        assert not dispute.is_active

    def test_cannot_respond_after_decided(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        decision = ArbitrationDecision(
            dispute_id=dispute.dispute_id,
            claim_id=claim.claim_id,
            resolution_tier="automated",
            respondent_fault_pct=100,
            claimant_fault_pct=0,
            no_fault_pct=0,
        )
        dispute.record_decision(decision)
        assert dispute.phase == DisputePhase.DECIDED
        with pytest.raises(ValueError, match="inactive"):
            dispute.submit_response(DisputeResponse(
                dispute_id=dispute.dispute_id,
                respondent=AgentReference(agent_id="r"),
                response_type="contest",
            ))

    def test_adverse_inference(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        # Simulate default response
        dispute.response = DisputeResponse(
            dispute_id=dispute.dispute_id,
            respondent=AgentReference(agent_id="r"),
            response_type="default",
        )
        inferences = dispute.check_adverse_inference()
        assert any("default" in i.lower() for i in inferences)

    def test_to_dict(self):
        finding = _make_finding()
        claim = _make_claim(finding)
        dispute = Dispute(claim, finding)
        d = dispute.to_dict()
        assert d["dispute_id"] == dispute.dispute_id
        assert d["phase"] == "claim_filed"
