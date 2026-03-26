"""Evidence request and management — temporal scoping, relevance filtering, redaction.

Implements Section 5.7 of the AJP whitepaper:
- Rule 1: Temporal scoping (incident_time +/- 24h default, max +/- 7 days)
- Rule 3: Relevance filtering
- Rule 4: Redaction protocol
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .schema import (
    EvidenceRecord,
    _content_hash,
    _hash_dict,
    _now_iso,
    _uuid,
)


# Maximum evidence request time window: +/- 7 days from incident
MAX_WINDOW_HOURS = 7 * 24  # 168 hours
DEFAULT_WINDOW_HOURS = 24


def _parse_iso(ts: str) -> datetime:
    """Parse ISO-8601 timestamp, tolerant of trailing Z."""
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        # Fallback for formats without timezone
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f").replace(
            tzinfo=timezone.utc
        )


# ---------------------------------------------------------------------------
# EvidenceRequest (Section 5.7 schema extension)
# ---------------------------------------------------------------------------

@dataclass
class EvidenceRequest:
    """A scoped request for evidence from a target agent.

    Enforces Rule 1 (temporal scoping): requests are limited to a time
    window around the incident, default +/- 24 hours, capped at +/- 7 days.
    """
    investigation_id: str
    target_agent_id: str
    incident_time: str
    evidence_types_requested: List[str]
    incident_relevance: str
    approved_by: str = ""
    window_hours: int = DEFAULT_WINDOW_HOURS
    justification: str = ""
    request_id: str = ""
    request_hash: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = _uuid()
        # Enforce Rule 1: cap at MAX_WINDOW_HOURS
        if self.window_hours > MAX_WINDOW_HOURS:
            raise ValueError(
                f"Evidence request window cannot exceed {MAX_WINDOW_HOURS} hours "
                f"(+/- 7 days). Got {self.window_hours} hours."
            )
        if self.window_hours > DEFAULT_WINDOW_HOURS and not self.justification:
            raise ValueError(
                "Extended evidence windows (>{} hours) require justification "
                "(Section 5.7, Rule 1).".format(DEFAULT_WINDOW_HOURS)
            )

    @property
    def time_window_start(self) -> str:
        incident_dt = _parse_iso(self.incident_time)
        start = incident_dt - timedelta(hours=self.window_hours)
        return start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @property
    def time_window_end(self) -> str:
        incident_dt = _parse_iso(self.incident_time)
        end = incident_dt + timedelta(hours=self.window_hours)
        return end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("request_hash", None)
        self.request_hash = _hash_dict(d)
        return self.request_hash

    def is_within_scope(self, evidence_timestamp: str) -> bool:
        """Check if an evidence timestamp falls within the approved window."""
        ev_dt = _parse_iso(evidence_timestamp)
        start = _parse_iso(self.time_window_start)
        end = _parse_iso(self.time_window_end)
        return start <= ev_dt <= end

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "evidence_request": {
                "request_id": self.request_id,
                "investigation_id": self.investigation_id,
                "target_agent": self.target_agent_id,
                "time_window": {
                    "start": self.time_window_start,
                    "end": self.time_window_end,
                    "justification": self.justification,
                },
                "evidence_types_requested": self.evidence_types_requested,
                "incident_relevance": self.incident_relevance,
                "approved_by": self.approved_by,
            },
        }
        if self.request_hash:
            d["evidence_request"]["request_hash"] = self.request_hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvidenceRequest":
        er = d.get("evidence_request", d)
        tw = er.get("time_window", {})
        # Reconstruct window_hours from start/end
        start_str = tw.get("start", "")
        end_str = tw.get("end", "")
        window_hours = DEFAULT_WINDOW_HOURS
        if start_str and end_str:
            try:
                start_dt = _parse_iso(start_str)
                end_dt = _parse_iso(end_str)
                total_hours = (end_dt - start_dt).total_seconds() / 3600
                window_hours = int(total_hours / 2)
            except (ValueError, TypeError):
                pass
        # Reconstruct incident_time as midpoint
        incident_time = ""
        if start_str and end_str:
            try:
                start_dt = _parse_iso(start_str)
                end_dt = _parse_iso(end_str)
                mid = start_dt + (end_dt - start_dt) / 2
                incident_time = mid.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            except (ValueError, TypeError):
                pass
        return cls(
            request_id=er.get("request_id", ""),
            investigation_id=er.get("investigation_id", ""),
            target_agent_id=er.get("target_agent", ""),
            incident_time=incident_time,
            evidence_types_requested=er.get("evidence_types_requested", []),
            incident_relevance=er.get("incident_relevance", ""),
            approved_by=er.get("approved_by", ""),
            window_hours=window_hours,
            justification=tw.get("justification", ""),
            request_hash=er.get("request_hash", ""),
        )


# ---------------------------------------------------------------------------
# Relevance filter (Rule 3)
# ---------------------------------------------------------------------------

# CoC entry types and their relevance criteria
_RELEVANCE_RULES = {
    "DECISION": "Include only if the decision directly relates to the incident.",
    "KNOWLEDGE_ADD": "Include only if the knowledge is directly relevant to the agent's capability to avoid the incident.",
    "SESSION_START": "Include as operational window markers only.",
    "SESSION_END": "Include as operational window markers only.",
}


def filter_relevant_evidence(
    evidence: List[EvidenceRecord],
    request: EvidenceRequest,
) -> List[EvidenceRecord]:
    """Filter evidence items by temporal scope and type relevance.

    Applies Rule 1 (temporal) and Rule 3 (relevance):
    - Only evidence within the approved time window
    - Only evidence types that were requested
    """
    filtered = []
    for item in evidence:
        # Rule 1: temporal scope
        if not request.is_within_scope(item.source_timestamp):
            continue
        # Rule 3: type filtering
        if (
            request.evidence_types_requested
            and item.evidence_type not in request.evidence_types_requested
        ):
            continue
        filtered.append(item)
    return filtered


# ---------------------------------------------------------------------------
# Redaction manifest (Rule 4)
# ---------------------------------------------------------------------------

@dataclass
class RedactionEntry:
    """A single redaction within an evidence record."""
    segment_id: str
    justification: str
    unredacted_hash: str  # SHA-256 of original content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "justification": self.justification,
            "unredacted_hash": self.unredacted_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RedactionEntry":
        return cls(**d)


@dataclass
class RedactionManifest:
    """Manifest documenting all redactions applied to evidence (Rule 4).

    Agents may redact portions of requested evidence that are clearly
    unrelated to the incident. They must provide a hash of the unredacted
    content so integrity can be verified later if challenged.
    """
    evidence_id: str
    agent_id: str
    redactions: List[RedactionEntry] = field(default_factory=list)
    manifest_id: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.manifest_id:
            self.manifest_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()

    def add_redaction(
        self,
        segment_id: str,
        justification: str,
        original_content: Any,
    ) -> RedactionEntry:
        """Add a redaction entry with automatic hash computation."""
        entry = RedactionEntry(
            segment_id=segment_id,
            justification=justification,
            unredacted_hash=_content_hash(original_content),
        )
        self.redactions.append(entry)
        return entry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "evidence_id": self.evidence_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "redactions": [r.to_dict() for r in self.redactions],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RedactionManifest":
        return cls(
            manifest_id=d.get("manifest_id", ""),
            evidence_id=d["evidence_id"],
            agent_id=d["agent_id"],
            timestamp=d.get("timestamp", ""),
            redactions=[RedactionEntry.from_dict(r) for r in d.get("redactions", [])],
        )
