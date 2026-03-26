"""Shared data structures and JSON schemas for the Agent Justice Protocol.

Implements Section 4.2 (Common Data Structures), Section 5.3 (Forensic Finding),
Section 6.3 (Claim Schema), Section 6.6 (Decision Schema), and Section 7.2
(Risk Profile Schema) of the AJP whitepaper v1.3.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IDENTITY_SYSTEMS = (
    "coc", "erc8004", "a2a", "w3c_vc", "w3c_did", "mcp", "uri",
)

EVIDENCE_TYPES = (
    "chain_entry", "interaction_log", "transaction_receipt", "rating_record",
    "telemetry", "communication", "external_attestation", "self_report",
)

PROVENANCE_TIERS = {
    1: {"name": "cryptographic", "weight": 1.0},
    2: {"name": "attested", "weight": 0.75},
    3: {"name": "bilateral", "weight": 0.50},
    4: {"name": "self_reported", "weight": 0.25},
}

INCIDENT_TYPES = (
    "service_failure", "data_loss", "unauthorized_action",
    "contractual_breach", "security_incident", "quality_deficiency",
    "timeout", "cascade_failure",
)

SEVERITY_LEVELS = ("critical", "high", "medium", "low")

HARM_TYPES = (
    "financial", "reputational", "data_loss", "service_disruption",
    "security_breach", "contractual_breach",
)

REMEDIATION_TYPES = (
    "compensation", "service_credit", "reputation_adjustment",
    "behavioral_restriction", "apology", "human_escalation",
    "referral", "no_action",
)

RESOLUTION_TIERS = ("automated", "peer_arbitration", "human_escalation")

VOTE_OPTIONS = ("for_claimant", "for_respondent", "split", "abstain")

CAUSAL_INDICATOR_TYPES = (
    "temporal_correlation", "policy_violation", "behavioral_anomaly",
)

ROOT_CAUSE_CATEGORIES = (
    "design", "configuration", "training", "environment",
    "interaction", "external",
)

FAULT_BASIS_TYPES = (
    "proximate_cause", "contributing_cause", "negligence", "strict_liability",
)

RISK_LEVELS = {
    (0, 100): "minimal",
    (101, 300): "low",
    (301, 500): "moderate",
    (501, 700): "elevated",
    (701, 900): "high",
    (901, 1000): "critical",
}

RISK_DIMENSIONS = (
    "incident_frequency", "severity_profile", "fault_history",
    "cooperation_score", "recovery_capability",
)

DEFAULT_RISK_WEIGHTS = {
    "incident_frequency": 0.25,
    "severity_profile": 0.25,
    "fault_history": 0.25,
    "cooperation_score": 0.15,
    "recovery_capability": 0.10,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonical_json(obj: Any) -> str:
    """JCS-like canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_dict(d: Dict[str, Any], exclude_keys: Optional[List[str]] = None) -> str:
    """SHA-256 of canonical JSON, optionally excluding specific keys."""
    filtered = {k: v for k, v in d.items() if k not in (exclude_keys or [])}
    return hashlib.sha256(_canonical_json(filtered).encode("utf-8")).hexdigest()


def _content_hash(content: Any) -> str:
    """SHA-256 of content (string or JSON-serializable object)."""
    if isinstance(content, str):
        data = content.encode("utf-8")
    else:
        data = _canonical_json(content).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def risk_level_for_score(score: int) -> str:
    """Return the risk level label for a given score (0-1000)."""
    for (lo, hi), level in RISK_LEVELS.items():
        if lo <= score <= hi:
            return level
    return "unknown"


# ---------------------------------------------------------------------------
# AgentReference (Section 4.2.1)
# ---------------------------------------------------------------------------

@dataclass
class AgentReference:
    """Identity-system-agnostic agent reference."""
    agent_id: str
    identity_system: str = "uri"
    identity_proof: str = ""
    operational_age_days: Optional[int] = None
    arp_composite: Optional[float] = None
    arp_confidence: Optional[float] = None

    def __post_init__(self) -> None:
        if self.identity_system not in IDENTITY_SYSTEMS:
            raise ValueError(
                f"identity_system must be one of {IDENTITY_SYSTEMS}, "
                f"got '{self.identity_system}'"
            )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "identity_system": self.identity_system,
            "identity_proof": self.identity_proof,
        }
        if self.operational_age_days is not None:
            d["operational_age_days"] = self.operational_age_days
        if self.arp_composite is not None or self.arp_confidence is not None:
            d["arp_reputation"] = {
                "composite": self.arp_composite,
                "confidence": self.arp_confidence,
            }
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentReference":
        arp = d.get("arp_reputation", {})
        return cls(
            agent_id=d["agent_id"],
            identity_system=d.get("identity_system", "uri"),
            identity_proof=d.get("identity_proof", ""),
            operational_age_days=d.get("operational_age_days"),
            arp_composite=arp.get("composite") if arp else None,
            arp_confidence=arp.get("confidence") if arp else None,
        )


# ---------------------------------------------------------------------------
# CustodyEntry (Section 4.2.2 — chain_of_custody)
# ---------------------------------------------------------------------------

@dataclass
class CustodyEntry:
    custodian: str
    received: str = ""
    action: str = "collected"
    integrity_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "custodian": self.custodian,
            "received": self.received or _now_iso(),
            "action": self.action,
            "integrity_hash": self.integrity_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CustodyEntry":
        return cls(**d)


# ---------------------------------------------------------------------------
# EvidenceRecord (Section 4.2.2)
# ---------------------------------------------------------------------------

@dataclass
class EvidenceRecord:
    """The fundamental unit of evidence across all modules."""
    evidence_type: str
    provenance_tier: int
    source_agent_id: str
    content: Any
    evidence_id: str = ""
    source_system: str = "custom"
    source_timestamp: str = ""
    anchor_proof: str = ""
    content_hash: str = ""
    chain_of_custody: List[CustodyEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.evidence_id:
            self.evidence_id = _uuid()
        if not self.source_timestamp:
            self.source_timestamp = _now_iso()
        if not self.content_hash:
            self.content_hash = _content_hash(self.content)
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(
                f"evidence_type must be one of {EVIDENCE_TYPES}, "
                f"got '{self.evidence_type}'"
            )
        if self.provenance_tier not in PROVENANCE_TIERS:
            raise ValueError(f"provenance_tier must be 1-4, got {self.provenance_tier}")

    @property
    def weight(self) -> float:
        return PROVENANCE_TIERS[self.provenance_tier]["weight"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "provenance_tier": self.provenance_tier,
            "source": {
                "agent_id": self.source_agent_id,
                "system": self.source_system,
                "timestamp": self.source_timestamp,
                "anchor_proof": self.anchor_proof,
            },
            "content_hash": self.content_hash,
            "content": self.content,
            "chain_of_custody": [c.to_dict() for c in self.chain_of_custody],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvidenceRecord":
        src = d.get("source", {})
        custody = [CustodyEntry.from_dict(c) for c in d.get("chain_of_custody", [])]
        return cls(
            evidence_id=d.get("evidence_id", ""),
            evidence_type=d["evidence_type"],
            provenance_tier=d["provenance_tier"],
            source_agent_id=src.get("agent_id", ""),
            source_system=src.get("system", "custom"),
            source_timestamp=src.get("timestamp", ""),
            anchor_proof=src.get("anchor_proof", ""),
            content_hash=d.get("content_hash", ""),
            content=d.get("content"),
            chain_of_custody=custody,
        )

    def verify_content_hash(self) -> bool:
        return self.content_hash == _content_hash(self.content)


# ---------------------------------------------------------------------------
# TimelineEvent (used in ForensicFinding)
# ---------------------------------------------------------------------------

@dataclass
class TimelineEvent:
    sequence: int
    timestamp: str
    agent_id: str
    action: str
    evidence_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "action": self.action,
            "evidence_ids": self.evidence_ids,
            "confidence": self.confidence,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TimelineEvent":
        return cls(
            sequence=d["sequence"],
            timestamp=d["timestamp"],
            agent_id=d["agent_id"],
            action=d["action"],
            evidence_ids=d.get("evidence_ids", []),
            confidence=d.get("confidence", 1.0),
            notes=d.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# CausalIndicator (Phase 4a automated flags)
# ---------------------------------------------------------------------------

@dataclass
class CausalIndicator:
    indicator_type: str
    description: str
    agent_id: str
    evidence_ids: List[str] = field(default_factory=list)
    rule_match_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.indicator_type not in CAUSAL_INDICATOR_TYPES:
            raise ValueError(
                f"indicator_type must be one of {CAUSAL_INDICATOR_TYPES}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_type": self.indicator_type,
            "description": self.description,
            "agent_id": self.agent_id,
            "evidence_ids": self.evidence_ids,
            "rule_match_confidence": self.rule_match_confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CausalIndicator":
        return cls(**d)


# ---------------------------------------------------------------------------
# FaultAllocation
# ---------------------------------------------------------------------------

@dataclass
class FaultAllocation:
    agent_id: str
    fault_percentage: int
    basis: str = "proximate_cause"
    evidence_summary: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.fault_percentage <= 100:
            raise ValueError("fault_percentage must be 0-100")
        if self.basis not in FAULT_BASIS_TYPES:
            raise ValueError(f"basis must be one of {FAULT_BASIS_TYPES}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "fault_percentage": self.fault_percentage,
            "basis": self.basis,
            "evidence_summary": self.evidence_summary,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FaultAllocation":
        return cls(**d)


# ---------------------------------------------------------------------------
# ForensicFinding (Section 5.3)
# ---------------------------------------------------------------------------

@dataclass
class ForensicFinding:
    """Structured output of a forensic investigation."""
    investigation_id: str
    incident_type: str
    severity: str
    reported_by: AgentReference
    description: str
    subjects: List[AgentReference] = field(default_factory=list)
    reporters: List[AgentReference] = field(default_factory=list)
    witnesses: List[AgentReference] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    causal_indicators: List[CausalIndicator] = field(default_factory=list)
    fault_allocation: List[FaultAllocation] = field(default_factory=list)
    no_fault_factors: List[str] = field(default_factory=list)
    total_evidence_items: int = 0
    tier_1_count: int = 0
    tier_2_count: int = 0
    tier_3_count: int = 0
    tier_4_count: int = 0
    key_evidence_ids: List[str] = field(default_factory=list)
    recommendations: List[Dict[str, str]] = field(default_factory=list)
    finding_id: str = ""
    incident_id: str = ""
    timestamp: str = ""
    reported_at: str = ""
    finding_hash: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.finding_id:
            self.finding_id = _uuid()
        if not self.incident_id:
            self.incident_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()
        if not self.reported_at:
            self.reported_at = self.timestamp
        if self.incident_type not in INCIDENT_TYPES:
            raise ValueError(f"incident_type must be one of {INCIDENT_TYPES}")
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(f"severity must be one of {SEVERITY_LEVELS}")

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("finding_hash", None)
        self.finding_hash = _hash_dict(d)
        return self.finding_hash

    def verify_hash(self) -> bool:
        if not self.finding_hash:
            return False
        d = self.to_dict()
        d.pop("finding_hash", None)
        return self.finding_hash == _hash_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "version": self.version,
            "finding_id": self.finding_id,
            "investigation_id": self.investigation_id,
            "timestamp": self.timestamp,
            "incident": {
                "incident_id": self.incident_id,
                "incident_type": self.incident_type,
                "severity": self.severity,
                "reported_by": self.reported_by.to_dict(),
                "reported_at": self.reported_at,
                "description": self.description,
            },
            "parties": {
                "subjects": [s.to_dict() for s in self.subjects],
                "reporters": [r.to_dict() for r in self.reporters],
                "witnesses": [w.to_dict() for w in self.witnesses],
            },
            "timeline": [t.to_dict() for t in self.timeline],
            "causal_indicators": {
                "automated_flags": [c.to_dict() for c in self.causal_indicators],
                "note": "Automated causal indicators (Phase 4a). Advisory only.",
            },
            "attribution": {
                "fault_allocation": [f.to_dict() for f in self.fault_allocation],
                "no_fault_factors": self.no_fault_factors,
            },
            "evidence_summary": {
                "total_evidence_items": self.total_evidence_items,
                "by_tier": {
                    "tier_1_cryptographic": self.tier_1_count,
                    "tier_2_attested": self.tier_2_count,
                    "tier_3_bilateral": self.tier_3_count,
                    "tier_4_self_reported": self.tier_4_count,
                },
                "key_evidence": self.key_evidence_ids,
            },
            "recommendations": self.recommendations,
        }
        if self.finding_hash:
            d["finding_hash"] = self.finding_hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ForensicFinding":
        incident = d.get("incident", {})
        parties = d.get("parties", {})
        attrib = d.get("attribution", {})
        ev_sum = d.get("evidence_summary", {})
        by_tier = ev_sum.get("by_tier", {})
        ci = d.get("causal_indicators", {})

        return cls(
            version=d.get("version", 1),
            finding_id=d.get("finding_id", ""),
            investigation_id=d.get("investigation_id", ""),
            timestamp=d.get("timestamp", ""),
            incident_type=incident.get("incident_type", "service_failure"),
            severity=incident.get("severity", "medium"),
            reported_by=AgentReference.from_dict(incident.get("reported_by", {"agent_id": "unknown"})),
            reported_at=incident.get("reported_at", ""),
            description=incident.get("description", ""),
            incident_id=incident.get("incident_id", ""),
            subjects=[AgentReference.from_dict(s) for s in parties.get("subjects", [])],
            reporters=[AgentReference.from_dict(r) for r in parties.get("reporters", [])],
            witnesses=[AgentReference.from_dict(w) for w in parties.get("witnesses", [])],
            timeline=[TimelineEvent.from_dict(t) for t in d.get("timeline", [])],
            causal_indicators=[CausalIndicator.from_dict(c) for c in ci.get("automated_flags", [])],
            fault_allocation=[FaultAllocation.from_dict(f) for f in attrib.get("fault_allocation", [])],
            no_fault_factors=attrib.get("no_fault_factors", []),
            total_evidence_items=ev_sum.get("total_evidence_items", 0),
            tier_1_count=by_tier.get("tier_1_cryptographic", 0),
            tier_2_count=by_tier.get("tier_2_attested", 0),
            tier_3_count=by_tier.get("tier_3_bilateral", 0),
            tier_4_count=by_tier.get("tier_4_self_reported", 0),
            key_evidence_ids=ev_sum.get("key_evidence", []),
            recommendations=d.get("recommendations", []),
            finding_hash=d.get("finding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DisputeClaim (Section 6.3)
# ---------------------------------------------------------------------------

@dataclass
class DisputeClaim:
    """A formal dispute claim referencing a forensic finding."""
    claimant: AgentReference
    respondent: AgentReference
    finding_id: str
    finding_hash: str
    harm_type: str
    harm_description: str
    requested_remediation_type: str
    requested_remediation_details: str = ""
    quantified_amount: Optional[float] = None
    quantified_currency: str = "USD"
    quantified_basis: str = ""
    supporting_evidence_ids: List[str] = field(default_factory=list)
    asa_id: str = ""
    terms_hash: str = ""
    breached_clauses: List[str] = field(default_factory=list)
    claim_id: str = ""
    incident_id: str = ""
    interaction_id: str = ""
    timestamp: str = ""
    claim_hash: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.claim_id:
            self.claim_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()
        if self.harm_type not in HARM_TYPES:
            raise ValueError(f"harm_type must be one of {HARM_TYPES}")
        if self.requested_remediation_type not in REMEDIATION_TYPES:
            raise ValueError(
                f"requested_remediation_type must be one of {REMEDIATION_TYPES}"
            )

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("claim_hash", None)
        self.claim_hash = _hash_dict(d)
        return self.claim_hash

    def verify_hash(self) -> bool:
        if not self.claim_hash:
            return False
        d = self.to_dict()
        d.pop("claim_hash", None)
        return self.claim_hash == _hash_dict(d)

    def select_tier(self) -> str:
        """Auto-select resolution tier based on dispute characteristics (Section 6.4)."""
        amount = self.quantified_amount or 0.0
        if amount < 1000 and self.asa_id:
            return "automated"
        if amount > 50000:
            return "human_escalation"
        return "peer_arbitration"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "version": self.version,
            "claim_id": self.claim_id,
            "timestamp": self.timestamp,
            "claimant": self.claimant.to_dict(),
            "respondent": self.respondent.to_dict(),
            "finding_id": self.finding_id,
            "finding_hash": self.finding_hash,
            "incident_id": self.incident_id,
            "interaction_id": self.interaction_id,
            "harm": {
                "type": self.harm_type,
                "description": self.harm_description,
                "quantified_value": {
                    "amount": self.quantified_amount,
                    "currency": self.quantified_currency,
                    "basis": self.quantified_basis,
                },
            },
            "requested_remediation": {
                "type": self.requested_remediation_type,
                "details": self.requested_remediation_details,
            },
            "supporting_evidence": self.supporting_evidence_ids,
            "agreement_reference": {
                "asa_id": self.asa_id,
                "terms_hash": self.terms_hash,
                "breached_clauses": self.breached_clauses,
            },
        }
        if self.claim_hash:
            d["claim_hash"] = self.claim_hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DisputeClaim":
        harm = d.get("harm", {})
        qv = harm.get("quantified_value", {})
        rem = d.get("requested_remediation", {})
        agr = d.get("agreement_reference", {})
        return cls(
            version=d.get("version", 1),
            claim_id=d.get("claim_id", ""),
            timestamp=d.get("timestamp", ""),
            claimant=AgentReference.from_dict(d.get("claimant", {"agent_id": "unknown"})),
            respondent=AgentReference.from_dict(d.get("respondent", {"agent_id": "unknown"})),
            finding_id=d.get("finding_id", ""),
            finding_hash=d.get("finding_hash", ""),
            incident_id=d.get("incident_id", ""),
            interaction_id=d.get("interaction_id", ""),
            harm_type=harm.get("type", "financial"),
            harm_description=harm.get("description", ""),
            quantified_amount=qv.get("amount"),
            quantified_currency=qv.get("currency", "USD"),
            quantified_basis=qv.get("basis", ""),
            requested_remediation_type=rem.get("type", "compensation"),
            requested_remediation_details=rem.get("details", ""),
            supporting_evidence_ids=d.get("supporting_evidence", []),
            asa_id=agr.get("asa_id", ""),
            terms_hash=agr.get("terms_hash", ""),
            breached_clauses=agr.get("breached_clauses", []),
            claim_hash=d.get("claim_hash", ""),
        )


# ---------------------------------------------------------------------------
# ArbitrationDecision (Section 6.6)
# ---------------------------------------------------------------------------

@dataclass
class ArbitratorVote:
    agent_id: str
    vote: str
    arbweight_at_decision: float = 0.0

    def __post_init__(self) -> None:
        if self.vote not in VOTE_OPTIONS:
            raise ValueError(f"vote must be one of {VOTE_OPTIONS}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "arbweight_at_decision": self.arbweight_at_decision,
            "vote": self.vote,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArbitratorVote":
        return cls(**d)


@dataclass
class ArbitrationDecision:
    """Structured outcome of dispute arbitration."""
    dispute_id: str
    claim_id: str
    resolution_tier: str
    claimant_fault_pct: int = 0
    respondent_fault_pct: int = 0
    no_fault_pct: int = 0
    fault_basis: str = ""
    remediation_type: str = "no_action"
    remediation_details: str = ""
    compensation_amount: Optional[float] = None
    compensation_currency: str = "USD"
    respondent_rep_adjustment: float = 0.0
    claimant_rep_adjustment: float = 0.0
    dimensions_affected: List[str] = field(default_factory=list)
    arbitrators: List[ArbitratorVote] = field(default_factory=list)
    findings_of_fact: List[Dict[str, Any]] = field(default_factory=list)
    precedent_tags: List[str] = field(default_factory=list)
    dissenting_opinions: List[Dict[str, str]] = field(default_factory=list)
    appeal_window_expires: str = ""
    escalation_tier: str = ""
    decision_id: str = ""
    timestamp: str = ""
    decision_hash: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.decision_id:
            self.decision_id = _uuid()
        if not self.timestamp:
            self.timestamp = _now_iso()
        if self.resolution_tier not in RESOLUTION_TIERS:
            raise ValueError(f"resolution_tier must be one of {RESOLUTION_TIERS}")
        total = self.claimant_fault_pct + self.respondent_fault_pct + self.no_fault_pct
        if total != 100:
            raise ValueError(f"Fault percentages must sum to 100, got {total}")

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("decision_hash", None)
        self.decision_hash = _hash_dict(d)
        return self.decision_hash

    def verify_hash(self) -> bool:
        if not self.decision_hash:
            return False
        d = self.to_dict()
        d.pop("decision_hash", None)
        return self.decision_hash == _hash_dict(d)

    @property
    def majority_vote(self) -> str:
        """Determine the majority vote from arbitrators."""
        if not self.arbitrators:
            return "abstain"
        counts: Dict[str, int] = {}
        for v in self.arbitrators:
            counts[v.vote] = counts.get(v.vote, 0) + 1
        return max(counts, key=lambda k: counts[k])

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "version": self.version,
            "decision_id": self.decision_id,
            "dispute_id": self.dispute_id,
            "claim_id": self.claim_id,
            "timestamp": self.timestamp,
            "resolution_tier": self.resolution_tier,
            "arbitrators": [a.to_dict() for a in self.arbitrators],
            "findings_of_fact": self.findings_of_fact,
            "fault_determination": {
                "claimant_fault_pct": self.claimant_fault_pct,
                "respondent_fault_pct": self.respondent_fault_pct,
                "no_fault_pct": self.no_fault_pct,
                "basis": self.fault_basis,
            },
            "remediation": {
                "type": self.remediation_type,
                "details": self.remediation_details,
                "compensation": {
                    "amount": self.compensation_amount,
                    "currency": self.compensation_currency,
                },
                "reputation_impact": {
                    "respondent_adjustment": self.respondent_rep_adjustment,
                    "claimant_adjustment": self.claimant_rep_adjustment,
                    "dimensions_affected": self.dimensions_affected,
                },
            },
            "precedent_tags": self.precedent_tags,
            "dissenting_opinions": self.dissenting_opinions,
            "appeal_window": {
                "expires": self.appeal_window_expires,
                "escalation_tier": self.escalation_tier,
            },
        }
        if self.decision_hash:
            d["decision_hash"] = self.decision_hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArbitrationDecision":
        fault = d.get("fault_determination", {})
        rem = d.get("remediation", {})
        comp = rem.get("compensation", {})
        rep = rem.get("reputation_impact", {})
        appeal = d.get("appeal_window", {})
        return cls(
            version=d.get("version", 1),
            decision_id=d.get("decision_id", ""),
            dispute_id=d.get("dispute_id", ""),
            claim_id=d.get("claim_id", ""),
            timestamp=d.get("timestamp", ""),
            resolution_tier=d.get("resolution_tier", "automated"),
            arbitrators=[ArbitratorVote.from_dict(a) for a in d.get("arbitrators", [])],
            findings_of_fact=d.get("findings_of_fact", []),
            claimant_fault_pct=fault.get("claimant_fault_pct", 0),
            respondent_fault_pct=fault.get("respondent_fault_pct", 0),
            no_fault_pct=fault.get("no_fault_pct", 0),
            fault_basis=fault.get("basis", ""),
            remediation_type=rem.get("type", "no_action"),
            remediation_details=rem.get("details", ""),
            compensation_amount=comp.get("amount"),
            compensation_currency=comp.get("currency", "USD"),
            respondent_rep_adjustment=rep.get("respondent_adjustment", 0.0),
            claimant_rep_adjustment=rep.get("claimant_adjustment", 0.0),
            dimensions_affected=rep.get("dimensions_affected", []),
            precedent_tags=d.get("precedent_tags", []),
            dissenting_opinions=d.get("dissenting_opinions", []),
            appeal_window_expires=appeal.get("expires", ""),
            escalation_tier=appeal.get("escalation_tier", ""),
            decision_hash=d.get("decision_hash", ""),
        )


# ---------------------------------------------------------------------------
# RiskProfile (Section 7.2)
# ---------------------------------------------------------------------------

@dataclass
class RiskProfile:
    """Standardized risk profile for insurance underwriting."""
    subject: AgentReference
    overall_score: int = 0
    confidence: float = 0.05
    trend: str = "stable"
    percentile: int = 50
    incident_frequency_score: int = 0
    incidents_per_1000: float = 0.0
    severity_score: int = 0
    severity_distribution: Dict[str, int] = field(
        default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0}
    )
    fault_history_score: int = 0
    disputes_at_fault: int = 0
    average_fault_pct: float = 0.0
    disputes_no_fault: int = 0
    cooperation_score: int = 1000
    evidence_provision_rate: float = 1.0
    response_rate: float = 1.0
    adverse_inferences: int = 0
    recovery_score: int = 1000
    mean_time_to_resolution: int = 0
    remediation_compliance_rate: float = 1.0
    risk_factors: List[Dict[str, str]] = field(default_factory=list)
    agent_class: str = ""
    class_average_score: int = 0
    class_size: int = 0
    expected_loss_rate: float = 0.0
    loss_p50: float = 0.0
    loss_p90: float = 0.0
    loss_p99: float = 0.0
    recommended_premium_basis: float = 0.0
    data_window_start: str = ""
    data_window_end: str = ""
    findings_count: int = 0
    disputes_count: int = 0
    profile_id: str = ""
    generated_at: str = ""
    profile_hash: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.profile_id:
            self.profile_id = _uuid()
        if not self.generated_at:
            self.generated_at = _now_iso()

    @property
    def risk_level(self) -> str:
        return risk_level_for_score(self.overall_score)

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("profile_hash", None)
        self.profile_hash = _hash_dict(d)
        return self.profile_hash

    def verify_hash(self) -> bool:
        if not self.profile_hash:
            return False
        d = self.to_dict()
        d.pop("profile_hash", None)
        return self.profile_hash == _hash_dict(d)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "version": self.version,
            "profile_id": self.profile_id,
            "subject": self.subject.to_dict(),
            "generated_at": self.generated_at,
            "data_window": {
                "start": self.data_window_start,
                "end": self.data_window_end,
                "findings_count": self.findings_count,
                "disputes_count": self.disputes_count,
            },
            "risk_score": {
                "overall": self.overall_score,
                "confidence": self.confidence,
                "trend": self.trend,
                "percentile": self.percentile,
            },
            "dimension_scores": {
                "incident_frequency": {
                    "score": self.incident_frequency_score,
                    "incidents_per_1000_interactions": self.incidents_per_1000,
                },
                "severity_profile": {
                    "score": self.severity_score,
                    "distribution": self.severity_distribution,
                },
                "fault_history": {
                    "score": self.fault_history_score,
                    "disputes_at_fault": self.disputes_at_fault,
                    "average_fault_pct": self.average_fault_pct,
                    "disputes_no_fault": self.disputes_no_fault,
                },
                "cooperation_score": {
                    "score": self.cooperation_score,
                    "evidence_provision_rate": self.evidence_provision_rate,
                    "response_rate": self.response_rate,
                    "adverse_inferences": self.adverse_inferences,
                },
                "recovery_capability": {
                    "score": self.recovery_score,
                    "mean_time_to_resolution": self.mean_time_to_resolution,
                    "remediation_compliance_rate": self.remediation_compliance_rate,
                },
            },
            "risk_factors": self.risk_factors,
            "comparable_agents": {
                "class": self.agent_class,
                "class_average_score": self.class_average_score,
                "class_size": self.class_size,
            },
            "actuarial_outputs": {
                "expected_loss_rate": self.expected_loss_rate,
                "loss_severity_distribution": {
                    "p50": self.loss_p50,
                    "p90": self.loss_p90,
                    "p99": self.loss_p99,
                },
                "recommended_premium_basis": self.recommended_premium_basis,
            },
        }
        if self.profile_hash:
            d["profile_hash"] = self.profile_hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RiskProfile":
        rs = d.get("risk_score", {})
        ds = d.get("dimension_scores", {})
        ifreq = ds.get("incident_frequency", {})
        sev = ds.get("severity_profile", {})
        fh = ds.get("fault_history", {})
        coop = ds.get("cooperation_score", {})
        rec = ds.get("recovery_capability", {})
        comp = d.get("comparable_agents", {})
        act = d.get("actuarial_outputs", {})
        lsd = act.get("loss_severity_distribution", {})
        dw = d.get("data_window", {})

        return cls(
            version=d.get("version", 1),
            profile_id=d.get("profile_id", ""),
            subject=AgentReference.from_dict(d.get("subject", {"agent_id": "unknown"})),
            generated_at=d.get("generated_at", ""),
            data_window_start=dw.get("start", ""),
            data_window_end=dw.get("end", ""),
            findings_count=dw.get("findings_count", 0),
            disputes_count=dw.get("disputes_count", 0),
            overall_score=rs.get("overall", 0),
            confidence=rs.get("confidence", 0.05),
            trend=rs.get("trend", "stable"),
            percentile=rs.get("percentile", 50),
            incident_frequency_score=ifreq.get("score", 0),
            incidents_per_1000=ifreq.get("incidents_per_1000_interactions", 0.0),
            severity_score=sev.get("score", 0),
            severity_distribution=sev.get("distribution", {}),
            fault_history_score=fh.get("score", 0),
            disputes_at_fault=fh.get("disputes_at_fault", 0),
            average_fault_pct=fh.get("average_fault_pct", 0.0),
            disputes_no_fault=fh.get("disputes_no_fault", 0),
            cooperation_score=coop.get("score", 1000),
            evidence_provision_rate=coop.get("evidence_provision_rate", 1.0),
            response_rate=coop.get("response_rate", 1.0),
            adverse_inferences=coop.get("adverse_inferences", 0),
            recovery_score=rec.get("score", 1000),
            mean_time_to_resolution=rec.get("mean_time_to_resolution", 0),
            remediation_compliance_rate=rec.get("remediation_compliance_rate", 1.0),
            risk_factors=d.get("risk_factors", []),
            agent_class=comp.get("class", ""),
            class_average_score=comp.get("class_average_score", 0),
            class_size=comp.get("class_size", 0),
            expected_loss_rate=act.get("expected_loss_rate", 0.0),
            loss_p50=lsd.get("p50", 0.0),
            loss_p90=lsd.get("p90", 0.0),
            loss_p99=lsd.get("p99", 0.0),
            recommended_premium_basis=act.get("recommended_premium_basis", 0.0),
            profile_hash=d.get("profile_hash", ""),
        )
