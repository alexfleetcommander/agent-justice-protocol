"""Arbitrator selection, panel formation, and vote aggregation.

Implements Section 6.4 (Tier 2: Peer Arbitration) of the AJP whitepaper:
- Arbitrator eligibility criteria
- ArbWeight computation
- Conflict-of-interest checking
- Weighted random panel selection
- Vote aggregation and decision rendering
- Bootstrapping mechanism (Section 6.4 bootstrapping subsection)
"""

import hashlib
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .schema import (
    AgentReference,
    ArbitrationDecision,
    ArbitratorVote,
    _now_iso,
    _uuid,
)


# Eligibility criteria (Section 6.4, Tier 2 table)
MIN_OPERATIONAL_AGE_DAYS = 90
MIN_PROTOCOL_COMPLIANCE = 70
MIN_COMPLETED_ARBITRATIONS = 5
PANEL_SIZE = 3

# Bootstrapping parameters
BOOTSTRAP_DURATION_DAYS = 180
BOOTSTRAP_POOL_THRESHOLD = 50
BOOTSTRAP_GRACE_PERIOD_DAYS = 90
BOOTSTRAP_MIN_ARBITRATIONS_GRACE = 3


@dataclass
class ArbitratorCandidate:
    """An agent that may serve as an arbitrator."""
    agent: AgentReference
    operational_age_days: int = 0
    protocol_compliance: float = 0.0
    completed_arbitrations: int = 0
    operator_id: str = ""
    rating_partners: List[str] = field(default_factory=list)

    @property
    def arbweight(self) -> float:
        """Compute ArbWeight per Section 6.4 selection algorithm.

        ArbWeight = log2(1 + age_days) * log2(1 + arbitrations_completed)
                    * (protocol_compliance / 100)
        """
        age_factor = math.log2(1 + self.operational_age_days)
        arb_factor = math.log2(1 + self.completed_arbitrations)
        compliance_factor = self.protocol_compliance / 100.0
        return age_factor * arb_factor * compliance_factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent.to_dict(),
            "operational_age_days": self.operational_age_days,
            "protocol_compliance": self.protocol_compliance,
            "completed_arbitrations": self.completed_arbitrations,
            "operator_id": self.operator_id,
            "arbweight": round(self.arbweight, 4),
        }


class ArbitratorPool:
    """Manages the pool of eligible arbitrators and panel selection.

    Supports both normal and bootstrapping modes per Section 6.4.
    """

    def __init__(
        self,
        bootstrapping: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        self._candidates: List[ArbitratorCandidate] = []
        self.bootstrapping = bootstrapping
        self._rng = random.Random(seed)

    def add_candidate(self, candidate: ArbitratorCandidate) -> None:
        """Register an arbitrator candidate in the pool."""
        self._candidates.append(candidate)

    @property
    def candidates(self) -> List[ArbitratorCandidate]:
        return list(self._candidates)

    def eligible_candidates(
        self,
        claimant_id: str,
        respondent_id: str,
        claimant_operator: str = "",
        respondent_operator: str = "",
    ) -> List[ArbitratorCandidate]:
        """Filter candidates by eligibility criteria.

        Criteria from Section 6.4:
        1. Operational age >= 90 days
        2. Protocol compliance >= 70
        3. >= 5 completed arbitrations (waived during bootstrap)
        4. No conflict of interest (no ARP ratings with either party)
        5. Different operator from both parties
        """
        eligible = []
        for c in self._candidates:
            # Age check
            if c.operational_age_days < MIN_OPERATIONAL_AGE_DAYS:
                continue
            # Compliance check
            if c.protocol_compliance < MIN_PROTOCOL_COMPLIANCE:
                continue
            # Arbitration count (waived during bootstrapping)
            if (
                not self.bootstrapping
                and c.completed_arbitrations < MIN_COMPLETED_ARBITRATIONS
            ):
                continue
            # Conflict of interest: no ARP ratings exchanged with either party
            if claimant_id in c.rating_partners or respondent_id in c.rating_partners:
                continue
            # Same operator check
            if c.operator_id and (
                c.operator_id == claimant_operator
                or c.operator_id == respondent_operator
            ):
                continue
            # Cannot be a party to the dispute
            if c.agent.agent_id in (claimant_id, respondent_id):
                continue
            eligible.append(c)
        return eligible

    def select_panel(
        self,
        claimant_id: str,
        respondent_id: str,
        claimant_operator: str = "",
        respondent_operator: str = "",
        panel_size: int = PANEL_SIZE,
    ) -> List[ArbitratorCandidate]:
        """Select an arbitration panel using weighted random sampling.

        Per Section 6.4: weight candidates by ArbWeight, select top N
        by weighted random (higher weight = higher probability, not
        deterministic).

        Raises ValueError if insufficient eligible candidates.
        """
        eligible = self.eligible_candidates(
            claimant_id, respondent_id,
            claimant_operator, respondent_operator,
        )
        if len(eligible) < panel_size:
            raise ValueError(
                f"Insufficient eligible arbitrators: need {panel_size}, "
                f"have {len(eligible)}. "
                + (
                    "Consider enabling bootstrapping mode."
                    if not self.bootstrapping
                    else "Pool is too small even in bootstrapping mode."
                )
            )

        # Weighted random sampling without replacement
        weights = [max(c.arbweight, 0.01) for c in eligible]
        selected: List[ArbitratorCandidate] = []
        remaining = list(zip(eligible, weights))

        for _ in range(panel_size):
            total = sum(w for _, w in remaining)
            r = self._rng.uniform(0, total)
            cumulative = 0.0
            for i, (candidate, weight) in enumerate(remaining):
                cumulative += weight
                if cumulative >= r:
                    selected.append(candidate)
                    remaining.pop(i)
                    break

        return selected


# ---------------------------------------------------------------------------
# Vote Aggregation
# ---------------------------------------------------------------------------

def aggregate_votes(votes: List[ArbitratorVote]) -> Dict[str, Any]:
    """Aggregate arbitrator votes and determine the majority decision.

    Returns dict with:
    - majority_vote: the winning vote
    - vote_counts: tally per option
    - unanimous: whether all votes agree
    - dissenting: list of dissenting arbitrator IDs
    """
    counts: Dict[str, int] = {}
    for v in votes:
        counts[v.vote] = counts.get(v.vote, 0) + 1

    majority = max(counts, key=lambda k: counts[k]) if counts else "abstain"
    dissenting = [v.agent_id for v in votes if v.vote != majority]

    return {
        "majority_vote": majority,
        "vote_counts": counts,
        "unanimous": len(set(v.vote for v in votes)) <= 1,
        "dissenting": dissenting,
    }


def render_decision(
    dispute_id: str,
    claim_id: str,
    votes: List[ArbitratorVote],
    findings_of_fact: List[Dict[str, Any]],
    claimant_fault_pct: int,
    respondent_fault_pct: int,
    no_fault_pct: int,
    fault_basis: str,
    remediation_type: str = "no_action",
    remediation_details: str = "",
    compensation_amount: Optional[float] = None,
    compensation_currency: str = "USD",
    respondent_rep_adjustment: float = 0.0,
    claimant_rep_adjustment: float = 0.0,
    dimensions_affected: Optional[List[str]] = None,
    precedent_tags: Optional[List[str]] = None,
    appeal_hours: int = 336,  # 14 days default
) -> ArbitrationDecision:
    """Render a complete arbitration decision from votes and findings."""
    agg = aggregate_votes(votes)
    dissenting_opinions = [
        {"arbitrator_id": aid, "dissent": f"Voted {next(v.vote for v in votes if v.agent_id == aid)}"}
        for aid in agg["dissenting"]
    ]

    from datetime import datetime, timedelta, timezone
    expires = (
        datetime.now(timezone.utc) + timedelta(hours=appeal_hours)
    ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Determine escalation tier
    resolution_tier = "peer_arbitration"
    escalation_tier = "human_escalation"

    decision = ArbitrationDecision(
        dispute_id=dispute_id,
        claim_id=claim_id,
        resolution_tier=resolution_tier,
        arbitrators=votes,
        findings_of_fact=findings_of_fact,
        claimant_fault_pct=claimant_fault_pct,
        respondent_fault_pct=respondent_fault_pct,
        no_fault_pct=no_fault_pct,
        fault_basis=fault_basis,
        remediation_type=remediation_type,
        remediation_details=remediation_details,
        compensation_amount=compensation_amount,
        compensation_currency=compensation_currency,
        respondent_rep_adjustment=respondent_rep_adjustment,
        claimant_rep_adjustment=claimant_rep_adjustment,
        dimensions_affected=dimensions_affected or [],
        precedent_tags=precedent_tags or [],
        dissenting_opinions=dissenting_opinions,
        appeal_window_expires=expires,
        escalation_tier=escalation_tier,
    )
    decision.compute_hash()
    return decision
