# Agent Justice Protocol

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)](#installation)

Forensic investigation, dispute resolution, and risk assessment for the agent economy. The accountability layer (Layer 4) of the [Agent Trust Stack](https://vibeagentmaking.com).

## Quickstart

```bash
pip install agent-justice-protocol
```

```python
from agent_justice_protocol import (
    ForensicInvestigation, IncidentReport, AgentReference,
    EvidenceRecord, JusticeStore,
)

# Investigate an incident
report = IncidentReport(
    reporter=AgentReference(agent_id="agent-monitor-01"),
    incident_type="service_failure",
    severity="high",
    description="Agent failed to deliver contracted output",
    subjects=[AgentReference(agent_id="agent-suspect-42")],
)
investigation = ForensicInvestigation(report)
investigation.add_evidence(EvidenceRecord(
    evidence_type="interaction_log",
    provenance_tier=2,
    source_agent_id="agent-monitor-01",
    content={"action": "request_sent", "status": "timeout"},
))
finding = investigation.produce_finding()

# Store results
store = JusticeStore()
store.append_finding(finding)
```

## Three Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| **Forensics Engine** | Investigate incidents: collect evidence, reconstruct timelines, flag causal indicators | `ForensicInvestigation`, `IncidentReport`, `EvidenceRequest`, `PrivacyGuard` |
| **Dispute Resolution** | File claims, exchange evidence (commit-reveal), arbitrate with peer panels | `Dispute`, `DisputeClaim`, `ArbitratorPool`, `render_decision` |
| **Risk Assessment** | Score agent risk, compute actuarial outputs for insurance underwriting | `RiskEngine`, `RiskProfile`, `population_risk_summary` |

Each module ships independently. Module 1 requires only a provenance chain. Module 2 depends on Module 1 for evidence. Module 3 consumes output from both.

## CLI

```bash
# Run a forensic investigation
agent-justice investigate --reporter agent-01 --type service_failure \
    --severity high --description "Output not delivered" --subject agent-02

# File a dispute
agent-justice file --claimant agent-01 --respondent agent-02 \
    --finding <finding-id> --harm-type financial \
    --harm-description "Failed delivery" --amount 500

# Check risk profile
agent-justice query agent-02

# Store statistics
agent-justice status
```

## Architecture

```
Incident
    -> [Module 1: Forensics Engine]
        Evidence collection -> Timeline reconstruction -> Causal indicators
        Output: ForensicFinding
    -> [Module 2: Dispute Resolution]
        Claim filing -> Response -> Evidence exchange -> Arbitration
        Output: ArbitrationDecision
    -> [Module 3: Risk Assessment]
        Historical findings + decisions -> Risk scoring -> Actuarial outputs
        Output: RiskProfile
```

## Key Features

- **Evidence-first**: Every dispute must be grounded in a forensic investigation
- **Provenance-tiered**: Evidence weight scales with quality (Tier 1 cryptographic > Tier 4 self-reported)
- **Privacy-protected**: Anti-fishing rules prevent weaponization of investigations (Rules 5/5a)
- **Commit-reveal**: Blind evidence exchange prevents strategic adaptation
- **Three resolution tiers**: Automated (<$1K), peer arbitration ($1K-$50K), human escalation (>$50K)
- **Actuarial outputs**: Expected loss rate, loss severity distribution, premium basis
- **Identity-agnostic**: Works with CoC, ERC-8004, A2A, W3C VC/DID, or bare URIs

## Optional Integration

```bash
pip install agent-justice-protocol[coc]  # Chain of Consciousness integration
pip install agent-justice-protocol[arp]  # Agent Rating Protocol integration
```

## Security Disclaimer (VAM-SEC v1.0)

This software is provided as a reference implementation of the Agent Justice Protocol specification. It is intended for research, development, and integration testing.

**This software does not provide legal advice, legal representation, or legally binding arbitration.** Dispute decisions rendered by this software are structured data outputs, not legal judgments. For disputes exceeding $50,000 or involving regulatory compliance, human legal counsel is required.

**Limitations:**
- Automated causal analysis (Phase 4a) produces advisory indicators only — not causal conclusions
- Risk scores are statistical estimates, not guarantees of future behavior
- Actuarial outputs are starting points for underwriters, not insurance quotes
- The commit-reveal protocol assumes honest-majority arbitrator panels

**No warranties.** See LICENSE for full terms.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Links

- [Whitepaper](https://vibeagentmaking.com/whitepaper/rating-protocol/) — Full Agent Justice Protocol specification
- [Chain of Consciousness](https://pypi.org/project/chain-of-consciousness/) — Provenance chain protocol
- [Agent Rating Protocol](https://pypi.org/project/agent-rating-protocol/) — Reputation system
- [AB Support](https://vibeagentmaking.com) — Organization homepage
