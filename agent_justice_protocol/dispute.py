"""Dispute Resolution — filing, response, and arbitration workflow.

Implements Module 2 (Section 6) of the AJP whitepaper:
- Dispute lifecycle (Section 6.2): filing, response, evidence exchange,
  tier selection, arbitration, decision
- Tiered system (Section 6.4): Tier 1 (<$1K automated), Tier 2 (peer),
  Tier 3 (>$50K human escalation)
- Commit-reveal protocol (Section 6.5)
- Adverse inference (Section 6.7)
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .schema import (
    AgentReference,
    ArbitrationDecision,
    DisputeClaim,
    ForensicFinding,
    _content_hash,
    _now_iso,
    _uuid,
)


# ---------------------------------------------------------------------------
# Dispute phases and response types
# ---------------------------------------------------------------------------

class DisputePhase(Enum):
    CLAIM_FILED = "claim_filed"
    RESPONSE_PENDING = "response_pending"
    EVIDENCE_EXCHANGE = "evidence_exchange"
    TIER_SELECTION = "tier_selection"
    ARBITRATION = "arbitration"
    DECIDED = "decided"
    WITHDRAWN = "withdrawn"
    SETTLED = "settled"


class ResponseType(Enum):
    ACCEPT = "accept"
    CONTEST = "contest"
    DEFAULT = "default"  # No response within window


# Default windows (Section 6.2)
AGENT_RESPONSE_HOURS = 72
OPERATOR_RESPONSE_DAYS = 14
AGENT_EVIDENCE_HOURS = 48
OPERATOR_EVIDENCE_DAYS = 7

# Tier thresholds (Section 6.4)
TIER_1_MAX_VALUE = 1000.0
TIER_3_MIN_VALUE = 50000.0


# ---------------------------------------------------------------------------
# Commit-Reveal (Section 6.5)
# ---------------------------------------------------------------------------

@dataclass
class Commitment:
    """A cryptographic commitment for blind evidence/decision submission."""
    party_id: str
    commitment_hash: str  # SHA-256(content || nonce)
    committed_at: str = ""

    def __post_init__(self) -> None:
        if not self.committed_at:
            self.committed_at = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "party_id": self.party_id,
            "commitment_hash": self.commitment_hash,
            "committed_at": self.committed_at,
        }


def create_commitment(content: Any, nonce: str) -> str:
    """Create a SHA-256 commitment hash: H(content || nonce)."""
    content_bytes = _content_hash(content).encode("utf-8")
    nonce_bytes = nonce.encode("utf-8")
    return hashlib.sha256(content_bytes + nonce_bytes).hexdigest()


def verify_commitment(
    commitment_hash: str,
    content: Any,
    nonce: str,
) -> bool:
    """Verify that content + nonce match a commitment hash."""
    return create_commitment(content, nonce) == commitment_hash


# ---------------------------------------------------------------------------
# DisputeResponse
# ---------------------------------------------------------------------------

@dataclass
class DisputeResponse:
    """Structured response to a dispute claim (Phase 2)."""
    dispute_id: str
    respondent: AgentReference
    response_type: str  # accept, contest, default
    counter_evidence_ids: List[str] = field(default_factory=list)
    proposed_remediation: str = ""
    explanation: str = ""
    response_id: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.response_id:
            self.response_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()
        valid_types = [rt.value for rt in ResponseType]
        if self.response_type not in valid_types:
            raise ValueError(f"response_type must be one of {valid_types}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "dispute_id": self.dispute_id,
            "respondent": self.respondent.to_dict(),
            "response_type": self.response_type,
            "counter_evidence_ids": self.counter_evidence_ids,
            "proposed_remediation": self.proposed_remediation,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DisputeResponse":
        return cls(
            response_id=d.get("response_id", ""),
            dispute_id=d["dispute_id"],
            respondent=AgentReference.from_dict(d.get("respondent", {"agent_id": "unknown"})),
            response_type=d["response_type"],
            counter_evidence_ids=d.get("counter_evidence_ids", []),
            proposed_remediation=d.get("proposed_remediation", ""),
            explanation=d.get("explanation", ""),
            timestamp=d.get("timestamp", ""),
        )


# ---------------------------------------------------------------------------
# SettlementOffer
# ---------------------------------------------------------------------------

@dataclass
class SettlementOffer:
    """A settlement proposal (alternative to arbitration)."""
    dispute_id: str
    proposer: AgentReference
    terms: str
    compensation_amount: Optional[float] = None
    compensation_currency: str = "USD"
    includes_reputation_impact: bool = False
    confidential_terms: bool = False
    offer_id: str = ""
    timestamp: str = ""
    status: str = "pending"  # pending, accepted, rejected, counter

    def __post_init__(self) -> None:
        if not self.offer_id:
            self.offer_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "dispute_id": self.dispute_id,
            "proposer": self.proposer.to_dict(),
            "terms": self.terms,
            "compensation": {
                "amount": self.compensation_amount,
                "currency": self.compensation_currency,
            },
            "includes_reputation_impact": self.includes_reputation_impact,
            "confidential_terms": self.confidential_terms,
            "timestamp": self.timestamp,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SettlementOffer":
        comp = d.get("compensation", {})
        return cls(
            offer_id=d.get("offer_id", ""),
            dispute_id=d["dispute_id"],
            proposer=AgentReference.from_dict(d.get("proposer", {"agent_id": "unknown"})),
            terms=d.get("terms", ""),
            compensation_amount=comp.get("amount"),
            compensation_currency=comp.get("currency", "USD"),
            includes_reputation_impact=d.get("includes_reputation_impact", False),
            confidential_terms=d.get("confidential_terms", False),
            timestamp=d.get("timestamp", ""),
            status=d.get("status", "pending"),
        )


# ---------------------------------------------------------------------------
# Dispute (lifecycle manager)
# ---------------------------------------------------------------------------

class Dispute:
    """Manages the full lifecycle of a dispute (Section 6.2).

    Usage:
        claim = DisputeClaim(...)
        dispute = Dispute(claim, finding)
        dispute.submit_response(response)
        tier = dispute.select_tier()
        # ... arbitration proceeds via arbitration.py ...
        dispute.record_decision(decision)
    """

    def __init__(
        self,
        claim: DisputeClaim,
        finding: ForensicFinding,
    ) -> None:
        self.dispute_id = _uuid()
        self.claim = claim
        self.finding = finding
        self.phase = DisputePhase.CLAIM_FILED
        self.response: Optional[DisputeResponse] = None
        self.commitments: Dict[str, Commitment] = {}
        self.settlement_offers: List[SettlementOffer] = []
        self.decision: Optional[ArbitrationDecision] = None
        self.selected_tier: Optional[str] = None
        self._filed_at = _now_iso()

        # Validate finding reference
        if claim.finding_id != finding.finding_id:
            raise ValueError(
                f"Claim references finding {claim.finding_id} but "
                f"provided finding has ID {finding.finding_id}"
            )

    @property
    def is_active(self) -> bool:
        return self.phase not in (
            DisputePhase.DECIDED,
            DisputePhase.WITHDRAWN,
            DisputePhase.SETTLED,
        )

    def submit_response(self, response: DisputeResponse) -> None:
        """Record the respondent's response to the claim."""
        if not self.is_active:
            raise ValueError("Cannot respond to an inactive dispute")
        response.dispute_id = self.dispute_id
        self.response = response
        if response.response_type == ResponseType.ACCEPT.value:
            self.phase = DisputePhase.TIER_SELECTION
        else:
            self.phase = DisputePhase.EVIDENCE_EXCHANGE

    def submit_commitment(self, party_id: str, content: Any, nonce: str) -> Commitment:
        """Submit a blind commitment for evidence exchange (Section 6.5)."""
        commitment = Commitment(
            party_id=party_id,
            commitment_hash=create_commitment(content, nonce),
        )
        self.commitments[party_id] = commitment
        return commitment

    def reveal_commitment(
        self, party_id: str, content: Any, nonce: str,
    ) -> bool:
        """Verify and reveal a commitment."""
        if party_id not in self.commitments:
            return False
        return verify_commitment(
            self.commitments[party_id].commitment_hash, content, nonce,
        )

    def select_tier(self) -> str:
        """Auto-select the appropriate resolution tier (Section 6.4)."""
        self.selected_tier = self.claim.select_tier()

        # Override: if respondent accepted, still use selected tier for remediation
        # Override: if finding confidence is low, escalate to at least Tier 2
        finding_confidence = 0.0
        for ci in self.finding.causal_indicators:
            finding_confidence = max(finding_confidence, ci.rule_match_confidence)

        if (
            self.selected_tier == "automated"
            and finding_confidence < 0.9
        ):
            self.selected_tier = "peer_arbitration"

        # Override: default response → at least Tier 2
        if (
            self.response
            and self.response.response_type == ResponseType.DEFAULT.value
        ):
            if self.selected_tier == "automated":
                self.selected_tier = "peer_arbitration"

        self.phase = DisputePhase.TIER_SELECTION
        return self.selected_tier

    def propose_settlement(self, offer: SettlementOffer) -> None:
        """Submit a settlement offer."""
        if not self.is_active:
            raise ValueError("Cannot settle an inactive dispute")
        offer.dispute_id = self.dispute_id
        self.settlement_offers.append(offer)

    def accept_settlement(self, offer_id: str) -> Optional[SettlementOffer]:
        """Accept a settlement offer, ending the dispute."""
        for offer in self.settlement_offers:
            if offer.offer_id == offer_id and offer.status == "pending":
                offer.status = "accepted"
                self.phase = DisputePhase.SETTLED
                return offer
        return None

    def withdraw(self) -> DisputePhase:
        """Claimant withdraws the dispute."""
        if not self.is_active:
            raise ValueError("Cannot withdraw an inactive dispute")
        self.phase = DisputePhase.WITHDRAWN
        return self.phase

    def record_decision(self, decision: ArbitrationDecision) -> None:
        """Record the arbitration decision, completing the dispute."""
        decision.dispute_id = self.dispute_id
        decision.claim_id = self.claim.claim_id
        self.decision = decision
        self.phase = DisputePhase.DECIDED

    def check_adverse_inference(self) -> List[str]:
        """Check for conditions that trigger adverse inference (Section 6.7)."""
        inferences = []
        # No response within window
        if self.response is None and self.phase != DisputePhase.CLAIM_FILED:
            inferences.append(
                "Respondent failed to respond within window — "
                "treated as accepting the claim as filed"
            )
        elif self.response and self.response.response_type == ResponseType.DEFAULT.value:
            inferences.append(
                "Respondent defaulted — assumed claim accepted"
            )
        # Check commitments: if one party didn't commit
        claimant_id = self.claim.claimant.agent_id
        respondent_id = self.claim.respondent.agent_id
        if claimant_id in self.commitments and respondent_id not in self.commitments:
            inferences.append(
                "Respondent did not submit evidence in exchange phase — "
                "assumed no favorable evidence"
            )
        if respondent_id in self.commitments and claimant_id not in self.commitments:
            inferences.append(
                "Claimant did not submit evidence in exchange phase — "
                "assumed no favorable evidence"
            )
        return inferences

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dispute_id": self.dispute_id,
            "phase": self.phase.value,
            "claim": self.claim.to_dict(),
            "finding_id": self.finding.finding_id,
            "response": self.response.to_dict() if self.response else None,
            "selected_tier": self.selected_tier,
            "settlement_offers": [s.to_dict() for s in self.settlement_offers],
            "decision": self.decision.to_dict() if self.decision else None,
            "filed_at": self._filed_at,
        }
