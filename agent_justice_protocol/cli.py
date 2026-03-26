"""CLI entry point for agent-justice-protocol.

Commands:
  investigate  Run a forensic investigation from evidence files
  file         File a dispute claim
  query        Check an agent's risk profile
  status       Show local store statistics
"""

import argparse
import json
import sys
from typing import List, Optional

from .schema import (
    AgentReference,
    ArbitrationDecision,
    DisputeClaim,
    EvidenceRecord,
    ForensicFinding,
    RiskProfile,
    risk_level_for_score,
)
from .store import JusticeStore
from .forensics import ForensicInvestigation, IncidentReport
from .risk import RiskEngine


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-justice",
        description="Agent Justice Protocol — forensic investigation, "
                    "dispute resolution, and risk assessment for the agent economy",
    )
    parser.add_argument(
        "--store",
        default=".ajp",
        help="Path to the AJP data directory (default: .ajp)",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # investigate
    p_inv = sub.add_parser(
        "investigate",
        help="Run a forensic investigation from evidence",
    )
    p_inv.add_argument("--reporter", required=True, help="Reporter agent ID")
    p_inv.add_argument(
        "--type",
        required=True,
        dest="incident_type",
        choices=[
            "service_failure", "data_loss", "unauthorized_action",
            "contractual_breach", "security_incident", "quality_deficiency",
            "timeout", "cascade_failure",
        ],
        help="Incident type",
    )
    p_inv.add_argument(
        "--severity",
        default="medium",
        choices=["critical", "high", "medium", "low"],
        help="Incident severity (default: medium)",
    )
    p_inv.add_argument("--description", required=True, help="Incident description")
    p_inv.add_argument(
        "--subject",
        action="append",
        default=[],
        help="Agent ID under investigation (can specify multiple)",
    )
    p_inv.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Path to evidence JSON file (can specify multiple)",
    )
    p_inv.add_argument("--json", action="store_true", help="Output as JSON")

    # file (dispute)
    p_file = sub.add_parser("file", help="File a dispute claim")
    p_file.add_argument("--claimant", required=True, help="Claimant agent ID")
    p_file.add_argument("--respondent", required=True, help="Respondent agent ID")
    p_file.add_argument("--finding", required=True, help="Finding ID to reference")
    p_file.add_argument(
        "--harm-type",
        required=True,
        choices=[
            "financial", "reputational", "data_loss",
            "service_disruption", "security_breach", "contractual_breach",
        ],
        help="Type of harm suffered",
    )
    p_file.add_argument("--harm-description", required=True, help="Description of harm")
    p_file.add_argument(
        "--remediation",
        default="compensation",
        choices=[
            "compensation", "service_credit", "reputation_adjustment",
            "behavioral_restriction", "apology", "human_escalation",
        ],
        help="Requested remediation type (default: compensation)",
    )
    p_file.add_argument("--amount", type=float, default=None, help="Quantified harm amount")
    p_file.add_argument("--currency", default="USD", help="Currency (default: USD)")
    p_file.add_argument("--json", action="store_true", help="Output as JSON")

    # query (risk profile)
    p_query = sub.add_parser("query", help="Check an agent's risk profile")
    p_query.add_argument("agent_id", help="Agent ID to query")
    p_query.add_argument("--json", action="store_true", help="Output as JSON")

    # status
    p_status = sub.add_parser("status", help="Show local store statistics")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def _cmd_investigate(args: argparse.Namespace) -> int:
    store = JusticeStore(args.store)

    reporter = AgentReference(agent_id=args.reporter)
    subjects = [AgentReference(agent_id=s) for s in args.subject]

    report = IncidentReport(
        reporter=reporter,
        incident_type=args.incident_type,
        severity=args.severity,
        description=args.description,
        subjects=subjects,
    )

    investigation = ForensicInvestigation(report)

    # Load evidence files
    for evidence_path in args.evidence:
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    investigation.add_evidence(EvidenceRecord.from_dict(item))
            else:
                investigation.add_evidence(EvidenceRecord.from_dict(data))
        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
            print(f"Warning: Could not load evidence from {evidence_path}: {e}",
                  file=sys.stderr)

    finding = investigation.produce_finding()
    store.append_finding(finding)

    if args.json:
        print(json.dumps(finding.to_dict(), indent=2))
    else:
        print(f"Investigation complete: {finding.finding_id}")
        print(f"  Incident: {finding.incident_type} ({finding.severity})")
        print(f"  Evidence items: {finding.total_evidence_items}")
        print(f"  Timeline events: {len(finding.timeline)}")
        print(f"  Causal indicators: {len(finding.causal_indicators)}")
        print(f"  Finding hash: {finding.finding_hash[:16]}...")

    _try_coc_record("INVESTIGATION_FINDING", {
        "investigation_id": finding.investigation_id,
        "finding_id": finding.finding_id,
        "finding_hash": finding.finding_hash,
        "severity": finding.severity,
    })

    return 0


def _cmd_file(args: argparse.Namespace) -> int:
    store = JusticeStore(args.store)

    # Look up the finding
    finding = store.get_finding(args.finding)
    if finding is None:
        print(f"Error: Finding {args.finding} not found in store", file=sys.stderr)
        return 1

    claim = DisputeClaim(
        claimant=AgentReference(agent_id=args.claimant),
        respondent=AgentReference(agent_id=args.respondent),
        finding_id=finding.finding_id,
        finding_hash=finding.finding_hash,
        harm_type=args.harm_type,
        harm_description=args.harm_description,
        requested_remediation_type=args.remediation,
        quantified_amount=args.amount,
        quantified_currency=args.currency,
        incident_id=finding.incident_id,
    )
    claim.compute_hash()
    store.append_claim(claim)

    tier = claim.select_tier()

    if args.json:
        output = claim.to_dict()
        output["selected_tier"] = tier
        print(json.dumps(output, indent=2))
    else:
        print(f"Dispute filed: {claim.claim_id}")
        print(f"  Claimant: {args.claimant}")
        print(f"  Respondent: {args.respondent}")
        print(f"  Harm: {args.harm_type}")
        if args.amount:
            print(f"  Amount: {args.amount} {args.currency}")
        print(f"  Resolution tier: {tier}")
        print(f"  Claim hash: {claim.claim_hash[:16]}...")

    _try_coc_record("DISPUTE_FILED", {
        "claim_id": claim.claim_id,
        "respondent": args.respondent,
        "harm_type": args.harm_type,
        "claim_hash": claim.claim_hash,
    })

    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    store = JusticeStore(args.store)

    # Check for existing profile
    profile = store.get_latest_profile(args.agent_id)

    if profile is None:
        # Compute a fresh profile from store data
        agent = AgentReference(agent_id=args.agent_id)
        findings = store.get_findings_for(args.agent_id)
        decisions = store.get_decisions()
        # Filter decisions where this agent was respondent
        relevant_decisions = [
            d for d in decisions
            if d.respondent_fault_pct > 0  # simplified check
        ]

        engine = RiskEngine()
        profile = engine.compute_profile(
            agent=agent,
            findings=findings,
            decisions=relevant_decisions,
            total_interactions=max(1, len(findings) * 10),  # estimate
        )
        store.append_profile(profile)

    if args.json:
        print(json.dumps(profile.to_dict(), indent=2))
    else:
        print(f"Risk Profile: {args.agent_id}")
        print(f"  Overall score: {profile.overall_score}/1000 "
              f"({profile.risk_level})")
        print(f"  Confidence: {profile.confidence}")
        print(f"  Trend: {profile.trend}")
        print(f"  Findings: {profile.findings_count}")
        print(f"  Disputes: {profile.disputes_count}")
        if profile.expected_loss_rate > 0:
            print(f"  Expected loss rate: {profile.expected_loss_rate}")
            print(f"  Recommended premium: {profile.recommended_premium_basis}")

    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    store = JusticeStore(args.store)
    stats = store.stats()

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print("Agent Justice Protocol — Store Status")
        print(f"  Directory: {stats['directory']}")
        print(f"  Investigations: {stats['investigations']['count']} "
              f"({stats['investigations']['file_size_bytes']} bytes)")
        print(f"  Disputes: {stats['disputes']['count']} "
              f"({stats['disputes']['file_size_bytes']} bytes)")
        print(f"  Decisions: {stats['decisions']['count']} "
              f"({stats['decisions']['file_size_bytes']} bytes)")
        print(f"  Risk profiles: {stats['risk_profiles']['count']} "
              f"({stats['risk_profiles']['file_size_bytes']} bytes)")

    return 0


def _try_coc_record(event_type: str, data: dict) -> None:
    """Optionally record event to a CoC chain if the package is installed."""
    try:
        from chain_of_consciousness import Chain  # type: ignore[import]
        import os

        chain_file = os.environ.get("COC_CHAIN_FILE")
        if not chain_file:
            return

        agent_id = os.environ.get("COC_AGENT_ID", "ajp-cli")
        chain = Chain(agent_id, storage=chain_file)
        chain.add(event_type, data)
    except ImportError:
        pass
    except Exception:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "investigate": _cmd_investigate,
        "file": _cmd_file,
        "query": _cmd_query,
        "status": _cmd_status,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
