"""Forensics Engine — investigation, timeline reconstruction, causal indicators.

Implements Module 1 (Section 5) of the AJP whitepaper:
- Five-phase investigation protocol (Section 5.2)
- Timeline reconstruction (Phase 3)
- Rule-based causal indicators (Phase 4a)
- Investigation modes (Section 5.5)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .evidence import EvidenceRequest, filter_relevant_evidence, _parse_iso
from .privacy import PrivacyGuard
from .schema import (
    AgentReference,
    CausalIndicator,
    CustodyEntry,
    EvidenceRecord,
    FaultAllocation,
    ForensicFinding,
    TimelineEvent,
    _now_iso,
    _uuid,
)


# Investigation phases
PHASES = ("initiation", "evidence_collection", "timeline_reconstruction",
          "causal_assessment", "finding_generation")


@dataclass
class IncidentReport:
    """Trigger for a forensic investigation (Phase 1 input)."""
    reporter: AgentReference
    incident_type: str
    severity: str
    description: str
    incident_time: str = ""
    subjects: List[AgentReference] = field(default_factory=list)
    incident_id: str = ""

    def __post_init__(self) -> None:
        if not self.incident_id:
            self.incident_id = _uuid()
        if not self.incident_time:
            self.incident_time = _now_iso()


class ForensicInvestigation:
    """Manages a single forensic investigation through 5 phases.

    Usage:
        report = IncidentReport(reporter=..., incident_type=..., ...)
        inv = ForensicInvestigation(report)

        # Phase 2: add evidence
        inv.add_evidence(evidence_record)

        # Phase 3: reconstruct timeline (automatic from evidence)
        inv.reconstruct_timeline()

        # Phase 4a: generate causal indicators
        inv.generate_causal_indicators()

        # Phase 5: produce finding
        finding = inv.produce_finding()
    """

    def __init__(
        self,
        report: IncidentReport,
        privacy_guard: Optional[PrivacyGuard] = None,
    ) -> None:
        self.investigation_id = _uuid()
        self.report = report
        self.phase = "initiation"
        self.evidence: List[EvidenceRecord] = []
        self.timeline: List[TimelineEvent] = []
        self.causal_indicators: List[CausalIndicator] = []
        self.privacy_guard = privacy_guard
        self._initiated_at = _now_iso()

    @property
    def evidence_by_tier(self) -> Dict[int, List[EvidenceRecord]]:
        result: Dict[int, List[EvidenceRecord]] = {1: [], 2: [], 3: [], 4: []}
        for e in self.evidence:
            result[e.provenance_tier].append(e)
        return result

    # -- Phase 2: Evidence Collection --

    def add_evidence(
        self,
        evidence: EvidenceRecord,
        collected_by: str = "",
    ) -> EvidenceRecord:
        """Add an evidence record with chain-of-custody tracking."""
        # Add custody entry
        evidence.chain_of_custody.append(CustodyEntry(
            custodian=collected_by or "forensics_engine",
            received=_now_iso(),
            action="collected",
            integrity_hash=evidence.content_hash,
        ))
        self.evidence.append(evidence)
        self.phase = "evidence_collection"
        return evidence

    def add_evidence_batch(
        self,
        records: List[EvidenceRecord],
        collected_by: str = "",
    ) -> int:
        """Add multiple evidence records at once."""
        for r in records:
            self.add_evidence(r, collected_by)
        return len(records)

    def create_evidence_request(
        self,
        target_agent_id: str,
        evidence_types: List[str],
        relevance: str,
        approved_by: str = "",
        window_hours: int = 24,
        justification: str = "",
    ) -> EvidenceRequest:
        """Create a scoped evidence request (Section 5.7)."""
        return EvidenceRequest(
            investigation_id=self.investigation_id,
            target_agent_id=target_agent_id,
            incident_time=self.report.incident_time,
            evidence_types_requested=evidence_types,
            incident_relevance=relevance,
            approved_by=approved_by,
            window_hours=window_hours,
            justification=justification,
        )

    def filter_evidence(self, request: EvidenceRequest) -> List[EvidenceRecord]:
        """Filter collected evidence by an evidence request's scope."""
        return filter_relevant_evidence(self.evidence, request)

    # -- Phase 3: Timeline Reconstruction --

    def reconstruct_timeline(self) -> List[TimelineEvent]:
        """Merge evidence into a unified chronological timeline.

        Sorts evidence by timestamp, creates timeline events,
        flags gaps and contradictions.
        """
        # Sort evidence by timestamp
        sorted_evidence = sorted(
            self.evidence,
            key=lambda e: e.source_timestamp,
        )

        self.timeline = []
        for seq, ev in enumerate(sorted_evidence, 1):
            # Extract action description from content
            action = _extract_action(ev)
            event = TimelineEvent(
                sequence=seq,
                timestamp=ev.source_timestamp,
                agent_id=ev.source_agent_id,
                action=action,
                evidence_ids=[ev.evidence_id],
                confidence=ev.weight,  # Tier weight as confidence
            )
            self.timeline.append(event)

        # Flag gaps (>1 hour between consecutive events)
        self._flag_timeline_gaps()

        self.phase = "timeline_reconstruction"
        return self.timeline

    def _flag_timeline_gaps(self) -> None:
        """Annotate timeline events where significant gaps exist."""
        for i in range(1, len(self.timeline)):
            prev = self.timeline[i - 1]
            curr = self.timeline[i]
            try:
                prev_dt = _parse_iso(prev.timestamp)
                curr_dt = _parse_iso(curr.timestamp)
                gap = (curr_dt - prev_dt).total_seconds()
                if gap > 3600:  # >1 hour gap
                    hours = gap / 3600
                    curr.notes = f"GAP: {hours:.1f}h since previous event"
            except (ValueError, TypeError):
                pass

    # -- Phase 4a: Rule-Based Causal Indicators --

    def generate_causal_indicators(self) -> List[CausalIndicator]:
        """Generate automated causal indicators (Phase 4a).

        Three types of indicators:
        1. Temporal correlation — actions immediately preceding the incident
        2. Policy violation — actions violating known protocol rules
        3. Behavioral anomaly — actions deviating from baseline
        """
        self.causal_indicators = []

        if not self.timeline:
            self.reconstruct_timeline()

        # 1. Temporal correlation: events in the 1 hour before the incident
        incident_time = self.report.incident_time
        self._flag_temporal_correlations(incident_time)

        # 2. Policy violations: look for known violation patterns
        self._flag_policy_violations()

        # 3. Behavioral anomalies: flag deviations
        self._flag_behavioral_anomalies()

        self.phase = "causal_assessment"
        return self.causal_indicators

    def _flag_temporal_correlations(self, incident_time: str) -> None:
        """Flag events that occurred shortly before the incident."""
        try:
            incident_dt = _parse_iso(incident_time)
        except (ValueError, TypeError):
            return

        for event in self.timeline:
            try:
                event_dt = _parse_iso(event.timestamp)
                seconds_before = (incident_dt - event_dt).total_seconds()
                if 0 < seconds_before <= 3600:  # Within 1 hour before
                    confidence = min(1.0, 1.0 - (seconds_before / 3600))
                    self.causal_indicators.append(CausalIndicator(
                        indicator_type="temporal_correlation",
                        description=(
                            f"Action '{event.action}' by {event.agent_id} "
                            f"occurred {seconds_before:.0f}s before incident"
                        ),
                        agent_id=event.agent_id,
                        evidence_ids=event.evidence_ids,
                        rule_match_confidence=round(confidence, 3),
                    ))
            except (ValueError, TypeError):
                continue

    def _flag_policy_violations(self) -> None:
        """Flag evidence items that indicate protocol or policy violations."""
        violation_keywords = (
            "unauthorized", "violation", "breach", "denied",
            "forbidden", "rejected", "error", "failed",
            "deleted", "destroyed", "corrupted",
        )
        for ev in self.evidence:
            content_str = str(ev.content).lower() if ev.content else ""
            for keyword in violation_keywords:
                if keyword in content_str:
                    self.causal_indicators.append(CausalIndicator(
                        indicator_type="policy_violation",
                        description=(
                            f"Evidence {ev.evidence_id} from {ev.source_agent_id} "
                            f"contains policy-relevant keyword: '{keyword}'"
                        ),
                        agent_id=ev.source_agent_id,
                        evidence_ids=[ev.evidence_id],
                        rule_match_confidence=0.5,
                    ))
                    break  # One flag per evidence item

    def _flag_behavioral_anomalies(self) -> None:
        """Flag agents with unusually high activity in the evidence window."""
        # Count actions per agent
        agent_counts: Dict[str, int] = {}
        for event in self.timeline:
            agent_counts[event.agent_id] = agent_counts.get(event.agent_id, 0) + 1

        if not agent_counts:
            return

        avg = sum(agent_counts.values()) / len(agent_counts)
        for agent_id, count in agent_counts.items():
            if count > avg * 2 and count >= 3:
                self.causal_indicators.append(CausalIndicator(
                    indicator_type="behavioral_anomaly",
                    description=(
                        f"Agent {agent_id} has {count} actions in the evidence "
                        f"window (average: {avg:.1f}), indicating elevated activity"
                    ),
                    agent_id=agent_id,
                    evidence_ids=[
                        eid
                        for event in self.timeline
                        if event.agent_id == agent_id
                        for eid in event.evidence_ids
                    ],
                    rule_match_confidence=min(1.0, (count / avg - 1) / 2),
                ))

    # -- Phase 5: Finding Generation --

    def produce_finding(
        self,
        fault_allocation: Optional[List[FaultAllocation]] = None,
        no_fault_factors: Optional[List[str]] = None,
        recommendations: Optional[List[Dict[str, str]]] = None,
    ) -> ForensicFinding:
        """Produce the structured forensic finding.

        If timeline or causal indicators haven't been generated,
        they are produced automatically.
        """
        if not self.timeline:
            self.reconstruct_timeline()
        if not self.causal_indicators:
            self.generate_causal_indicators()

        by_tier = self.evidence_by_tier
        # Key evidence: top-tier items and those referenced by causal indicators
        indicator_evidence = set()
        for ci in self.causal_indicators:
            indicator_evidence.update(ci.evidence_ids)
        key_ids = (
            [e.evidence_id for e in by_tier[1]]
            + list(indicator_evidence)
        )

        finding = ForensicFinding(
            investigation_id=self.investigation_id,
            incident_id=self.report.incident_id,
            incident_type=self.report.incident_type,
            severity=self.report.severity,
            reported_by=self.report.reporter,
            reported_at=self.report.incident_time,
            description=self.report.description,
            subjects=list(self.report.subjects),
            reporters=[self.report.reporter],
            timeline=list(self.timeline),
            causal_indicators=list(self.causal_indicators),
            fault_allocation=fault_allocation or [],
            no_fault_factors=no_fault_factors or [],
            total_evidence_items=len(self.evidence),
            tier_1_count=len(by_tier[1]),
            tier_2_count=len(by_tier[2]),
            tier_3_count=len(by_tier[3]),
            tier_4_count=len(by_tier[4]),
            key_evidence_ids=list(dict.fromkeys(key_ids)),  # dedupe, preserve order
            recommendations=recommendations or [],
        )
        finding.compute_hash()
        self.phase = "finding_generation"
        return finding


def _extract_action(evidence: EvidenceRecord) -> str:
    """Extract a human-readable action description from evidence content."""
    content = evidence.content
    if isinstance(content, dict):
        # Try common fields
        for key in ("action", "event_type", "type", "description", "message"):
            if key in content:
                return str(content[key])
        return str(content)[:100]
    if isinstance(content, str):
        return content[:100]
    return f"{evidence.evidence_type} evidence"
