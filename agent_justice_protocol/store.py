"""Local append-only JSONL store for AJP records.

Stores investigations, disputes, decisions, and risk profiles.
Same pattern as Chain of Consciousness and Agent Rating Protocol:
one JSON record per line, append-only, no deletion.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from .schema import (
    ArbitrationDecision,
    DisputeClaim,
    ForensicFinding,
    RiskProfile,
)

T = TypeVar("T")


class JusticeStore:
    """Append-only local store backed by JSONL files.

    Maintains separate files for each record type:
    - investigations.jsonl — ForensicFinding records
    - disputes.jsonl — DisputeClaim records
    - decisions.jsonl — ArbitrationDecision records
    - risk_profiles.jsonl — RiskProfile records
    """

    def __init__(self, directory: str = ".ajp") -> None:
        self.directory = Path(directory)
        self._lock = threading.Lock()
        self.directory.mkdir(parents=True, exist_ok=True)

    def _file_path(self, record_type: str) -> Path:
        return self.directory / f"{record_type}.jsonl"

    def _append(self, record_type: str, data: Dict[str, Any]) -> None:
        path = self._file_path(record_type)
        line = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _read_all(
        self,
        record_type: str,
        from_dict: Callable[[Dict[str, Any]], T],
    ) -> List[T]:
        path = self._file_path(record_type)
        if not path.exists():
            return []
        records: List[T] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    records.append(from_dict(d))
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        return records

    # -- Investigations (ForensicFinding) --

    def append_finding(self, finding: ForensicFinding) -> str:
        if not finding.finding_hash:
            finding.compute_hash()
        self._append("investigations", finding.to_dict())
        return finding.finding_id

    def get_findings(self) -> List[ForensicFinding]:
        return self._read_all("investigations", ForensicFinding.from_dict)

    def get_finding(self, finding_id: str) -> Optional[ForensicFinding]:
        for f in self.get_findings():
            if f.finding_id == finding_id:
                return f
        return None

    def get_findings_for(self, agent_id: str) -> List[ForensicFinding]:
        """Get all findings where agent_id is a subject."""
        results = []
        for f in self.get_findings():
            if any(s.agent_id == agent_id for s in f.subjects):
                results.append(f)
        return results

    # -- Disputes (DisputeClaim) --

    def append_claim(self, claim: DisputeClaim) -> str:
        if not claim.claim_hash:
            claim.compute_hash()
        self._append("disputes", claim.to_dict())
        return claim.claim_id

    def get_claims(self) -> List[DisputeClaim]:
        return self._read_all("disputes", DisputeClaim.from_dict)

    def get_claim(self, claim_id: str) -> Optional[DisputeClaim]:
        for c in self.get_claims():
            if c.claim_id == claim_id:
                return c
        return None

    def get_claims_against(self, agent_id: str) -> List[DisputeClaim]:
        return [c for c in self.get_claims() if c.respondent.agent_id == agent_id]

    def get_claims_by(self, agent_id: str) -> List[DisputeClaim]:
        return [c for c in self.get_claims() if c.claimant.agent_id == agent_id]

    # -- Decisions (ArbitrationDecision) --

    def append_decision(self, decision: ArbitrationDecision) -> str:
        if not decision.decision_hash:
            decision.compute_hash()
        self._append("decisions", decision.to_dict())
        return decision.decision_id

    def get_decisions(self) -> List[ArbitrationDecision]:
        return self._read_all("decisions", ArbitrationDecision.from_dict)

    def get_decision(self, decision_id: str) -> Optional[ArbitrationDecision]:
        for d in self.get_decisions():
            if d.decision_id == decision_id:
                return d
        return None

    def get_decisions_for_dispute(self, dispute_id: str) -> List[ArbitrationDecision]:
        return [d for d in self.get_decisions() if d.dispute_id == dispute_id]

    # -- Risk Profiles --

    def append_profile(self, profile: RiskProfile) -> str:
        if not profile.profile_hash:
            profile.compute_hash()
        self._append("risk_profiles", profile.to_dict())
        return profile.profile_id

    def get_profiles(self) -> List[RiskProfile]:
        return self._read_all("risk_profiles", RiskProfile.from_dict)

    def get_latest_profile(self, agent_id: str) -> Optional[RiskProfile]:
        """Get the most recent risk profile for an agent."""
        profiles = [
            p for p in self.get_profiles()
            if p.subject.agent_id == agent_id
        ]
        if not profiles:
            return None
        return max(profiles, key=lambda p: p.generated_at)

    # -- Statistics --

    def stats(self) -> Dict[str, Any]:
        findings = self.get_findings()
        claims = self.get_claims()
        decisions = self.get_decisions()
        profiles = self.get_profiles()

        def _file_size(name: str) -> int:
            p = self._file_path(name)
            return p.stat().st_size if p.exists() else 0

        return {
            "directory": str(self.directory),
            "investigations": {
                "count": len(findings),
                "file_size_bytes": _file_size("investigations"),
            },
            "disputes": {
                "count": len(claims),
                "file_size_bytes": _file_size("disputes"),
            },
            "decisions": {
                "count": len(decisions),
                "file_size_bytes": _file_size("decisions"),
            },
            "risk_profiles": {
                "count": len(profiles),
                "file_size_bytes": _file_size("risk_profiles"),
            },
        }
