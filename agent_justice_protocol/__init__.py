"""Agent Justice Protocol — forensic investigation, dispute resolution,
and risk assessment for the agent economy.

A pip-installable implementation of the Agent Justice Protocol,
companion to Chain of Consciousness and Agent Rating Protocol.
"""

from .schema import (
    CAUSAL_INDICATOR_TYPES,
    DEFAULT_RISK_WEIGHTS,
    EVIDENCE_TYPES,
    FAULT_BASIS_TYPES,
    HARM_TYPES,
    IDENTITY_SYSTEMS,
    INCIDENT_TYPES,
    PROVENANCE_TIERS,
    REMEDIATION_TYPES,
    RESOLUTION_TIERS,
    RISK_DIMENSIONS,
    RISK_LEVELS,
    SEVERITY_LEVELS,
    VOTE_OPTIONS,
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
)
from .store import JusticeStore
from .forensics import ForensicInvestigation, IncidentReport
from .evidence import (
    EvidenceRequest,
    RedactionEntry,
    RedactionManifest,
    filter_relevant_evidence,
)
from .privacy import PrivacyGuard
from .dispute import (
    Commitment,
    Dispute,
    DisputePhase,
    DisputeResponse,
    ResponseType,
    SettlementOffer,
    create_commitment,
    verify_commitment,
)
from .arbitration import (
    ArbitratorCandidate,
    ArbitratorPool,
    aggregate_votes,
    render_decision,
)
from .remediation import RemediationOrder, RemediationTracker
from .risk import RiskEngine, population_risk_summary

__all__ = [
    # Schema / data structures
    "AgentReference",
    "ArbitrationDecision",
    "ArbitratorVote",
    "CausalIndicator",
    "CustodyEntry",
    "DisputeClaim",
    "EvidenceRecord",
    "FaultAllocation",
    "ForensicFinding",
    "RiskProfile",
    "TimelineEvent",
    "risk_level_for_score",
    # Constants
    "CAUSAL_INDICATOR_TYPES",
    "DEFAULT_RISK_WEIGHTS",
    "EVIDENCE_TYPES",
    "FAULT_BASIS_TYPES",
    "HARM_TYPES",
    "IDENTITY_SYSTEMS",
    "INCIDENT_TYPES",
    "PROVENANCE_TIERS",
    "REMEDIATION_TYPES",
    "RESOLUTION_TIERS",
    "RISK_DIMENSIONS",
    "RISK_LEVELS",
    "SEVERITY_LEVELS",
    "VOTE_OPTIONS",
    # Store
    "JusticeStore",
    # Forensics (Module 1)
    "ForensicInvestigation",
    "IncidentReport",
    "EvidenceRequest",
    "RedactionEntry",
    "RedactionManifest",
    "filter_relevant_evidence",
    "PrivacyGuard",
    # Dispute Resolution (Module 2)
    "Commitment",
    "Dispute",
    "DisputePhase",
    "DisputeResponse",
    "ResponseType",
    "SettlementOffer",
    "create_commitment",
    "verify_commitment",
    # Arbitration
    "ArbitratorCandidate",
    "ArbitratorPool",
    "aggregate_votes",
    "render_decision",
    # Remediation
    "RemediationOrder",
    "RemediationTracker",
    # Risk Assessment (Module 3)
    "RiskEngine",
    "population_risk_summary",
]

__version__ = "0.1.0"
