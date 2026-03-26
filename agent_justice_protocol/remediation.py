"""Remedy types and enforcement tracking.

Implements the remediation portion of Section 6.6 (Decision Schema)
and Section 7.6 (Risk Profile Updates) of the AJP whitepaper.

Remedy types: compensation, service_credit, reputation_adjustment,
behavioral_restriction, apology, human_escalation, referral, no_action.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schema import (
    ArbitrationDecision,
    REMEDIATION_TYPES,
    _now_iso,
    _uuid,
)


# ---------------------------------------------------------------------------
# Remediation Order
# ---------------------------------------------------------------------------

@dataclass
class RemediationOrder:
    """A specific remediation action arising from a dispute decision."""
    decision_id: str
    respondent_id: str
    remediation_type: str
    details: str
    compensation_amount: Optional[float] = None
    compensation_currency: str = "USD"
    reputation_dimensions: List[str] = field(default_factory=list)
    reputation_adjustment: float = 0.0
    behavioral_requirements: List[str] = field(default_factory=list)
    deadline: str = ""
    order_id: str = ""
    created_at: str = ""
    status: str = "pending"  # pending, in_progress, completed, expired, appealed

    def __post_init__(self) -> None:
        if not self.order_id:
            self.order_id = _uuid()
        if not self.created_at:
            self.created_at = _now_iso()
        if self.remediation_type not in REMEDIATION_TYPES:
            raise ValueError(
                f"remediation_type must be one of {REMEDIATION_TYPES}"
            )

    def mark_completed(self) -> None:
        self.status = "completed"

    def mark_expired(self) -> None:
        self.status = "expired"

    def mark_appealed(self) -> None:
        self.status = "appealed"

    @property
    def is_pending(self) -> bool:
        return self.status in ("pending", "in_progress")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "decision_id": self.decision_id,
            "respondent_id": self.respondent_id,
            "remediation_type": self.remediation_type,
            "details": self.details,
            "compensation": {
                "amount": self.compensation_amount,
                "currency": self.compensation_currency,
            },
            "reputation_impact": {
                "dimensions": self.reputation_dimensions,
                "adjustment": self.reputation_adjustment,
            },
            "behavioral_requirements": self.behavioral_requirements,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RemediationOrder":
        comp = d.get("compensation", {})
        rep = d.get("reputation_impact", {})
        return cls(
            order_id=d.get("order_id", ""),
            decision_id=d["decision_id"],
            respondent_id=d["respondent_id"],
            remediation_type=d["remediation_type"],
            details=d.get("details", ""),
            compensation_amount=comp.get("amount"),
            compensation_currency=comp.get("currency", "USD"),
            reputation_dimensions=rep.get("dimensions", []),
            reputation_adjustment=rep.get("adjustment", 0.0),
            behavioral_requirements=d.get("behavioral_requirements", []),
            deadline=d.get("deadline", ""),
            created_at=d.get("created_at", ""),
            status=d.get("status", "pending"),
        )


# ---------------------------------------------------------------------------
# Remediation Tracker
# ---------------------------------------------------------------------------

class RemediationTracker:
    """Tracks remediation orders and their compliance status."""

    def __init__(self) -> None:
        self._orders: List[RemediationOrder] = []

    def create_from_decision(
        self,
        decision: ArbitrationDecision,
        respondent_id: str,
        deadline: str = "",
    ) -> RemediationOrder:
        """Create a remediation order from an arbitration decision."""
        order = RemediationOrder(
            decision_id=decision.decision_id,
            respondent_id=respondent_id,
            remediation_type=decision.remediation_type,
            details=decision.remediation_details,
            compensation_amount=decision.compensation_amount,
            compensation_currency=decision.compensation_currency,
            reputation_dimensions=decision.dimensions_affected,
            reputation_adjustment=decision.respondent_rep_adjustment,
            deadline=deadline,
        )
        self._orders.append(order)
        return order

    def add_order(self, order: RemediationOrder) -> None:
        self._orders.append(order)

    def get_orders_for(self, respondent_id: str) -> List[RemediationOrder]:
        """Get all remediation orders for a respondent."""
        return [o for o in self._orders if o.respondent_id == respondent_id]

    def get_pending_orders(self, respondent_id: str) -> List[RemediationOrder]:
        """Get pending remediation orders for a respondent."""
        return [
            o for o in self._orders
            if o.respondent_id == respondent_id and o.is_pending
        ]

    def complete_order(self, order_id: str) -> Optional[RemediationOrder]:
        """Mark a remediation order as completed."""
        for o in self._orders:
            if o.order_id == order_id:
                o.mark_completed()
                return o
        return None

    def compliance_rate(self, respondent_id: str) -> float:
        """Calculate remediation compliance rate for an agent.

        Returns float 0-1 representing the fraction of completed orders.
        Used by risk.py for recovery_capability scoring.
        """
        orders = self.get_orders_for(respondent_id)
        if not orders:
            return 1.0  # No orders = full compliance
        completed = sum(1 for o in orders if o.status == "completed")
        return completed / len(orders)

    def total_compensation_owed(self, respondent_id: str) -> float:
        """Total pending compensation amount for a respondent."""
        return sum(
            o.compensation_amount or 0.0
            for o in self.get_pending_orders(respondent_id)
        )

    @property
    def all_orders(self) -> List[RemediationOrder]:
        return list(self._orders)

    def export_orders(self) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._orders]

    def load_orders(self, records: List[Dict[str, Any]]) -> None:
        self._orders = [RemediationOrder.from_dict(r) for r in records]
