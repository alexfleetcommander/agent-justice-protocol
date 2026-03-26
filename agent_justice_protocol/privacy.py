"""Anti-fishing enforcement and evidence scoping validation.

Implements Section 5.7 Rules 5 and 5a of the AJP whitepaper:
- Rule 5: Per-initiator investigation limit (>2 targeting same respondent
  within 90 days triggers Tier 2 approval requirement)
- Rule 5a: Per-respondent volume tracking (>5 investigations targeting
  same agent within 90 days regardless of initiator)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .evidence import _parse_iso


# Thresholds from whitepaper Section 5.7
PER_INITIATOR_LIMIT = 2  # Max investigations same initiator→same respondent in 90 days
PER_RESPONDENT_LIMIT = 5  # Max investigations targeting same respondent in 90 days
TRACKING_WINDOW_DAYS = 90


@dataclass
class InvestigationRecord:
    """Minimal record for tracking investigation volumes."""
    investigation_id: str
    initiator_id: str
    respondent_id: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "initiator_id": self.initiator_id,
            "respondent_id": self.respondent_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InvestigationRecord":
        return cls(**d)


class PrivacyGuard:
    """Enforces anti-fishing rules for investigation requests.

    Tracks investigation volumes per-initiator and per-respondent
    to prevent weaponization of the forensic investigation process.
    """

    def __init__(self, window_days: int = TRACKING_WINDOW_DAYS) -> None:
        self.window_days = window_days
        self._records: List[InvestigationRecord] = []

    def record_investigation(
        self,
        investigation_id: str,
        initiator_id: str,
        respondent_id: str,
        timestamp: Optional[str] = None,
    ) -> None:
        """Record an investigation for tracking purposes."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        self._records.append(InvestigationRecord(
            investigation_id=investigation_id,
            initiator_id=initiator_id,
            respondent_id=respondent_id,
            timestamp=timestamp,
        ))

    def _recent_records(
        self,
        reference_time: Optional[str] = None,
    ) -> List[InvestigationRecord]:
        """Get records within the tracking window."""
        if reference_time:
            ref_dt = _parse_iso(reference_time)
        else:
            ref_dt = datetime.now(timezone.utc)
        cutoff = ref_dt - timedelta(days=self.window_days)
        return [
            r for r in self._records
            if _parse_iso(r.timestamp) >= cutoff
        ]

    def check_per_initiator(
        self,
        initiator_id: str,
        respondent_id: str,
        reference_time: Optional[str] = None,
    ) -> Tuple[bool, int]:
        """Check Rule 5: per-initiator limit.

        Returns:
            (requires_approval, count) — True if the investigation
            requires Tier 2 arbitrator panel approval.
        """
        recent = self._recent_records(reference_time)
        count = sum(
            1
            for r in recent
            if r.initiator_id == initiator_id
            and r.respondent_id == respondent_id
        )
        return (count >= PER_INITIATOR_LIMIT, count)

    def check_per_respondent(
        self,
        respondent_id: str,
        reference_time: Optional[str] = None,
    ) -> Tuple[bool, int]:
        """Check Rule 5a: per-respondent volume tracking.

        Returns:
            (requires_approval, count) — True if investigations targeting
            this respondent require Tier 2 approval.
        """
        recent = self._recent_records(reference_time)
        count = sum(
            1
            for r in recent
            if r.respondent_id == respondent_id
        )
        return (count >= PER_RESPONDENT_LIMIT, count)

    def check_investigation(
        self,
        initiator_id: str,
        respondent_id: str,
        reference_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Comprehensive privacy check for a new investigation.

        Returns a dict with:
        - approved: bool — True if investigation can proceed without approval
        - requires_tier2_approval: bool
        - reason: str — why approval is required (if applicable)
        - per_initiator_count: int
        - per_respondent_count: int
        """
        init_blocked, init_count = self.check_per_initiator(
            initiator_id, respondent_id, reference_time
        )
        resp_blocked, resp_count = self.check_per_respondent(
            respondent_id, reference_time
        )

        reasons = []
        if init_blocked:
            reasons.append(
                f"Rule 5: Initiator {initiator_id} has filed "
                f"{init_count} investigations against {respondent_id} "
                f"in the last {self.window_days} days "
                f"(limit: {PER_INITIATOR_LIMIT})"
            )
        if resp_blocked:
            reasons.append(
                f"Rule 5a: Respondent {respondent_id} has been targeted by "
                f"{resp_count} investigations in the last "
                f"{self.window_days} days "
                f"(limit: {PER_RESPONDENT_LIMIT})"
            )

        requires_approval = init_blocked or resp_blocked
        return {
            "approved": not requires_approval,
            "requires_tier2_approval": requires_approval,
            "reason": "; ".join(reasons) if reasons else "No restrictions",
            "per_initiator_count": init_count,
            "per_respondent_count": resp_count,
        }

    def load_records(self, records: List[Dict[str, Any]]) -> None:
        """Load investigation records from serialized form."""
        self._records = [InvestigationRecord.from_dict(r) for r in records]

    def export_records(self) -> List[Dict[str, Any]]:
        """Export all records for persistence."""
        return [r.to_dict() for r in self._records]
