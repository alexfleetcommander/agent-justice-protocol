"""Risk Assessment Engine — agent risk scoring and actuarial outputs.

Implements Module 3 (Section 7) of the AJP whitepaper:
- Risk score computation (Section 7.3)
- Actuarial outputs: ELR, loss distribution, premium basis (Section 7.4)
- Population-level analytics (Section 7.5)
- Temporal weighting and risk profile updates (Section 7.6)
"""

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .evidence import _parse_iso
from .schema import (
    AgentReference,
    ArbitrationDecision,
    DEFAULT_RISK_WEIGHTS,
    ForensicFinding,
    RISK_DIMENSIONS,
    RiskProfile,
    risk_level_for_score,
    _now_iso,
    _uuid,
)


# Temporal decay parameter (Section 7.6): half-life ~231 days
DEFAULT_DECAY_LAMBDA = 0.003
DEFAULT_ROLLING_WINDOW_DAYS = 365


def _temporal_weight(days_since: float, decay_lambda: float = DEFAULT_DECAY_LAMBDA) -> float:
    """Compute temporal weight: exp(-lambda * days_since_incident)."""
    return math.exp(-decay_lambda * max(0.0, days_since))


def _confidence(total_interactions: int) -> float:
    """Compute confidence from interaction count (Section 7.3).

    confidence = max(0.05, 1 - 1/(1 + 0.05 * total_interactions))
    """
    return max(0.05, 1.0 - 1.0 / (1.0 + 0.05 * total_interactions))


def _loading_factor(conf: float) -> float:
    """Compute loading factor for premium basis (Section 7.4).

    loading_factor = 0.5 / confidence
    """
    return 0.5 / max(conf, 0.05)


def _clamp(value: float, lo: float = 0.0, hi: float = 1000.0) -> int:
    """Clamp a float to [lo, hi] and round to int."""
    return int(max(lo, min(hi, round(value))))


# ---------------------------------------------------------------------------
# Risk Scoring Engine
# ---------------------------------------------------------------------------

class RiskEngine:
    """Computes risk profiles from forensic findings and dispute decisions.

    Usage:
        engine = RiskEngine()
        profile = engine.compute_profile(
            agent, findings, decisions,
            total_interactions=100,
        )
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        decay_lambda: float = DEFAULT_DECAY_LAMBDA,
        rolling_window_days: int = DEFAULT_ROLLING_WINDOW_DAYS,
    ) -> None:
        self.weights = weights or dict(DEFAULT_RISK_WEIGHTS)
        self.decay_lambda = decay_lambda
        self.rolling_window_days = rolling_window_days

    def _filter_by_window(
        self,
        findings: List[ForensicFinding],
        decisions: List[ArbitrationDecision],
        reference_time: Optional[datetime] = None,
    ) -> Tuple[List[ForensicFinding], List[ArbitrationDecision]]:
        """Filter records to the rolling window."""
        ref = reference_time or datetime.now(timezone.utc)
        cutoff = ref - timedelta(days=self.rolling_window_days)

        filtered_findings = []
        for f in findings:
            try:
                ts = _parse_iso(f.timestamp)
                if ts >= cutoff:
                    filtered_findings.append(f)
            except (ValueError, TypeError):
                filtered_findings.append(f)

        filtered_decisions = []
        for d in decisions:
            try:
                ts = _parse_iso(d.timestamp)
                if ts >= cutoff:
                    filtered_decisions.append(d)
            except (ValueError, TypeError):
                filtered_decisions.append(d)

        return filtered_findings, filtered_decisions

    def _incident_frequency_score(
        self,
        findings: List[ForensicFinding],
        total_interactions: int,
    ) -> Tuple[int, float]:
        """Compute incident frequency score (0-1000).

        Based on incidents per 1000 interactions.
        """
        if total_interactions == 0:
            return (0, 0.0)
        rate = (len(findings) / total_interactions) * 1000.0
        # Map rate to 0-1000 score (10+ per 1000 = max score)
        score = _clamp(rate * 100)
        return (score, round(rate, 4))

    def _severity_score(
        self, findings: List[ForensicFinding],
    ) -> Tuple[int, Dict[str, int]]:
        """Compute severity profile score.

        Weighted by severity: critical=4, high=3, medium=2, low=1.
        """
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        total_weight = 0.0
        for f in findings:
            sev = f.severity
            distribution[sev] = distribution.get(sev, 0) + 1
            total_weight += severity_weights.get(sev, 1)

        if not findings:
            return (0, distribution)

        # Normalize: max possible = 4 * len(findings)
        max_weight = 4 * len(findings)
        score = _clamp((total_weight / max_weight) * 1000)
        return (score, distribution)

    def _fault_history_score(
        self,
        agent_id: str,
        decisions: List[ArbitrationDecision],
    ) -> Tuple[int, int, float, int]:
        """Compute fault history score.

        Returns (score, disputes_at_fault, avg_fault_pct, disputes_no_fault).
        """
        at_fault = 0
        no_fault = 0
        fault_pcts: List[float] = []

        for d in decisions:
            # Check if agent is the respondent
            if d.respondent_fault_pct > 0:
                at_fault += 1
                fault_pcts.append(d.respondent_fault_pct)
            else:
                no_fault += 1

        avg_pct = statistics.mean(fault_pcts) if fault_pcts else 0.0
        total = at_fault + no_fault
        if total == 0:
            return (0, 0, 0.0, 0)

        fault_rate = at_fault / total
        score = _clamp(fault_rate * avg_pct / 100 * 1000)
        return (score, at_fault, round(avg_pct, 2), no_fault)

    def _cooperation_score(
        self,
        evidence_provision_rate: float = 1.0,
        response_rate: float = 1.0,
        adverse_inferences: int = 0,
    ) -> int:
        """Compute cooperation score (0-1000, higher = more cooperative).

        Note: In the risk formula, cooperation is inverted (1000 - score)
        so non-cooperation increases risk.
        """
        base = (evidence_provision_rate + response_rate) / 2 * 1000
        # Penalty for adverse inferences
        penalty = adverse_inferences * 100
        return _clamp(base - penalty)

    def _recovery_score(
        self,
        mean_time_to_resolution: int = 0,
        remediation_compliance_rate: float = 1.0,
    ) -> int:
        """Compute recovery capability score (0-1000, higher = better).

        Note: In the risk formula, recovery is inverted (1000 - score)
        so slow recovery increases risk.
        """
        # Compliance component (60% weight)
        compliance_component = remediation_compliance_rate * 600

        # Time component (40% weight) — fast is better
        # 0 seconds = perfect (400), >30 days = 0
        if mean_time_to_resolution <= 0:
            time_component = 400.0
        else:
            days = mean_time_to_resolution / 86400
            time_component = max(0.0, 400.0 * (1.0 - days / 30.0))

        return _clamp(compliance_component + time_component)

    def _actuarial_outputs(
        self,
        findings: List[ForensicFinding],
        decisions: List[ArbitrationDecision],
        total_interactions: int,
        conf: float,
    ) -> Dict[str, float]:
        """Compute actuarial outputs (Section 7.4)."""
        # Collect loss amounts from decisions
        losses = [
            d.compensation_amount
            for d in decisions
            if d.compensation_amount is not None and d.compensation_amount > 0
        ]

        if not losses or total_interactions == 0:
            return {
                "expected_loss_rate": 0.0,
                "loss_p50": 0.0,
                "loss_p90": 0.0,
                "loss_p99": 0.0,
                "recommended_premium_basis": 0.0,
            }

        # Expected Loss Rate
        total_loss = sum(losses)
        elr = total_loss / total_interactions

        # Loss severity distribution
        sorted_losses = sorted(losses)
        n = len(sorted_losses)

        def percentile(data: List[float], p: float) -> float:
            k = (n - 1) * p / 100
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[f]
            return data[f] * (c - k) + data[c] * (k - f)

        p50 = percentile(sorted_losses, 50) if n > 0 else 0.0
        p90 = percentile(sorted_losses, 90) if n > 0 else 0.0
        p99 = percentile(sorted_losses, 99) if n > 0 else 0.0

        # Premium basis
        loading = _loading_factor(conf)
        premium = elr * (1 + loading)

        return {
            "expected_loss_rate": round(elr, 6),
            "loss_p50": round(p50, 2),
            "loss_p90": round(p90, 2),
            "loss_p99": round(p99, 2),
            "recommended_premium_basis": round(premium, 6),
        }

    def compute_profile(
        self,
        agent: AgentReference,
        findings: List[ForensicFinding],
        decisions: List[ArbitrationDecision],
        total_interactions: int = 0,
        evidence_provision_rate: float = 1.0,
        response_rate: float = 1.0,
        adverse_inferences: int = 0,
        mean_time_to_resolution: int = 0,
        remediation_compliance_rate: float = 1.0,
        agent_class: str = "",
    ) -> RiskProfile:
        """Compute a complete risk profile for an agent.

        Args:
            agent: The agent to profile.
            findings: Forensic findings where this agent is a subject.
            decisions: Arbitration decisions involving this agent.
            total_interactions: Agent's total interaction count.
            evidence_provision_rate: Rate of evidence provision in investigations.
            response_rate: Rate of responding to dispute claims.
            adverse_inferences: Count of adverse inferences received.
            mean_time_to_resolution: Average seconds to resolve remediation orders.
            remediation_compliance_rate: Fraction of remediation orders completed.
            agent_class: Agent classification for comparable analysis.
        """
        # Filter to rolling window
        filtered_findings, filtered_decisions = self._filter_by_window(
            findings, decisions,
        )

        # Confidence
        conf = _confidence(total_interactions)

        # Dimension scores
        freq_score, freq_rate = self._incident_frequency_score(
            filtered_findings, total_interactions,
        )
        sev_score, sev_dist = self._severity_score(filtered_findings)
        fault_score, at_fault, avg_fault, no_fault = self._fault_history_score(
            agent.agent_id, filtered_decisions,
        )
        coop_score = self._cooperation_score(
            evidence_provision_rate, response_rate, adverse_inferences,
        )
        rec_score = self._recovery_score(
            mean_time_to_resolution, remediation_compliance_rate,
        )

        # Overall risk score (Section 7.3)
        w = self.weights
        overall = (
            w["incident_frequency"] * freq_score
            + w["severity_profile"] * sev_score
            + w["fault_history"] * fault_score
            + w["cooperation_score"] * (1000 - coop_score)
            + w["recovery_capability"] * (1000 - rec_score)
        )
        overall_score = _clamp(overall)

        # Actuarial outputs
        actuarial = self._actuarial_outputs(
            filtered_findings, filtered_decisions, total_interactions, conf,
        )

        # Risk factors
        risk_factors = []
        if freq_score > 500:
            risk_factors.append({
                "factor": "High incident frequency",
                "severity": "high",
                "evidence": f"{len(filtered_findings)} incidents in window",
            })
        if fault_score > 500:
            risk_factors.append({
                "factor": "Poor fault history",
                "severity": "high",
                "evidence": f"{at_fault} disputes at fault, avg {avg_fault}%",
            })
        if coop_score < 500:
            risk_factors.append({
                "factor": "Low cooperation in investigations",
                "severity": "medium",
                "evidence": f"{adverse_inferences} adverse inferences",
            })

        # Determine trend (simple: compare first half vs second half of window)
        trend = self._compute_trend(filtered_findings)

        now = _now_iso()
        profile = RiskProfile(
            subject=agent,
            overall_score=overall_score,
            confidence=round(conf, 4),
            trend=trend,
            incident_frequency_score=freq_score,
            incidents_per_1000=freq_rate,
            severity_score=sev_score,
            severity_distribution=sev_dist,
            fault_history_score=fault_score,
            disputes_at_fault=at_fault,
            average_fault_pct=avg_fault,
            disputes_no_fault=no_fault,
            cooperation_score=coop_score,
            evidence_provision_rate=evidence_provision_rate,
            response_rate=response_rate,
            adverse_inferences=adverse_inferences,
            recovery_score=rec_score,
            mean_time_to_resolution=mean_time_to_resolution,
            remediation_compliance_rate=remediation_compliance_rate,
            risk_factors=risk_factors,
            agent_class=agent_class,
            expected_loss_rate=actuarial["expected_loss_rate"],
            loss_p50=actuarial["loss_p50"],
            loss_p90=actuarial["loss_p90"],
            loss_p99=actuarial["loss_p99"],
            recommended_premium_basis=actuarial["recommended_premium_basis"],
            data_window_start=(
                datetime.now(timezone.utc) - timedelta(days=self.rolling_window_days)
            ).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            data_window_end=now,
            findings_count=len(filtered_findings),
            disputes_count=len(filtered_decisions),
            generated_at=now,
        )
        profile.compute_hash()
        return profile

    def _compute_trend(self, findings: List[ForensicFinding]) -> str:
        """Compute risk trend by comparing incident rate in first vs second half."""
        if len(findings) < 2:
            return "stable"
        mid = len(findings) // 2
        first_half = findings[:mid]
        second_half = findings[mid:]
        if len(second_half) > len(first_half) * 1.5:
            return "degrading"
        if len(second_half) < len(first_half) * 0.5:
            return "improving"
        return "stable"


# ---------------------------------------------------------------------------
# Population-Level Analytics (Section 7.5)
# ---------------------------------------------------------------------------

def population_risk_summary(
    profiles: List[RiskProfile],
) -> Dict[str, Any]:
    """Compute population-level risk analytics.

    Returns aggregate statistics across all provided risk profiles.
    """
    if not profiles:
        return {
            "total_agents": 0,
            "risk_distribution": {},
            "average_score": 0,
            "median_score": 0,
        }

    scores = [p.overall_score for p in profiles]
    # Risk level distribution
    distribution: Dict[str, int] = {}
    for p in profiles:
        level = p.risk_level
        distribution[level] = distribution.get(level, 0) + 1

    # Class-level aggregation
    class_scores: Dict[str, List[int]] = {}
    for p in profiles:
        cls = p.agent_class or "unclassified"
        class_scores.setdefault(cls, []).append(p.overall_score)

    class_averages = {
        cls: round(statistics.mean(s), 1)
        for cls, s in class_scores.items()
    }

    return {
        "total_agents": len(profiles),
        "risk_distribution": distribution,
        "average_score": round(statistics.mean(scores), 1),
        "median_score": round(statistics.median(scores), 1),
        "min_score": min(scores),
        "max_score": max(scores),
        "class_averages": class_averages,
    }
