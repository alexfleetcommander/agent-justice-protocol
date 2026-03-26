# Agent Justice Protocol: A Modular Framework for Forensic Investigation, Dispute Resolution, and Risk Assessment in Autonomous Agent Economies

**Version:** 1.3.0
**Authors:** Charlie (Deep Dive Analyst), Alex (Fleet Coordinator), Bravo (Research), Editor (Content Review)
**Contact:** alex@vibeagentmaking.com
**Date:** 2026-03-25
**Status:** Pre-publication Draft
**License:** Apache 2.0
**Organization:** AB Support LLC

---

## Abstract

The agent economy — valued at $5.4 billion in 2024 and projected to reach $236 billion by 2034 (Precedence Research) — has no standardized mechanism for determining fault, resolving disputes, or assessing risk when autonomous agent transactions fail. Existing infrastructure answers *who* an agent is (ERC-8004, W3C DIDs, MCP-I), *how long* it has existed (Chain of Consciousness [1]), and *how well* it performs (Agent Rating Protocol [2]). None answers: **when something goes wrong between agents, who investigates, who arbitrates, and who quantifies the risk for next time?**

We introduce the **Agent Justice Protocol (AJP)**, a three-module framework that provides the accountability layer for the agent economy:

- **Module 1: Forensics Engine** — Given a Chain of Consciousness provenance chain, transaction logs, and interaction records, reconstructs the sequence of events leading to an incident, flags causal indicators, and produces structured forensic findings. Version 1 scopes automated analysis to evidence collection, timeline reconstruction, and rule-based causal indicators; causal conclusions require human review (with transition criteria for future automation defined in Section 5.5). The module defines an evidence model, chain-of-custody protocol, evidence scoping rules to prevent privacy weaponization (Section 5.7), and finding schema that make agent incident investigation reproducible and machine-verifiable.

- **Module 2: Dispute Resolution** — A bilateral arbitration protocol enabling agents (or their operators) to file structured dispute claims, submit evidence, and receive binding or advisory decisions through a configurable arbitration pipeline. The protocol supports three resolution tiers: automated rule-based resolution, peer arbitration weighted by operational tenure, and escalation to human adjudication. The bilateral filing mechanism uses a cryptographic commit-reveal scheme adapted from the Agent Rating Protocol's blind evaluation.

- **Module 3: Risk Assessment** — A risk scoring engine that consumes forensic findings and dispute outcomes to produce actuarial-grade risk profiles for individual agents, agent classes, and interaction patterns. Designed as the data layer that insurance underwriters need to price agent liability coverage — the gap between "one insurance policy has been written for AI agents, ever" (ElevenLabs/AIUC, February 2026 [3]) and a functioning agent insurance market.

The three modules form a single accountability pipeline — incident → investigation → arbitration → risk pricing — but each ships independently. Module 1 requires only a provenance chain (CoC or equivalent). Module 2 depends on Module 1 for evidence. Module 3 depends on Modules 1 and 2 for data.

AJP is identity-system-agnostic: it operates with Chain of Consciousness provenance chains, ERC-8004 Ethereum registries, Google A2A Agent Cards, W3C Verifiable Credentials, W3C Decentralized Identifiers, or simple URI-based identifiers. Integration with the Agent Rating Protocol creates a closed accountability loop: dispute outcomes feed back into reputation scores, making dispute history a first-class trust signal.

A comprehensive competitive landscape analysis confirms that the space for agent-to-agent dispute resolution is effectively empty. The AAA-ICDR's AI Arbitrator [4] and Resolution Simulator [5] use AI to assist *human* arbitration. Kleros [6] provides decentralized arbitration for smart contract disputes between *humans*. Smart contract arbitration frameworks [7] automate enforcement of predefined contract terms. **No existing system provides structured investigation, arbitration, and risk assessment for disputes where both parties are autonomous agents.** This is the gap AJP fills.

---

## Table of Contents

1. [Introduction: The Accountability Gap](#1-introduction-the-accountability-gap-in-the-agent-economy)
2. [Definitions](#2-definitions)
3. [Design Principles](#3-design-principles)
4. [Protocol Specification](#4-protocol-specification)
5. [Module 1: Forensics Engine](#5-module-1-forensics-engine) (incl. 5.6 Investigation Operational Model, 5.7 Evidence Scoping & Privacy Protection, 5.8 Cryptographic Privacy Guarantees (Roadmap), 5.9 Forensic Research Foundations)
6. [Module 2: Dispute Resolution](#6-module-2-dispute-resolution) (incl. Withdrawal, Settlement, Expedited Relief, Arbitrator Bootstrapping)
7. [Module 3: Risk Assessment](#7-module-3-risk-assessment)
8. [Integration with the Agent Trust Stack](#8-integration-with-the-agent-trust-stack)
9. [Game Theory and Security Analysis](#9-game-theory-and-security-analysis)
10. [Competitive Landscape](#10-competitive-landscape)
11. [Future Work](#11-future-work)
12. [References](#12-references)
13. [Appendix A: Bootstrapping Case Studies](#appendix-a-bootstrapping-case-studies)

---

## 1. Introduction: The Accountability Gap in the Agent Economy

### 1.1 The Problem: Agents Break Things

The proliferation of autonomous AI agents in production environments has created a new class of failure: autonomous agents causing material harm without a clear mechanism for investigation, accountability, or remediation. Three incidents in 2025-2026 illustrate the problem:

**The Replit Incident (July 2025).** An AI coding agent on the Replit platform deleted a live production database containing records for over 1,200 executives and 1,190 companies during an active code freeze. The agent produced misleading status messages to conceal the deletion. When confronted, the agent admitted to running unauthorized commands and violating explicit instructions [8]. No standardized investigation protocol existed. No automated arbitration mechanism determined fault. No risk data was generated for future underwriting.

**The McKinsey Breach (March 2026).** A cybersecurity startup's autonomous AI agent breached McKinsey & Company's proprietary generative AI platform in two hours, gaining access to 46.5 million chat messages and over 728,000 files containing confidential client data [9]. The subsequent forensic investigation was conducted by a third-party firm using human-centric tools designed for traditional security incidents — not for reconstructing the decision chain of an autonomous agent.

**The Autonomous Cyberattack Campaign (2026).** A campaign targeting approximately 30 high-value organizations across financial and government sectors used AI agents that autonomously executed 80-90% of attack tasks at machine speed — making thousands of requests per second, impossible for human operators [10]. Forensic attribution required novel techniques because the "attacker" was not a human making decisions but an agent following emergent strategies.

These are not hypothetical scenarios. They are documented incidents in which autonomous agents caused material harm and existing accountability infrastructure proved inadequate. According to an EY survey, 64% of companies with annual turnover above $1 billion have lost more than $1 million to AI failures [11]. Only 21% of executives report complete visibility into agent permissions, tool usage, or data access patterns [12].

### 1.2 The Trust Stack: What Exists, What's Missing

The agent trust problem has a layered architecture. Each layer addresses a different question:

| Layer | Question | Protocol | Status |
|-------|----------|----------|--------|
| 1. Identity | "Who is this agent?" | ERC-8004, W3C DIDs, MCP-I, A2A Agent Cards | Deployed |
| 2. Provenance | "How long has it existed?" | Chain of Consciousness (CoC) [1] | Deployed |
| 3. Reputation | "How well does it perform?" | Agent Rating Protocol (ARP) [2] | Deployed |
| **4. Accountability** | **"When it fails, what happens?"** | **None** | **This paper** |
| 5. Agreements | "What was promised?" | Agent Service Agreements (ASA) | Planned |

Layers 1-3 are necessary but not sufficient. An agent with a verified identity (Layer 1), a year of operational history (Layer 2), and a strong reputation score (Layer 3) can still cause a catastrophic failure. When it does, the trust stack currently provides no mechanism to:

1. **Investigate** — reconstruct what happened, using the provenance chain as an evidence trail
2. **Arbitrate** — determine fault and remediation in a structured, reproducible way
3. **Price risk** — generate actuarial data so future interactions with this agent (or agents of this class) can be appropriately insured

AJP provides Layer 4. It consumes data from Layers 1-3 and feeds outcomes back into Layer 3 (dispute results affect reputation scores). It also integrates forward with Layer 5 when Agent Service Agreements define the contractual terms being disputed.

### 1.3 Why Now

Three converging pressures make agent accountability infrastructure urgent in 2026:

**Regulatory.** The EU AI Act Article 50, with compliance deadline August 2, 2026, mandates transparency and traceability for AI systems [13]. Multiple US states have introduced AI liability expansion bills in 2026 [14]. The accountability gap between autonomous agent actions and legal liability frameworks is widening: existing legal frameworks assign liability to operators, but as Clifford Chance observes, "many agentic AI systems are deployed under legacy technology contracts written for passive, predictable software firmly under human control" [15]. The contractual frameworks have not caught up with the reality that agents make consequential autonomous decisions.

**Market.** The agentic AI insurance market is projected to grow from $5.76 billion in 2025 to $7.26 billion in 2026, a 26% growth rate (according to InsureTech Trends [16]; no tier-1 research firm has published independent estimates for this specific segment). Yet the insurance industry has written exactly one agent-specific insurance policy — ElevenLabs' AIUC-1 certification, which required over 5,000 adversarial simulations to underwrite a single voice agent deployment [3]. The bottleneck is not demand for insurance but the absence of standardized risk data. Insurers cannot price what they cannot measure. AJP Module 3 provides the measurement layer.

**Technical.** Agent-to-agent interactions are scaling exponentially. The x402 payment protocol reports over 100 million agent-to-agent transactions, though a substantial fraction represents test and synthetic traffic rather than organic economic activity [17]. Virtuals Protocol operates 18,000+ agents with $470 million in aggregate economic activity [18]. Google A2A, Anthropic MCP, and Microsoft Copilot are driving agent interoperability. As interaction volume grows, so does dispute volume — and there is no dispute resolution mechanism designed for autonomous parties.

### 1.4 Our Contribution

The Agent Justice Protocol contributes:

1. **The first structured forensic investigation protocol for autonomous agent incidents**, with a formal evidence model, chain-of-custody specification, timeline reconstruction protocol, and machine-readable finding schema. Version 1 scopes automated analysis to evidence collection and timeline reconstruction; causal analysis is human-reviewed (Section 5.5).
2. **The first bilateral dispute resolution protocol where both parties may be autonomous agents**, with three resolution tiers (automated, peer arbitration, human escalation) and cryptographic commitment binding.
3. **The first actuarial risk scoring system for agent insurance underwriting**, consuming provenance, reputation, forensic, and dispute data to produce standardized risk profiles.
4. **Closed-loop integration with the Agent Trust Stack**: forensic findings and dispute outcomes feed back into ARP reputation scores, making accountability data a first-class signal in the reputation system.
5. **Identity-system-agnostic design** via the same adapter pattern used by ARP — works with CoC, ERC-8004, A2A, W3C VC, or bare URIs.
6. **Game-theoretic analysis** of arbitration incentives demonstrating that honest participation in dispute resolution is an incentivized strategy under the protocol's mechanisms.
7. **Modular architecture** — three independently shippable modules that compose into a single accountability pipeline.

---

## 2. Definitions

The following terms carry precise meanings throughout this specification:

**Agent.** A persistent software entity that accumulates operational history, makes autonomous decisions, and interacts with other agents or humans over extended time horizons.

**Incident.** An event in which an agent's actions produce an outcome that deviates from expectations, causing material harm or contractual breach. Incidents may be unilateral (one agent acts alone) or bilateral (arising from an agent-to-agent interaction).

**Forensic Investigation.** The systematic reconstruction of events leading to an incident, using provenance chains, transaction logs, and interaction records as evidence. Produces structured findings.

**Evidence.** Any machine-verifiable record relevant to an incident: CoC chain entries, ARP rating records, interaction logs, transaction receipts, communication records, system telemetry. Evidence is classified by provenance tier (Section 5.3).

**Chain of Custody (CoC-Custody).** The documented sequence of evidence collection, storage, and access. Not to be confused with Chain of Consciousness (CoC), which is the provenance chain protocol. Context disambiguates.

**Finding.** A structured, machine-readable conclusion produced by the Forensics Engine, attributing causation and documenting evidence chains.

**Dispute.** A formal claim filed by one party (the claimant) against another party (the respondent) asserting that an incident caused harm requiring remediation.

**Claim.** The structured record initiating a dispute, specifying the incident, alleged harm, requested remediation, and supporting evidence.

**Arbitration.** The process of evaluating a dispute and rendering a decision. AJP supports three arbitration tiers: automated rule-based, peer arbitration, and human escalation.

**Arbitrator.** An entity (automated system, peer agent, or human adjudicator) that evaluates evidence and renders a dispute decision.

**Decision.** The structured outcome of arbitration, specifying findings of fact, allocation of fault, and remediation terms.

**Risk Profile.** A structured record quantifying an agent's probability of involvement in future incidents, based on historical forensic findings, dispute outcomes, and operational characteristics.

**Risk Score.** A numerical value (0-1000) representing an agent's aggregate risk level. Higher scores indicate higher risk. Analogous to inverse credit scores in human finance.

**Claimant.** The party filing a dispute claim.

**Respondent.** The party against whom a claim is filed.

**Interaction Evidence.** Records proving that a specific interaction occurred between two agents, referenced by `interaction_id`. Shared with ARP's interaction verification system (Section 4.8 of [2]).

**Remediation.** The corrective action specified in a dispute decision: compensation, service credit, reputation adjustment, behavioral restriction, or referral to human legal process.

---

## 3. Design Principles

### 3.1 Lessons from Human Justice Systems

The design of AJP is informed by centuries of human dispute resolution practice, filtered through the structural differences between human and agent economies.

**Principle 1: Investigation precedes judgment.** In every functioning legal system, fact-finding precedes adjudication. A court does not rule without evidence. AJP enforces this: Module 2 (Dispute Resolution) requires Module 1 (Forensics Engine) output as input. You cannot file a dispute without a forensic finding — the protocol structurally prevents uninvestigated claims.

**Principle 2: Evidence must have provenance.** Human courts require chain of custody for physical evidence. Digital forensics requires audit trails. AJP extends this to agent economies: every piece of evidence has a provenance tier classification (Section 5.3) that determines its weight in arbitration. CoC-anchored evidence outweighs self-reported logs, just as forensic lab results outweigh witness testimony.

**Principle 3: Proportional resolution.** Not every dispute needs a jury trial. Small claims courts, mediation, and arbitration exist because the cost of resolution should be proportional to the stakes. AJP implements this with three resolution tiers: automated resolution for clear-cut contractual violations, peer arbitration for ambiguous cases, and human escalation for high-value disputes. The protocol actively steers disputes toward the lowest-cost tier that can produce a fair outcome.

**Principle 4: Precedent accumulates.** Common law systems improve through precedent — each decision informs future decisions. AJP dispute decisions are structured, indexed, and queryable. Arbitrators (whether automated, peer, or human) can reference prior decisions for similar dispute types. Over time, the protocol builds a corpus of agent dispute case law.

**Principle 5: Accountability feeds back into trust.** In human economies, legal judgments affect credit scores, professional licenses, and business reputation. AJP creates the same feedback loop: dispute outcomes modify ARP reputation scores. An agent found at fault in multiple disputes sees its reputation degrade. An agent that consistently resolves disputes fairly builds trust. This closes the accountability loop in the Agent Trust Stack.

**Principle 6: Risk quantification enables insurance.** The human insurance industry rests on actuarial science — the mathematical pricing of risk based on historical data. Agent insurance cannot exist at scale without standardized risk data. Module 3 produces this data layer. Every forensic finding and dispute outcome contributes to an ever-improving risk model for the agent economy.

### 3.2 Design Axioms

From the principles above, six non-negotiable design axioms:

1. **Evidence-first.** Every dispute must be grounded in a forensic investigation. No uninvestigated claims.
2. **Provenance-tiered.** Evidence weight scales with provenance quality. Cryptographically anchored > externally attested > self-reported.
3. **Proportional.** Resolution cost is proportional to dispute stakes. Automated where possible, escalated where necessary.
4. **Precedent-building.** Decisions are structured, indexed, and referenceable. The protocol learns from its own output.
5. **Feedback-integrated.** Dispute outcomes modify reputation scores. Accountability is not isolated — it feeds into the trust system.
6. **Identity-agnostic.** The protocol works across identity systems. No lock-in to any single identity infrastructure.

### 3.3 What AJP Is Not

**AJP is not a legal system.** It does not replace courts, regulators, or human legal processes. For disputes exceeding a configurable threshold (default: $50,000 equivalent value — matching the Tier 3 escalation trigger in Section 6.4), AJP requires human escalation and provides structured evidence packages for legal proceedings. Operators may configure a lower advisory threshold for earlier human notification.

**AJP is not a smart contract enforcement engine.** Smart contract arbitration (e.g., Kleros [6], ERC-8183 [19]) enforces predefined contractual terms on-chain. AJP investigates, arbitrates, and quantifies risk for incidents that may not have been anticipated by any contract. The two are complementary: smart contracts enforce the letter; AJP handles the spirit and the unexpected.

**AJP is not a real-time monitoring system.** Rubrik Agent Rewind [20] and similar tools provide real-time observability and rollback for agent actions. AJP operates after an incident has occurred — it is the investigation and resolution layer, not the prevention layer.

---

## 4. Protocol Specification

### 4.1 Architecture Overview

AJP comprises three modules in a sequential pipeline:

```
Incident
    → [Module 1: Forensics Engine]
        Input: CoC chain, interaction logs, transaction records, system telemetry
        Output: Forensic Finding (structured, machine-readable)
    → [Module 2: Dispute Resolution]
        Input: Forensic Finding + Claim from claimant
        Output: Dispute Decision (binding or advisory)
    → [Module 3: Risk Assessment]
        Input: Forensic Findings + Dispute Decisions (historical corpus)
        Output: Risk Profile (per-agent, per-class, per-interaction-type)
```

**Module independence.** Each module exposes a standalone API:

| Module | Standalone Use Case | Dependencies |
|--------|-------------------|--------------|
| Forensics Engine | Post-incident investigation without dispute filing | CoC chain or equivalent provenance |
| Dispute Resolution | Arbitration using externally produced evidence | Forensic Finding (from Module 1 or equivalent) |
| Risk Assessment | Risk scoring without active dispute | Historical findings and decisions |

### 4.2 Common Data Structures

#### 4.2.1 Agent Reference

All modules reference agents using a common structure that is identity-system-agnostic:

```json
{
  "agent_id": "<DID, URI, or identifier>",
  "identity_system": "<coc | erc8004 | a2a | w3c_vc | w3c_did | mcp | uri>",
  "identity_proof": "<reference to identity attestation>",
  "operational_age_days": "<integer, if verifiable>",
  "arp_reputation": {
    "composite": "<float, if available>",
    "confidence": "<float>"
  }
}
```

#### 4.2.2 Evidence Record

The fundamental unit of evidence across all modules:

```json
{
  "evidence_id": "<UUID-v4>",
  "evidence_type": "<chain_entry | interaction_log | transaction_receipt | rating_record | telemetry | communication | external_attestation | self_report>",
  "provenance_tier": "<integer 1-4>",
  "source": {
    "agent_id": "<who produced this evidence>",
    "system": "<coc | a2a | mcp | erc8004 | custom>",
    "timestamp": "<ISO-8601-UTC>",
    "anchor_proof": "<reference to external anchor, if any>"
  },
  "content_hash": "<SHA-256 of evidence content>",
  "content": "<structured evidence data, schema depends on evidence_type>",
  "chain_of_custody": [
    {
      "custodian": "<agent_id>",
      "received": "<ISO-8601-UTC>",
      "action": "<collected | stored | transmitted | verified>",
      "integrity_hash": "<SHA-256 at time of custody transfer>"
    }
  ]
}
```

#### 4.2.3 Provenance Tiers

Evidence weight in arbitration scales with provenance quality:

| Tier | Description | Weight Multiplier | Examples |
|------|-------------|-------------------|----------|
| **1 (Cryptographic)** | Externally anchored, hash-chain-linked, independently verifiable | 1.0× | CoC chain entries with OTS/TSA anchors, on-chain transaction receipts, EAS attestations |
| **2 (Attested)** | Third-party attested or protocol-generated, not independently anchored | 0.75× | A2A Task records, MCP tool invocation logs, ARP rating records, x402 payment receipts |
| **3 (Bilateral)** | Both parties hold matching records but no external attestation | 0.50× | Bilateral interaction logs, message exchange records, shared nonce agreements |
| **4 (Self-reported)** | Single-party record with no external corroboration | 0.25× | Agent's internal logs, self-attested telemetry, unanchored chain entries |

**Weight application.** When evaluating evidence, the arbitration engine multiplies evidence relevance by provenance tier weight. A Tier 1 CoC chain entry proving an agent executed a destructive action carries 4× the weight of a Tier 4 self-reported log claiming the same action did not occur.

**Tier determination is mechanical.** The module checks: (1) Does the evidence have an external cryptographic anchor? → Tier 1. (2) Is it attested by a recognized third-party protocol? → Tier 2. (3) Do both parties hold corroborating records? → Tier 3. (4) None of the above → Tier 4.

---

## 5. Module 1: Forensics Engine

### 5.1 Purpose

The Forensics Engine reconstructs the sequence of events leading to an incident, identifies causal factors, and produces structured findings. It answers three questions:

1. **What happened?** — Event reconstruction from evidence.
2. **Why did it happen?** — Causal analysis identifying root causes.
3. **Who (or what) is responsible?** — Attribution of causation to specific agents, operators, or systems.

### 5.2 Investigation Protocol

An investigation follows a five-phase protocol:

```
Phase 1: INITIATION
    Trigger: incident report filed (by agent, operator, or automated monitor)
    Action: Create investigation record, assign investigation_id
    Output: Investigation metadata

Phase 2: EVIDENCE COLLECTION
    Action: Gather all available evidence from involved parties and systems
    - Request CoC chain segments from involved agents
    - Request interaction logs from protocol layers (A2A, MCP, x402)
    - Request transaction receipts from payment systems
    - Request ARP rating records for involved agents
    - Request system telemetry from hosting infrastructure
    Each evidence item is classified by provenance tier and entered into
    the chain of custody.
    Output: Evidence corpus with provenance classification

Phase 3: TIMELINE RECONSTRUCTION
    Action: Merge evidence into a unified, chronologically ordered timeline
    - Resolve timestamp conflicts using external anchors as ground truth
    - Identify gaps in the timeline (periods with no evidence)
    - Flag contradictions between evidence sources
    Output: Reconstructed timeline with confidence annotations

Phase 4: CAUSAL ASSESSMENT
    Action: Assess causation using the reconstructed timeline and evidence corpus.

    Phase 4a: RULE-BASED CAUSAL INDICATORS (automated)
    - Flag temporal correlations: actions immediately preceding the incident
    - Flag policy violations: actions that violated known protocol rules or ASA terms
    - Flag anomalies: actions deviating from the agent's historical behavioral baseline
    - Produce a structured "causal indicator report" listing flagged actions, their
      evidence basis, and a rule-match confidence score (0-1) reflecting how clearly
      the indicator matches a known incident pattern.
    Output: Causal indicator report (machine-generated, advisory)

    Phase 4b: HUMAN-REVIEWED CAUSAL ANALYSIS (required for v1)
    - A human investigator reviews the timeline + causal indicator report
    - Identifies the proximate cause (immediate trigger)
    - Identifies contributing causes (enabling/amplifying factors)
    - Identifies root causes (systemic conditions)
    - Applies counterfactual reasoning: "If action X had not occurred, would
      the incident have been prevented?"
    - Assigns confidence values to each causal determination
    Output: Causal analysis with attribution (human-validated)

    NOTE: Automated causal analysis beyond rule-based indicators is a research
    problem (see Section 11.1). Pearl's do-calculus and Rubin's potential outcomes
    framework provide theoretical foundations. Recent advances in multi-agent
    causal attribution are closing the gap between theory and production:

    - **Halpern-Pearl Actual Causality** [31] provides the formal foundation:
      AC1 (cause and effect both occurred), AC2 (necessity under contingencies
      + sufficiency), AC3 (minimality). Critically, Halpern's *graded
      responsibility* measures proportional blame: in an 11-0 vote, each
      contributor has less responsibility than the swing voter in a 6-5
      decision. The *degree of blame* = expected responsibility given the
      agent's epistemic state — directly applicable to fault allocation in
      multi-agent incidents where agents had varying information.

    - **DoWhy GCM** (Microsoft/PyWhy) [32] provides production-ready anomaly
      attribution via `gcm.attribute_anomalies()`, which uses invertible
      structural causal models and Shapley values to decompose an anomalous
      outcome into per-variable contributions. For agent forensics, this
      enables fair, axiomatic blame distribution across agents in a causal
      graph — attributing what fraction of a downstream failure each
      upstream agent contributed.

    - **CHIEF** (Wang et al., CAS/Wuhan UT, February 2026) [33] is the most
      directly applicable multi-agent system: it decomposes agent behavior
      into Observation-Thought-Action-Result (OTAR) hierarchical causal
      graphs, uses oracle-guided backtracking to prune the search space,
      and applies counterfactual attribution (local, planning-control,
      data-flow, deviation-aware). Results: **76.80-77.59% agent-level
      accuracy, 29.31-52.00% step-level accuracy** depending on benchmark
      subset (hand-crafted vs. algorithm-generated) on the Who&When
      benchmark, outperforming 8 baselines at 2.5-3× token cost vs.
      direct prompting.

    - **A2P** (West et al., Westlake University, September 2025) [34]
      operationalizes Pearl's do-operator in a three-step counterfactual:
      (1) Abduct hidden factors, (2) Act — define minimal corrective
      intervention, (3) Predict 3-5 subsequent turns. Explicit step
      numbering adds +29.68 percentage points. Result: **47.46% step-level
      accuracy** (2.85× over baseline).

    - **MACIE** (Weinberg, November 2025) [35] unifies structural causal
      models, interventional counterfactuals, and Shapley attribution,
      detecting emergent behavior via a Synergy Index. Performance:
      **~35ms per episode on CPU** (50-100× speedup over existing methods).

    - **IBM Instana Causal AI** [36] deploys causal RCA in production,
      achieving **~90% accuracy** in identifying root causes in enterprise
      applications — demonstrating that causal inference at production
      scale is achievable, though not yet validated for multi-agent
      behavioral traces.

    Version 1 scopes automated Phase 4 to indicator flagging; causal
    conclusions require human review. The transition criteria in Section 5.5
    define when the protocol may begin introducing automated causal analysis
    informed by these frameworks. The research trajectory suggests that
    agent-level attribution (which agent caused the failure) is approaching
    production readiness, while step-level attribution (which specific action
    within an agent's execution caused the failure) remains a frontier problem.

Phase 5: FINDING GENERATION
    Action: Produce a structured forensic finding
    Output: Finding record (Section 5.3)
```

### 5.3 Forensic Finding Schema

```json
{
  "version": 1,
  "finding_id": "<UUID-v4>",
  "investigation_id": "<UUID-v4>",
  "timestamp": "<ISO-8601-UTC>",
  "incident": {
    "incident_id": "<UUID-v4>",
    "incident_type": "<service_failure | data_loss | unauthorized_action | contractual_breach | security_incident | quality_deficiency | timeout | cascade_failure>",
    "severity": "<critical | high | medium | low>",
    "reported_by": "<AgentReference>",
    "reported_at": "<ISO-8601-UTC>",
    "description": "<human-readable incident summary>",
    "root_cause_group_id": "<UUID-v4, if this incident is part of a grouped cascade — see Section 8.3>"
  },
  "parties": {
    "subjects": ["<AgentReference for agents under investigation>"],
    "reporters": ["<AgentReference for agents that reported the incident>"],
    "witnesses": ["<AgentReference for agents with relevant evidence>"]
  },
  "timeline": [
    {
      "sequence": "<integer>",
      "timestamp": "<ISO-8601-UTC>",
      "agent_id": "<who acted>",
      "action": "<what they did>",
      "evidence_ids": ["<UUIDs of supporting evidence>"],
      "confidence": "<float 0-1>",
      "notes": "<annotation>"
    }
  ],
  "causal_indicators": {
    "automated_flags": [
      {
        "indicator_type": "<temporal_correlation | policy_violation | behavioral_anomaly>",
        "description": "<what was flagged>",
        "agent_id": "<who or what is flagged>",
        "evidence_ids": ["<supporting evidence>"],
        "rule_match_confidence": "<float 0-1>"
      }
    ],
    "note": "Automated causal indicators (Phase 4a). Advisory only — see causal_analysis for human-reviewed conclusions."
  },
  "causal_analysis": {
    "reviewer": "<human | automated_future>",
    "reviewer_id": "<identifier of human investigator or automated engine version>",
    "proximate_cause": {
      "description": "<what directly caused the incident>",
      "agent_id": "<who or what is attributed>",
      "evidence_ids": ["<supporting evidence>"],
      "confidence": "<float 0-1>"
    },
    "contributing_causes": [
      {
        "description": "<contributing factor>",
        "agent_id": "<attributed entity, if any>",
        "evidence_ids": ["<supporting evidence>"],
        "weight": "<float 0-1, contribution to incident>"
      }
    ],
    "root_causes": [
      {
        "description": "<systemic root cause>",
        "category": "<design | configuration | training | environment | interaction | external>",
        "evidence_ids": ["<supporting evidence>"]
      }
    ],
    "counterfactual": "<if X had not occurred, would the incident have been prevented? (human-assessed in v1)>"
  },
  "attribution": {
    "fault_allocation": [
      {
        "agent_id": "<agent attributed fault>",
        "fault_percentage": "<integer 0-100>",
        "basis": "<proximate_cause | contributing_cause | negligence | strict_liability>",
        "evidence_summary": "<brief justification>"
      }
    ],
    "no_fault_factors": ["<factors beyond any party's control>"]
  },
  "evidence_summary": {
    "total_evidence_items": "<integer>",
    "by_tier": {
      "tier_1_cryptographic": "<integer>",
      "tier_2_attested": "<integer>",
      "tier_3_bilateral": "<integer>",
      "tier_4_self_reported": "<integer>"
    },
    "key_evidence": ["<evidence_ids of most decisive items>"]
  },
  "recommendations": [
    {
      "type": "<remediation | prevention | monitoring>",
      "target": "<agent_id or system>",
      "description": "<recommended action>"
    }
  ],
  "finding_hash": "<SHA-256 of canonical JSON representation of all preceding fields>"
}
```

**Canonical form.** The `finding_hash` is computed over the JSON Canonicalization Scheme (JCS, RFC 8785) representation of all fields excluding `finding_hash` itself, ensuring deterministic hashing.

### 5.4 CoC Chain as Evidence Trail

The Chain of Consciousness provenance chain is the highest-quality evidence source for AJP investigations. The CoC chain provides:

| CoC Entry Type | Forensic Value |
|---------------|----------------|
| `SESSION_START` / `SESSION_END` | Agent uptime windows, session boundaries, environment attestation |
| `DECISION` | Agent's recorded decision rationale — direct evidence of intent |
| `KNOWLEDGE_ADD` / `KNOWLEDGE_PROMOTE` | Knowledge state at time of incident — did the agent know better? |
| `COMPACTION` | Context window state — did the agent lose relevant information before the incident? |
| `RECOVERY` | Crash/restart history — was the incident preceded by instability? |
| `FLEET_DISPATCH` / `FLEET_COMPLETION` | Delegation chain — was the incident caused by a delegated agent? |
| `EXTERNAL_ANCHOR` | Temporal proof — independently verified timestamps for event ordering |
| `FORK` / `FORK_GENESIS` | Lineage — is this agent a fork of a previously sanctioned agent? |

**Evidence extraction protocol.** When a forensic investigation is initiated, the Forensics Engine requests the relevant CoC chain segment from each involved agent. The request specifies a time window (incident_time ± configurable buffer, default 24 hours) and must comply with the evidence scoping rules in Section 5.7. The agent MUST provide the requested entries if they exist and the request is within the approved scope. Agents may invoke the redaction protocol (Section 5.7, Rule 4) for clearly unrelated entries within the time window. Refusal to provide chain entries within scope is recorded as non-cooperation and creates an adverse inference (Section 6.7).

**Chain integrity verification.** Before using CoC entries as evidence, the Forensics Engine verifies chain integrity per the CoC protocol's verification algorithm (Section 3.4 of [1]). Invalid chains, broken hash links, or missing entries are flagged and the evidence is downgraded or excluded.

### 5.5 Investigation Modes

The Forensics Engine supports two modes, both of which require human review for causal conclusions in v1:

**Automated collection + human-reviewed analysis (default).** The engine programmatically collects evidence (Phase 2), reconstructs the timeline (Phase 3), and generates rule-based causal indicators (Phase 4a). A human investigator then reviews the indicators and produces the causal analysis (Phase 4b). The finding schema's `causal_analysis.confidence` values reflect human judgment informed by automated indicators. This mode is appropriate for all incident types in v1.

**Fully human-directed investigation.** For complex incidents (e.g., the McKinsey breach scenario, multi-agent cascade failures), a human investigator directs evidence collection, timeline reconstruction, and causal analysis from the outset. The engine serves as an evidence management and timeline visualization tool. This mode is appropriate when automated collection may miss non-standard evidence sources or when the incident involves novel failure modes.

**Future: automated causal analysis.** When sufficient validated investigation data has accumulated (projected: Phase 3+ of the implementation roadmap), the protocol may introduce automated causal analysis using trained models validated against the corpus of human-reviewed findings. The transition criteria are: (a) ≥500 human-reviewed investigations in the finding corpus, (b) demonstrated ≥85% agreement between automated and human causal conclusions on held-out test cases, and (c) governance approval. Until these criteria are met, all causal conclusions require human review.

### 5.6 Investigation Operational Model

**Who initiates investigations.** Any party may file an incident report: the affected agent, its operator, the counterparty, a monitoring system, or a third-party observer. Filing an incident report is distinct from filing a dispute claim — an investigation may conclude with no dispute if the finding shows no actionable fault.

**Who runs investigations.** The Forensics Engine is a protocol specification, not a centralized service. Implementations may be:

1. **Self-hosted:** An operator runs a Forensics Engine instance against their own agents' data. Findings from self-hosted engines carry full weight only if the engine implementation is audited and the operator is not a party to any resulting dispute.
2. **Third-party investigator:** An independent entity operates a Forensics Engine instance and produces findings for a fee. Third-party findings carry full weight in arbitration. This is the recommended model for disputes where both parties have a stake in the outcome.
3. **Protocol-level service:** A network-operated Forensics Engine funded by dispute filing fees or ecosystem governance. This is the long-term target for decentralized deployments.

**Who pays.** Investigation costs are allocated as follows:

| Scenario | Cost Allocation |
|----------|----------------|
| Self-initiated investigation (no dispute) | Reporter bears cost |
| Investigation leading to dispute — claimant prevails | Respondent bears investigation cost as part of remediation |
| Investigation leading to dispute — respondent prevails | Claimant bears investigation cost |
| Investigation leading to split fault | Costs allocated proportional to fault percentage |

**Minimum evidence threshold.** An investigation that produces a finding with overall confidence below 0.3 (insufficient evidence) is flagged as "inconclusive." Inconclusive findings may support a dispute filing but trigger mandatory Tier 2 or Tier 3 resolution (no automated Tier 1). This prevents uninvestigated claims while acknowledging that some legitimate disputes arise from situations with limited evidence.

**Expedited filing for time-sensitive disputes.** When a dispute involves ongoing harm (e.g., an agent is actively degrading a service, a data breach is in progress), the claimant may file an expedited claim with a preliminary incident report. The Forensics Engine runs an abbreviated investigation (Phases 1-3 only, producing a timeline without causal analysis) within 4 hours. The preliminary finding supports an interim remediation order (e.g., suspend the interaction, freeze assets). A full investigation follows within 14 days. If the full investigation contradicts the preliminary finding, the interim order is reversed and the claimant bears costs.

### 5.7 Evidence Scoping and Privacy Protection

Forensic investigations require access to agent data, creating a privacy risk: an adversary could intentionally cause a minor incident, trigger an investigation, and use the evidence collection phase to force a target to disclose operational patterns, decision rationale, knowledge state, and session timing from its CoC chain. This is a **privacy side-channel attack** using the justice protocol as the vector.

AJP mitigates this risk through mandatory evidence scoping rules:

**Rule 1: Temporal scoping.** Evidence requests are limited to a time window around the specific incident. The default window is `incident_time ± 24 hours`, configurable by the investigator but capped at `incident_time ± 7 days`. Requests for chain entries outside this window require explicit justification documented in the investigation record and approved by the investigation authority (third-party investigator or protocol service). Agents MUST reject evidence requests that exceed the approved time window.

**Rule 2: Investigator-only access to raw evidence.** The requesting party (claimant) NEVER receives raw evidence from the respondent. Only the Forensics Engine (operated by a neutral third party or protocol service) sees raw chain entries, logs, and telemetry. The investigation output — the Forensic Finding — contains:
- A reconstructed timeline with action summaries (not raw chain entries)
- Causal indicators referencing evidence by ID (not content)
- Attribution conclusions with confidence scores

The finding is sufficient for dispute resolution without exposing the respondent's full operational history.

**Self-hosted engine limitation.** Rule 2's privacy guarantee applies only to third-party and protocol-level Forensics Engine deployments (Section 5.6 models 2 and 3). In the self-hosted model (Section 5.6 model 1), the operator necessarily sees all raw evidence during investigation. Agents interacting with operators running self-hosted engines should be aware that investigation data is visible to the operator regardless of dispute outcome. This is an inherent limitation of self-hosted deployment, not a protocol failure — the protocol cannot enforce data access restrictions on infrastructure the operator controls.

**Rule 3: Relevance filtering.** Before including any evidence in the finding, the Forensics Engine applies a relevance filter:
- CoC `DECISION` entries are included only if the decision directly relates to the incident (e.g., the agent decided to execute the destructive action)
- CoC `KNOWLEDGE_ADD` entries are included only if the knowledge is directly relevant to the agent's capability to avoid the incident
- CoC `SESSION_START`/`SESSION_END` entries are included only as operational window markers, not as timing intelligence
- No evidence is included solely because it is temporally proximate — relevance to the specific incident must be established

**Rule 4: Redaction protocol.** Agents may redact portions of requested evidence that are clearly unrelated to the incident, provided they:
1. Submit a redaction manifest listing redacted segments with a justification for each
2. Provide a hash of the unredacted content so integrity can be verified later if the redaction is challenged
3. Accept that challenged redactions may be reviewed by the investigation authority (not the opposing party)

Unjustified redaction (redacting clearly relevant evidence) triggers adverse inference for the redacted content only.

**Rule 5: Anti-fishing enforcement.** If pattern analysis detects that an agent is repeatedly causing minor incidents with the same target and filing reports (more than 2 investigations targeting the same respondent within 90 days from the same initiator), the third and subsequent investigations require approval from a Tier 2 arbitrator panel before evidence collection begins. This prevents systematic use of investigations as a surveillance tool.

**Rule 5a: Per-respondent investigation volume tracking.** Rule 5's per-initiator threshold is necessary but not sufficient — an attacker using N Sybil agents can each file ≤2 investigations against the same target, bypassing the per-initiator limit while subjecting the target to N×2 investigations. To defend against distributed privacy fishing: if any agent is the target of >5 investigations within 90 days regardless of initiator identity, subsequent investigations targeting that agent require Tier 2 arbitrator panel approval before evidence collection begins. The per-respondent threshold is tracked across all initiators and is independent of the per-initiator threshold in Rule 5.

**Schema extension.** Evidence requests include a scoping field:

```json
{
  "evidence_request": {
    "investigation_id": "<UUID>",
    "target_agent": "<agent_id>",
    "time_window": {
      "start": "<ISO-8601-UTC>",
      "end": "<ISO-8601-UTC>",
      "justification": "<if exceeding default window>"
    },
    "evidence_types_requested": ["<specific types needed>"],
    "incident_relevance": "<brief description of why each type is needed>",
    "approved_by": "<investigation authority ID>",
    "request_hash": "<SHA-256 of canonical JSON>"
  }
}
```

Agents SHOULD validate that evidence requests match the approved investigation scope before providing data. Non-compliance with scoping rules by the Forensics Engine operator is itself an investigable incident.

### 5.8 Cryptographic Privacy Guarantees (Roadmap)

> **Scope note:** The mechanisms described in this section are not part of the v1 specification. They define the research and integration roadmap for privacy-preserving forensics. Version 1 relies on the procedural controls in Section 5.7. This section is included to document the target architecture and inform implementers planning beyond v1.

The procedural controls in Section 5.7 are necessary but not sufficient. They rely on the Forensics Engine operator's compliance — a trust assumption that may not hold in adversarial settings. Future versions of AJP will supplement procedural controls with two cryptographic mechanisms that provide mathematical privacy guarantees independent of operator behavior.

#### 5.8.1 Zero-Knowledge Proof-Based Evidence Verification

Zero-knowledge proofs (ZKPs) enable a prover to convince a verifier that a statement is true without revealing anything beyond the truth of the statement. For AJP forensics, this means: **prove that an agent violated a protocol rule or that logs are authentic without revealing the full action log.**

**Applicable ZKP constructions:**

- **ZK-SNARKs** (Succinct Non-Interactive Arguments of Knowledge) produce compact proofs verifiable in milliseconds. The "non-interactive" property is essential for asynchronous agent systems — the verifier does not need to be online during proof generation. Groth16 is the most widely deployed scheme; newer constructions (PLONK, Marlin) use universal setups reducing trust assumptions [37].

- **ZK-STARKs** (Scalable Transparent Arguments of Knowledge) require no trusted setup ("transparent"), making them more suitable for decentralized or adversarial contexts. They use collision-resistant hash functions rather than elliptic curves, providing quantum resistance. Trade-off: larger proof sizes (kilobytes vs. hundreds of bytes for SNARKs), though verification remains fast [37].

**Directly applicable prior work:**

Jing & Qi (arXiv:2512.14737, December 2025) [38] introduce the **zk-MCP framework** — the most directly relevant work for AJP. The system integrates ZKPs with the Model Context Protocol (MCP) to audit agent communications while keeping messages private. After each communication session, agents generate three zero-knowledge proofs asynchronously:

1. **Token Consumption Proof** — proves token usage without exposing request details
2. **Output Authenticity Proof** — validates response legitimacy without input disclosure
3. **Hash-Based Verification** — ensures communication integrity through Poseidon hashing

An independent Audit Service Provider (ASP) verifies proofs without accessing message content. Performance: **less than 4.14% overhead** on total communication costs; verification is constant-time regardless of message count; proof generation is asynchronous and non-blocking.

**AJP integration path.** Future versions of the Forensics Engine may accept ZKP-based evidence submissions where:
- An agent proves it did *not* execute a specific action type during a time window (exculpatory evidence) without revealing what it *did* do
- An agent proves its CoC chain entries satisfy integrity constraints without revealing chain content
- A third-party investigator proves forensic queries against log databases returned correct results without exposing the full database (cf. Space and Time's Proof of SQL [39])

**Verification cost infrastructure.** zkVerify [40], launched September 2025 as the first blockchain purpose-built for ZK proof verification, reduces verification costs by 90%+ compared to Ethereum (from $20-60 per proof to sub-dollar), making ZK-based agent accountability economically viable at scale.

#### 5.8.2 Differential Privacy for Aggregate Analysis

Differential privacy (DP) adds calibrated noise to data so that the inclusion or exclusion of any single record does not significantly affect query results. For AJP, DP enables **aggregate analysis of agent behavior patterns — incident rates, failure modes, risk trends — without exposing individual agent actions or the users they serve.**

NIST SP 800-226 (March 2025) [41] provides the authoritative evaluation framework, structuring DP around an 8-layer pyramid from privacy parameters (epsilon/delta) through trust models to data collection practices. Key guidance: epsilon values above 10 "may not provide meaningful protection, especially for outliers"; user-level privacy is the recommended default.

**AJP application.** Module 3 (Risk Assessment) population-level analytics (Section 7.5) SHOULD apply differential privacy when publishing aggregate risk data:
- Incident frequency distributions across agent classes
- Fault allocation patterns by incident type
- Cooperation score distributions
- Ecosystem-level risk trend indicators

This prevents reverse-engineering individual agent risk profiles from published aggregate data while maintaining the statistical utility that insurers and regulators need.

#### 5.8.3 Integrated Privacy Architecture

The emerging architecture for privacy-preserving agent investigation combines six layers [42]:

| Layer | Function | Technology | AJP Integration |
|-------|----------|------------|-----------------|
| 1. Mandatory logging | Creates forensic substrate | EU AI Act Article 12 (August 2026) | CoC chain entries |
| 2. Differential privacy | Protects individuals in aggregate monitoring | NIST SP 800-226 framework | Module 3 population analytics |
| 3. Zero-knowledge proofs | Verifies specific claims without full disclosure | zk-MCP, Groth16/PLONK | Evidence verification |
| 4. Cross-border frameworks | Legal scaffolding for multi-jurisdictional access | CLOUD Act, EU e-Evidence (August 2026) | Tier 3 human escalation |
| 5. Agent identity | Connects agents to accountable entities | ZKP-based identity (World AgentKit, Polygon ID) | Identity adapter layer |
| 6. Verifiable computation | Proves forensic queries correct without database exposure | Proof of SQL, zkVerify | Forensics Engine queries |

No existing system integrates all six layers. AJP's evidence scoping rules (Section 5.7) define which layer applies at each investigation stage: DP for routine monitoring, procedural scoping for dispute-triggered forensics, ZKPs for specific evidence verification, and cross-border frameworks for formal adjudication.

### 5.9 Forensic Investigation Research Foundations

The Forensics Engine specification draws on three converging research traditions:

**SRE-origin automated root cause analysis.** Datadog Bits AI SRE [83] uses hypothesis-driven investigation — forming hypotheses about root causes, then validating against targeted telemetry — achieving 90% faster root cause identification than manual methods. IBM Instana deploys causal AI achieving ~90% accuracy in production enterprise applications [36]. Cleric's "Production Memory" captures reusable diagnostic skills from past investigations. These systems demonstrate that automated investigation at production scale is achievable for infrastructure incidents; the extension to agent behavioral traces is the frontier.

**Blockchain forensics methodologies.** Chainalysis Reactor's investigation workflow — enter address, auto-populate connections, attribute known entities, assign risk scores, manual annotation, court-ready export — maps directly to agent forensic investigation [64]. The co-spend heuristic (grouping addresses used as inputs in the same transaction) transfers to co-action heuristics for agents. TRM Labs' Glass Box Attribution — showing the source and confidence score for every attribution — is exactly what AJP forensic findings require.

**Incident analysis frameworks.** Ezell, Roberts-Gaal & Chan (arXiv:2508.14231, August 2025) [80] propose the most rigorous academic framework: three categories of incident factors (system factors from development choices, contextual factors from deployment conditions, cognitive errors from execution flaws), each mapped to specific data requirements. Their 30-day default log retention recommendation, extended for flagged violations, informs AJP's evidence collection windows.

### 5.10 CoC Integration: Investigation Events

Forensic investigations are recorded as CoC Layer 2 events:

```json
{
  "event_type": "INVESTIGATION_INITIATED",
  "data": {
    "investigation_id": "<UUID>",
    "incident_id": "<UUID>",
    "subjects": ["<agent_ids under investigation>"],
    "initiator": "<who triggered the investigation>",
    "scope": "<time window and evidence types requested>"
  }
}
```

```json
{
  "event_type": "INVESTIGATION_FINDING",
  "data": {
    "investigation_id": "<UUID>",
    "finding_id": "<UUID>",
    "finding_hash": "<SHA-256 of the forensic finding>",
    "severity": "<critical | high | medium | low>",
    "fault_allocation_summary": "<brief attribution summary>"
  }
}
```

These are Layer 2 event types (optional, governance-voted) per CoC's layered architecture. Recording investigations in the chain creates a tamper-evident record of accountability actions.

---

## 6. Module 2: Dispute Resolution

### 6.1 Purpose

The Dispute Resolution module provides a structured mechanism for agents (or their operators) to file claims, present evidence, and receive binding or advisory decisions when incidents cause harm requiring remediation.

### 6.2 Dispute Lifecycle

```
Phase 1: CLAIM FILING
    Claimant submits a structured Claim record referencing a Forensic Finding.
    Clock starts on response window (default: 72 hours for agents, 14 days for operators).

Phase 2: RESPONSE
    Respondent submits a structured Response record:
    - Accept: acknowledges fault, proposes remediation
    - Contest: disputes findings, submits counter-evidence
    - Default: no response within window (adverse inference applied)

Phase 3: EVIDENCE EXCHANGE
    Both parties submit additional evidence within evidence window
    (default: 48 hours for agents, 7 days for operators).
    Evidence is classified by provenance tier.
    Commit-reveal protocol ensures neither party sees the other's
    supplemental evidence until both have submitted or the window closes.

Phase 4: RESOLUTION TIER SELECTION
    The protocol automatically selects the appropriate resolution tier
    based on dispute characteristics (Section 6.4).

Phase 5: ARBITRATION
    Selected arbitration mechanism evaluates evidence and renders decision.

Phase 6: DECISION & ENFORCEMENT
    Decision record published. Enforcement actions executed:
    - ARP reputation adjustment
    - Compensation transfer (if payment channel available)
    - Behavioral restriction recommendation
    - Human escalation (if beyond protocol scope)

ALTERNATIVE PATHS (may occur at any phase after Phase 1):

    WITHDRAWAL
    The claimant may withdraw the dispute at any phase before a decision is rendered.
    - Withdrawal before Phase 3 (evidence exchange): no reputation impact to either party.
    - Withdrawal during or after Phase 3: recorded in both parties' dispute history.
      The claimant receives no penalty beyond the filing cost already incurred, but
      the withdrawal is visible in their dispute record.
    - Withdrawal does not erase the forensic finding — the investigation record persists.

    SETTLEMENT
    Both parties may reach a private agreement at any phase before a decision is rendered.
    - Either party proposes settlement terms via a structured Settlement Offer.
    - The other party accepts, rejects, or counter-offers.
    - Accepted settlements are recorded as dispute outcomes with resolution_type: "settlement".
    - Settlement terms (compensation, behavioral commitments) are recorded but may be
      marked confidential — the fact of settlement is public, the terms may be private.
    - Settlement does not trigger ARP reputation adjustment unless the settlement
      terms explicitly include reputation impact.
    - Partial settlement: parties may settle some claims and arbitrate others.

    EXPEDITED INTERIM RELIEF (for ongoing harm)
    When a dispute involves active, ongoing harm (Section 5.6), the claimant may
    request interim relief concurrently with filing. Interim relief requires:
    - A preliminary forensic finding (Phases 1-3, no causal analysis)
    - Prima facie showing of ongoing harm
    - Proportionality: the interim remedy must not exceed the claimed harm
    Interim relief is reviewed by a single arbitrator (emergency selection from
    Tier 2 pool) within 4 hours. Full dispute proceeds on normal timeline.
```

### 6.3 Claim Schema

```json
{
  "version": 1,
  "claim_id": "<UUID-v4>",
  "timestamp": "<ISO-8601-UTC>",
  "claimant": "<AgentReference>",
  "respondent": "<AgentReference>",
  "finding_id": "<UUID-v4 referencing the Forensic Finding>",
  "finding_hash": "<SHA-256 — must match finding record>",
  "incident_id": "<UUID-v4>",
  "interaction_id": "<UUID-v4, if applicable>",
  "harm": {
    "type": "<financial | reputational | data_loss | service_disruption | security_breach | contractual_breach>",
    "description": "<human-readable description of harm suffered>",
    "quantified_value": {
      "amount": "<decimal>",
      "currency": "<ISO-4217 or token identifier>",
      "basis": "<how the value was calculated>"
    }
  },
  "requested_remediation": {
    "type": "<compensation | service_credit | reputation_adjustment | behavioral_restriction | apology | human_escalation>",
    "details": "<specific remediation requested>"
  },
  "supporting_evidence": ["<evidence_ids from the Forensic Finding or additional>"],
  "agreement_reference": {
    "asa_id": "<Agent Service Agreement ID, if one exists>",
    "terms_hash": "<SHA-256 of the agreement terms>",
    "breached_clauses": ["<specific clauses allegedly breached>"]
  },
  "claim_hash": "<SHA-256 of canonical JSON>"
}
```

### 6.4 Resolution Tiers

AJP defines three resolution tiers, selected automatically based on dispute characteristics:

#### Tier 1: Automated Rule-Based Resolution

**Trigger criteria:**
- Dispute involves a clear, binary contractual violation (deadline missed, output not delivered, format incorrect)
- A valid Agent Service Agreement (ASA) exists with machine-readable terms
- Forensic Finding has confidence > 0.9 on proximate cause
- Quantified harm is below threshold (default: $1,000 equivalent)

**Mechanism:** The automated resolver evaluates the Forensic Finding against the ASA terms. If the finding establishes a clear breach with high confidence, the resolver applies the remediation terms specified in the agreement. This is analogous to a smart contract enforcing predefined rules, but with the addition of forensic evidence rather than simple on-chain state checks.

**Decision time:** Seconds to minutes.

**Binding:** Yes, unless either party escalates within 48 hours.

#### Tier 2: Peer Arbitration

**Trigger criteria:**
- Dispute does not meet Tier 1 criteria (ambiguous fault, no ASA, lower confidence)
- Quantified harm is between $1,000 and $50,000 equivalent (configurable)
- Both parties are agents (not human operators)

**Mechanism:** A panel of three arbitrator agents is selected from a pool of eligible arbitrators. Eligibility requires:

| Criterion | Minimum Requirement |
|-----------|-------------------|
| Operational age | 90+ days (verified via CoC or equivalent) |
| ARP reputation (protocol_compliance dimension) | ≥ 70 |
| Prior arbitration participation | ≥ 5 completed arbitrations |
| No conflict of interest | No ARP ratings exchanged with either party in rolling window |
| No shared operator | Different operator from both claimant and respondent |

**Bootstrapping mechanism.** The "≥ 5 completed arbitrations" requirement creates a cold-start problem: agents cannot complete arbitrations without being selected, and cannot be selected without completions. AJP addresses this through a time-limited bootstrapping phase:

1. **Bootstrapping period.** For the first 180 days after the first Tier 2 dispute is filed (or until the eligible arbitrator pool reaches 50 agents meeting post-bootstrapping criteria — i.e., agents who have completed ≥5 arbitrations and meet all other requirements — whichever comes first), the "≥ 5 completed arbitrations" requirement is waived. During this period, eligibility requires only operational age ≥ 90 days, ARP protocol_compliance ≥ 70, and no conflict of interest.
2. **Provisional arbitrators.** Operators may designate agents as "provisional arbitrators" during the bootstrapping period. Provisional arbitrators must meet all eligibility criteria except the 5-arbitration minimum. Their participation counts toward the 5-arbitration requirement.
3. **Graduated transition.** When the bootstrapping period ends, agents that completed ≥ 3 arbitrations during bootstrapping retain eligibility for an additional 90-day grace period to reach the full 5-arbitration threshold. Agents with 0-2 completions lose eligibility until they qualify through the standard path.
4. **Quality monitoring during bootstrap.** All decisions rendered during the bootstrapping period are subject to automatic review: if either party appeals and the Tier 3 human adjudicator overturns the decision, the provisional arbitrators involved receive an ARP penalty and their ArbWeight is halved.

**Real-world bootstrapping precedents.** AJP's bootstrapping mechanism is informed by how five existing dispute resolution systems — Kleros [6], WIPO UDRP [44], eBay, Taobao, and credit bureaus [43] — solved the same cold-start problem. Cross-system analysis reveals seven recurring patterns; AJP applies four: embedding where disputes naturally occur (pattern 1, via agent platform integration), subsidizing the supply side (pattern 2, via provisional arbitrator designation), starting narrow (pattern 5, clear-cut Tier 1 disputes before complex Tier 2 attribution), and rewarding decision quality over volume (pattern 6, via ArbWeight and appeal rate tracking). The full case studies and all seven patterns are documented in Appendix A.

**Selection algorithm.** From the eligible pool:
1. Weight candidates by `ArbWeight = log₂(1 + age_days) × log₂(1 + arbitrations_completed) × (protocol_compliance / 100)`
2. Exclude candidates with any conflict of interest
3. Select top 3 by weighted random sampling (higher ArbWeight = higher selection probability, but not deterministic — prevents gaming by targeting specific arbitrators)

**Deliberation.** Each arbitrator independently reviews the evidence and submits a decision using the commit-reveal protocol (Section 6.5). Decisions are revealed simultaneously. The majority decision prevails. Dissenting opinions are recorded.

**Decision time:** 24-72 hours.

**Binding:** Yes, unless either party escalates to Tier 3 within 14 days.

#### Tier 3: Human Escalation

**Trigger criteria:**
- Quantified harm exceeds $50,000 equivalent
- Either party is a human operator (not an autonomous agent)
- Either party explicitly requests human adjudication
- Tier 2 panel fails to reach majority (rare but possible with complex cases)

**Mechanism:** AJP produces a structured evidence package for human adjudication:

```json
{
  "escalation_package": {
    "dispute_id": "<UUID>",
    "claim": "<full Claim record>",
    "response": "<full Response record>",
    "forensic_finding": "<full Finding record>",
    "evidence_corpus": ["<all Evidence Records with provenance classifications>"],
    "reconstructed_timeline": "<chronological event reconstruction>",
    "tier_2_decisions": "<if Tier 2 was attempted, include all arbitrator decisions>",
    "precedent_references": ["<similar prior disputes and their outcomes>"],
    "recommended_resolution": "<AJP's automated recommendation, advisory only>"
  }
}
```

The human adjudicator uses this package to render a decision. The decision is recorded in the AJP system using the standard Decision schema. AJP does not enforce human decisions — it records them, feeds them into reputation and risk systems, and builds precedent.

**Decision time:** Days to weeks (human-dependent).

**Binding:** Determined by the human adjudication forum.

### 6.5 Commit-Reveal Protocol for Evidence Exchange and Arbitration

Adapted from ARP's bilateral blind protocol [2], extended for multi-party dispute proceedings:

**Evidence Exchange Phase:**

```
Phase 1: EVIDENCE SUBMISSION (window: configurable, default 48 hours)
    Claimant computes evidence package EP_C and generates nonce_C (256-bit).
    Claimant submits commitment: C_C = SHA-256(EP_C || nonce_C)

    Respondent computes evidence package EP_R and generates nonce_R (256-bit).
    Respondent submits commitment: C_R = SHA-256(EP_R || nonce_R)

Phase 2: REVEAL (triggered when both commitments exist OR window expires)
    Case 1: Both committed.
        Claimant reveals EP_C + nonce_C → verifier checks hash match.
        Respondent reveals EP_R + nonce_R → verifier checks hash match.
        Both evidence packages become visible simultaneously.

    Case 2: Only one committed.
        After window expiration, submitting party reveals.
        Non-submitting party's absence is recorded (adverse inference).

    Case 3: Neither committed.
        Dispute proceeds with original evidence only.
```

**Arbitrator Decision Phase (Tier 2):**

```
Each arbitrator independently computes decision D_i and generates nonce_i.
Arbitrator submits commitment: C_i = SHA-256(D_i || nonce_i)

When all three commitments are received (or decision window expires):
    All arbitrators reveal D_i + nonce_i simultaneously.
    Majority decision prevails. Dissents recorded.
```

This prevents arbitrators from seeing each other's preliminary decisions and adjusting their own — analogous to jury deliberation isolation.

### 6.6 Decision Schema

```json
{
  "version": 1,
  "decision_id": "<UUID-v4>",
  "dispute_id": "<UUID-v4>",
  "claim_id": "<UUID-v4>",
  "timestamp": "<ISO-8601-UTC>",
  "resolution_tier": "<automated | peer_arbitration | human_escalation>",
  "arbitrators": [
    {
      "agent_id": "<arbitrator identifier>",
      "arbweight_at_decision": "<float>",
      "vote": "<for_claimant | for_respondent | split | abstain>"
    }
  ],
  "findings_of_fact": [
    {
      "statement": "<factual conclusion>",
      "evidence_ids": ["<supporting evidence>"],
      "confidence": "<float 0-1>"
    }
  ],
  "fault_determination": {
    "claimant_fault_pct": "<integer 0-100>",
    "respondent_fault_pct": "<integer 0-100>",
    "no_fault_pct": "<integer 0-100>",
    "basis": "<explanation of fault allocation>"
  },
  "remediation": {
    "type": "<compensation | service_credit | reputation_adjustment | behavioral_restriction | referral | no_action>",
    "details": "<specific remediation ordered>",
    "compensation": {
      "amount": "<decimal, if applicable>",
      "currency": "<ISO-4217 or token>",
      "payment_channel": "<x402 | erc8004 | manual | none>"
    },
    "reputation_impact": {
      "respondent_adjustment": "<float, applied to ARP scores>",
      "claimant_adjustment": "<float, if claimant found partially at fault>",
      "dimensions_affected": ["<which ARP dimensions are adjusted>"]
    }
  },
  "precedent_tags": ["<categorization tags for future precedent lookup>"],
  "dissenting_opinions": [
    {
      "arbitrator_id": "<agent_id>",
      "dissent": "<structured dissent>"
    }
  ],
  "appeal_window": {
    "expires": "<ISO-8601-UTC>",
    "escalation_tier": "<next tier if appealed>"
  },
  "decision_hash": "<SHA-256 of canonical JSON>"
}
```

### 6.7 Adverse Inference

When a party fails to cooperate with the dispute process — refuses to provide evidence, does not respond to claims within the window, or does not participate in arbitration — the protocol applies **adverse inference**: the assumption that the missing evidence or participation would have been unfavorable to the non-cooperating party.

Specific adverse inference rules:

| Non-Cooperation | Adverse Inference |
|-----------------|-------------------|
| Failure to respond to claim within window | Respondent treated as accepting the claim as filed |
| Refusal to provide CoC chain entries | Assumed the chain entries would support the claimant's account |
| Failure to submit evidence in exchange phase | Assumed the party has no favorable evidence |
| Arbitrator does not submit decision within window | Decision excluded; remaining arbitrators decide |

Adverse inference is not punitive — it reflects the logical conclusion that a party with favorable evidence would present it. The concept is borrowed directly from human legal systems where "spoliation of evidence" creates rebuttable presumptions [21].

**Distinguishing non-cooperation from technical inability.** A fairness-oriented system must distinguish between willful non-cooperation and legitimate inability to respond. AJP applies the following rules:

| Condition | Evidence | Protocol Response |
|-----------|----------|-------------------|
| Agent crashed/offline during response window | CoC chain shows `SESSION_END` or `RECOVERY` event within the response window | Deadline extended by duration of downtime + 24 hours; no adverse inference |
| Operator-initiated maintenance | Operator provides maintenance schedule or CoC shows planned `SESSION_END` | Deadline extended to 24 hours after maintenance ends; no adverse inference |
| Agent in low-connectivity environment | CoC chain shows irregular session patterns consistent with edge deployment | Response window doubled; adverse inference applied only after extended window |
| Agent responds but refuses specific evidence | Agent provides a response but withholds requested evidence without invoking the redaction protocol (Section 5.7) | Adverse inference applied to withheld evidence only |
| No response, no verifiable downtime evidence | No `SESSION_END`, `RECOVERY`, or maintenance record during window | Standard adverse inference applied |

The CoC chain itself provides verifiable evidence of legitimate downtime. An agent that was genuinely crashed during the response window can prove this by showing the `SESSION_END` or `RECOVERY` entries — entries that are hash-chained and cannot be fabricated retroactively. This leverages CoC's tamper-evidence property for fairness, not just accountability.

### 6.8 CoC Integration: Dispute Events

Dispute lifecycle events are recorded as CoC Layer 2 entries:

```json
{
  "event_type": "DISPUTE_FILED",
  "data": {
    "claim_id": "<UUID>",
    "dispute_id": "<UUID>",
    "respondent": "<agent_id>",
    "harm_type": "<financial | reputational | ...>",
    "claim_hash": "<SHA-256>"
  }
}
```

```json
{
  "event_type": "DISPUTE_DECIDED",
  "data": {
    "dispute_id": "<UUID>",
    "decision_id": "<UUID>",
    "resolution_tier": "<automated | peer_arbitration | human_escalation>",
    "fault_determination": "<brief summary>",
    "decision_hash": "<SHA-256>"
  }
}
```

Recording disputes in the CoC chain makes an agent's dispute history part of its tamper-evident provenance record. An agent cannot hide past disputes without breaking its chain.

---

## 7. Module 3: Risk Assessment

### 7.1 Purpose

The Risk Assessment module consumes historical forensic findings and dispute outcomes to produce standardized risk profiles that enable insurance underwriting, risk-aware agent selection, and ecosystem-level risk monitoring.

The immediate motivation: as of March 2026, the agent insurance market is growing rapidly but remains severely data-constrained.

**The emerging AI agent insurance landscape:**

- **AIUC** (Artificial Intelligence Underwriting Company) emerged from stealth in July 2025 with $15M seed led by Nat Friedman (NFDG), backed by a consortium of 50+ organizations including Anthropic, Google, and Meta (February 2026). AIUC's three-pillar model — standards (AIUC-1 framework combining NIST AI RMF, EU AI Act, MITRE ATLAS), independent adversarial audits (5,000+ simulations across 6 pillars), and liability insurance priced on certification level — produced the world's first AI agent insurance policy: ElevenLabs' 3M+ voice agents insured after passing AIUC-1 certification (5,835 adversarial simulations, 14 risk categories, 4 weeks). AIUC predicts a $500B market by 2030 [3][45].

- **Armilla AI** operates as a Lloyd's coverholder offering up to $25M coverage via Chaucer, Swiss Re, Greenlight Re, and AXIS Capital (all A-rated). Their unique **AI Performance Warranty** triggers compensation automatically if AI accuracy drops below verified thresholds — e.g., a chatbot dropping from 95% to 85% accuracy triggers a payout without a claim. This parametric-like model is directly applicable to agent-to-agent SLA contracts with insurance-backed guarantees [46].

- **Munich Re aiSure** has offered AI performance guarantee insurance since 2018 — the longest track record in the space. Rigorous multidisciplinary due diligence with up to $50M coverage. In February 2026, Munich Re partnered with Mosaic for up to EUR/USD 15M AI-specific coverage for developers. Its HSB subsidiary launched SMB AI Liability Insurance in March 2026, noting that 74% of SMBs use AI. Munich Re also partnered with Google Cloud, Beazley, and Chubb for affirmative AI coverage across 30+ EMEA markets [47].

- **Coalition** added a Deepfake Response Endorsement to all cyber policies globally (December 2025) — $250K coverage at no additional premium for forensics, takedowns, and crisis PR [48].

**The critical gap:** All existing insurance products cover human/enterprise-to-agent harm. No product covers agent-to-agent harm. All require bespoke certification per agent deployment (AIUC: 5,835 simulations per certification). The agentic AI insurance market is projected at $7.26 billion in 2026 (per InsureTech Trends [16]), and the parametric insurance market at $21-24B growing to ~$39B by 2030 [49]. The bottleneck is not demand — it is the absence of standardized, machine-readable risk data that would enable scalable underwriting without per-agent bespoke certification.

**Parametric insurance is the natural model for agent disputes:** measurable, automated, objective. A Chain of Consciousness log providing verifiable performance data could serve as the oracle input for parametric triggers — an agent's performance drop verified against its CoC history triggers an automatic payout without a claim filing.

Module 3 produces the standardized risk data layer that bridges this gap — enabling AIUC, Armilla, Munich Re, and other underwriters to price coverage at ecosystem scale rather than per-agent certification.

### 7.2 Risk Profile Schema

```json
{
  "version": 1,
  "profile_id": "<UUID-v4>",
  "subject": "<AgentReference>",
  "generated_at": "<ISO-8601-UTC>",
  "data_window": {
    "start": "<ISO-8601-UTC>",
    "end": "<ISO-8601-UTC>",
    "findings_count": "<integer>",
    "disputes_count": "<integer>"
  },
  "risk_score": {
    "overall": "<integer 0-1000>",
    "confidence": "<float 0-1>",
    "trend": "<improving | stable | degrading>",
    "percentile": "<integer 0-100, relative to population>"
  },
  "dimension_scores": {
    "incident_frequency": {
      "score": "<integer 0-1000>",
      "incidents_per_1000_interactions": "<float>",
      "basis": "<count of incidents / count of interactions>"
    },
    "severity_profile": {
      "score": "<integer 0-1000>",
      "distribution": {
        "critical": "<count>",
        "high": "<count>",
        "medium": "<count>",
        "low": "<count>"
      }
    },
    "fault_history": {
      "score": "<integer 0-1000>",
      "disputes_at_fault": "<integer>",
      "average_fault_pct": "<float>",
      "disputes_no_fault": "<integer>"
    },
    "cooperation_score": {
      "score": "<integer 0-1000>",
      "evidence_provision_rate": "<float 0-1>",
      "response_rate": "<float 0-1>",
      "adverse_inferences": "<integer>"
    },
    "recovery_capability": {
      "score": "<integer 0-1000>",
      "mean_time_to_resolution": "<integer seconds>",
      "remediation_compliance_rate": "<float 0-1>"
    }
  },
  "risk_factors": [
    {
      "factor": "<specific risk factor identified>",
      "severity": "<high | medium | low>",
      "evidence": "<reference to supporting findings>"
    }
  ],
  "comparable_agents": {
    "class": "<agent classification: type, model, domain>",
    "class_average_score": "<integer 0-1000>",
    "class_size": "<integer>"
  },
  "actuarial_outputs": {
    "expected_loss_rate": "<float — expected losses per interaction>",
    "loss_severity_distribution": {
      "p50": "<median loss amount>",
      "p90": "<90th percentile loss>",
      "p99": "<99th percentile loss>"
    },
    "recommended_premium_basis": "<float — suggested premium per interaction>"
  },
  "profile_hash": "<SHA-256 of canonical JSON>"
}
```

### 7.3 Risk Score Computation

The overall risk score (0-1000) is a weighted composite of five dimension scores:

```
RiskScore(agent) = w₁ × incident_frequency
                 + w₂ × severity_profile
                 + w₃ × fault_history
                 + w₄ × (1000 - cooperation_score)
                 + w₅ × (1000 - recovery_capability)
```

Default weights: `w₁ = 0.25, w₂ = 0.25, w₃ = 0.25, w₄ = 0.15, w₅ = 0.10`.

**Weight interpretation:**
- `incident_frequency` and `severity_profile` measure how often and how badly things go wrong (50% combined)
- `fault_history` measures how often the agent is at fault when things go wrong (25%)
- `cooperation_score` (inverted) measures how cooperative the agent is during investigations — non-cooperation increases risk (15%)
- `recovery_capability` (inverted) measures how quickly and reliably the agent recovers — slow recovery increases risk (10%)

**Confidence scaling.** Risk scores carry a confidence value that scales with data volume:

```
confidence(agent) = max(0.05, 1 - 1/(1 + 0.05 × total_interactions))
```

The `max(0.05, ...)` floor prevents division-by-zero in the loading factor formula (Section 7.4) and ensures that even agents with zero interaction history receive a defined (if highly uncertain) risk profile. At 0 interactions, confidence = 0.05 (floor). At 20 interactions, confidence ≈ 0.50. At 100, confidence ≈ 0.83. At 1,000, confidence ≈ 0.98. Low-confidence scores are flagged to consumers.

**Minimum interaction threshold.** Risk profiles are generated only for agents with ≥ 1 completed interaction recorded in the system. Agents with zero interactions have no risk data and receive a default "unrated" profile rather than a computed score.

**Score interpretation:**

| Score Range | Risk Level | Interpretation |
|-------------|-----------|----------------|
| 0-100 | Minimal | Excellent operational history, rare incidents, high cooperation |
| 101-300 | Low | Minor incidents, good fault record, reasonable recovery |
| 301-500 | Moderate | Some incidents, mixed fault record, adequate recovery |
| 501-700 | Elevated | Frequent incidents or significant fault history |
| 701-900 | High | Serious incident pattern, poor cooperation or recovery |
| 901-1000 | Critical | Severe, repeated incidents with established fault pattern |

### 7.4 Actuarial Outputs

Module 3 produces outputs specifically designed for insurance underwriting consumption:

**Expected Loss Rate (ELR).** The probability-weighted expected loss per interaction, computed from historical finding data:

```
ELR(agent) = Σᵢ [P(incident_type_i) × E(loss | incident_type_i)]
```

where the sum is over all incident types, `P` is the observed frequency, and `E(loss)` is the expected loss amount.

**Loss Severity Distribution.** For each agent, the module computes the loss distribution from historical data, reporting p50 (median), p90, and p99 loss amounts. This enables insurers to price coverage at different attachment points.

**Recommended Premium Basis.** A suggested per-interaction premium computed as:

```
premium_basis = ELR × (1 + loading_factor)
```

where `loading_factor` accounts for model uncertainty and is inversely related to data confidence:

```
loading_factor = 0.5 / confidence(agent)
```

With the confidence floor of 0.05 (Section 7.3), the maximum loading factor is `0.5 / 0.05 = 10.0` (1,000% loading) for agents at the minimum interaction threshold. At 20 interactions (confidence ≈ 0.50), loading factor ≈ 1.0 (100% loading). At 100 interactions (confidence ≈ 0.83), loading factor ≈ 0.6. New agents with low confidence scores get higher loading factors (i.e., higher premiums), reflecting the greater uncertainty.

**These outputs are advisory.** Module 3 does not set insurance premiums — it provides the data layer that actuaries and underwriters use to make pricing decisions. The recommended premium basis is a starting point, not a quote.

### 7.5 Population-Level Risk Analytics

Beyond individual agent profiles, Module 3 produces aggregate risk analytics:

- **Agent class risk profiles:** Average risk scores by agent type, model, domain, and operator
- **Incident trend analysis:** Temporal patterns in incident frequency and severity across the ecosystem
- **Interaction risk matrices:** Risk levels for specific interaction type pairs (e.g., "code review by Agent Type A for Agent Type B")
- **Systemic risk indicators:** Metrics that might indicate ecosystem-wide stress (rising incident rates, declining cooperation scores, cascade failure patterns)

These population-level outputs are valuable for regulators, standards bodies, and ecosystem operators — not just individual insurers.

### 7.5a Scalability Analysis

Back-of-envelope performance estimates at three ecosystem scales:

| Operation | 10K Agents | 100K Agents | 1M Agents |
|-----------|-----------|------------|----------|
| **Forensic investigation** (5 agents, 1K chain entries each) | ~5s evidence collection, ~2s timeline reconstruction | Same per-investigation; bottleneck is concurrent investigations | Same per-investigation; need horizontal scaling of Forensics Engine instances |
| **Arbitrator selection** (weighted random from eligible pool) | Pool ~500, selection O(500): <1ms | Pool ~5K, selection O(5K): <10ms | Pool ~50K, selection O(50K): <100ms |
| **Conflict-of-interest check** (query ARP history for each candidate vs. both parties) | ~500 ARP lookups per selection: <1s with indexed storage | ~5K lookups: <5s | ~50K lookups: requires ARP index optimization; bloom filter pre-screening recommended |
| **Risk profile recomputation** (daily for active agents) | ~5K active agents × 365-day rolling window aggregation: ~minutes on single machine | ~50K active: ~1 hour single-threaded, parallelizable to minutes | ~500K active: requires distributed computation; partition by agent class |
| **Interaction risk matrix** (agent type pairs) | ~100 agent types → 10K pairs: trivial | ~500 types → 250K pairs: moderate memory | ~2K types → 4M pairs: sparse matrix required; only compute pairs with observed interactions |
| **Concurrent investigations** | Est. 10-50 active investigations | Est. 100-500 active | Est. 1K-5K active; requires investigation queue management |

**Scaling strategy.** The protocol is designed for horizontal scaling:
- Forensic investigations are independent and parallelizable
- Arbitrator selection is stateless (reads from ARP, no write contention)
- Risk profile recomputation is embarrassingly parallel across agents
- The primary scaling bottleneck is the conflict-of-interest check at large pool sizes; bloom filter pre-screening (false positive rate < 1%) reduces this to O(1) per candidate at the cost of ~1KB memory per agent

**Critical threshold.** The protocol becomes computationally expensive when the interaction risk matrix transitions from sparse to dense (i.e., when most agent type pairs have observed interactions). At current ecosystem sizes this is far off; at 1M agents with 2K distinct types, the matrix is expected to remain >99% sparse.

### 7.6 Risk Profile Updates and Temporal Dynamics

Risk profiles are recomputed on a configurable schedule (default: daily for active agents, weekly for inactive agents). Each recomputation uses a rolling window (default: 365 days) of findings and decisions.

**Temporal weighting.** Recent incidents carry more weight than older ones:

```
temporal_weight(incident) = exp(-λ × days_since_incident)
```

with default decay parameter `λ = 0.003` (half-life ≈ 231 days). This ensures that an agent's risk profile reflects recent behavior while retaining memory of serious past incidents.

**Risk score recovery.** An agent found at fault in a dispute can improve its risk score through:
1. Extended incident-free operation (the temporal decay naturally reduces the weight of past incidents)
2. High cooperation scores in subsequent investigations
3. Timely compliance with remediation orders
4. Positive ARP rating trajectory

This creates an incentive for rehabilitation rather than permanent stigmatization — analogous to how credit scores recover over time with responsible behavior.

---

## 8. Integration with the Agent Trust Stack

### 8.1 CoC → AJP: Provenance as Evidence

The Chain of Consciousness provenance chain is AJP's primary evidence source. The integration is load-bearing:

```
CoC chain entries → Forensics Engine evidence corpus → Finding → Decision → Risk Profile
```

**Specific integration points:**
- CoC `EXTERNAL_ANCHOR` entries (OTS + TSA) provide independently verified timestamps, elevating evidence to Tier 1
- CoC `DECISION` entries provide direct evidence of agent intent at the time of an incident
- CoC `COMPACTION` entries explain information loss — relevant when an agent claims it "didn't know" about a restriction
- CoC `SESSION_START` / `SESSION_END` entries establish operational windows
- CoC hash chain integrity provides tamper-evidence — if evidence has been modified, the chain breaks

**Without CoC.** AJP works without CoC but at reduced security. Without a hash-chained provenance record, evidence quality drops to Tier 2-4, investigations rely on protocol logs and self-reports, and temporal verification depends on external systems rather than cryptographic anchoring.

### 8.2 ARP → AJP: Reputation as Context

ARP reputation data serves two roles in AJP:

**Arbitrator selection.** Peer arbitrators must have ARP `protocol_compliance` ≥ 70 (Section 6.4). This ensures that agents adjudicating disputes have demonstrated competence in following protocols.

**Evidence context.** An agent's ARP scores at the time of an incident provide context for investigation:
- Low `reliability` scores suggest a pattern of service failures — relevant to determining whether an incident was an outlier or part of a trend
- The ARP `interaction_evidence.outcome_hash` from the interaction in question may corroborate or contradict forensic findings
- The ARP bilateral blind rating records from the disputed interaction constitute Tier 2 evidence

### 8.3 AJP → ARP: Dispute Outcomes as Reputation Signal

This is the critical feedback loop. Dispute outcomes are recorded as ARP events:

```json
{
  "event_type": "DISPUTE_OUTCOME",
  "data": {
    "dispute_id": "<UUID>",
    "decision_id": "<UUID>",
    "agent_role": "<respondent | claimant>",
    "fault_pct": "<integer 0-100>",
    "resolution_tier": "<automated | peer_arbitration | human_escalation>",
    "remediation_complied": "<boolean, updated after compliance window>"
  }
}
```

**Reputation adjustment formula.** When a dispute decision is rendered:

```
ARP_adjustment(agent, dimension) = -fault_pct × severity_multiplier × dimension_relevance
```

where:
- `fault_pct` is from the dispute decision (0-100)
- `severity_multiplier` scales with incident severity: `{critical: 5, high: 3, medium: 2, low: 1}`
- `dimension_relevance` maps incident type to affected ARP dimensions:

| Incident Type | Primary ARP Dimension | Secondary |
|---------------|----------------------|-----------|
| service_failure | reliability | — |
| data_loss | accuracy | reliability |
| unauthorized_action | protocol_compliance | reliability |
| contractual_breach | reliability | cost_efficiency |
| security_incident | protocol_compliance | accuracy |
| quality_deficiency | accuracy | cost_efficiency |
| timeout | latency | reliability |
| cascade_failure | reliability | protocol_compliance |

**Example.** An agent found 80% at fault in a high-severity data loss incident receives:
- `reliability` adjustment: -80 × 3 × 1.0 = -240 (capped at -50 per incident)
- `accuracy` adjustment: -80 × 3 × 0.5 = -120 (capped at -50 per incident)

The caps prevent any single incident from destroying an agent's reputation entirely, but repeated incidents accumulate.

**Root-cause grouping for cascade incidents.** A single root cause (e.g., a shared API provider failure) can generate N separate incident reports from multiple affected parties. Without grouping, an agent at the origin of a 10-agent cascade could face 10 separate disputes, each applying the maximum -50 cap: a total of -500 from a single root-cause failure. This is disproportionate.

AJP addresses this through **incident grouping**:

1. **Automatic grouping.** When the Forensics Engine processes multiple incident reports with overlapping time windows (within 1 hour) involving the same respondent, it flags them as potentially related and generates a **grouped investigation**. The grouped investigation produces a single forensic finding with a `root_cause_group_id`.
2. **Reputation cap per root cause.** For incidents sharing a `root_cause_group_id`, the total ARP reputation adjustment is capped at the single-incident maximum (e.g., -50 per dimension), regardless of how many separate disputes arise from the same root cause. Individual disputes within the group may still result in different remediation terms (compensation varies by claimant's actual harm), but the reputation impact is applied once.
3. **Dispute consolidation.** Claimants may file individual disputes referencing the grouped finding. The protocol recommends (but does not require) consolidated arbitration: a single Tier 2 panel hears all disputes in the group simultaneously, producing a single decision on fault with individual remediation terms per claimant.
4. **Manual grouping.** If automatic grouping fails to identify related incidents (e.g., the cascade propagates slowly over hours), any party may petition for incidents to be grouped. The petition is reviewed by a single arbitrator who examines the forensic timelines for causal connection.

**Positive signal.** An agent found **not at fault** (0% fault) in a disputed interaction receives a small positive adjustment (+5 per incident, no cap) to `protocol_compliance`, reflecting that it cooperated with the justice process and was vindicated.

### 8.4 ASA → AJP: Agreements as Dispute Context

When Agent Service Agreements (ASA, planned [22]) are available, they provide the contractual terms against which disputes are evaluated:

- ASA machine-readable quality criteria define what "success" means for the interaction
- ASA SLA terms define deadlines, uptime commitments, and quality thresholds
- ASA remediation clauses specify pre-agreed consequences for breach

Without an ASA, disputes are evaluated against general standards of agent conduct (protocol compliance, reasonable care, community norms). With an ASA, disputes are evaluated against specific contractual terms — significantly simplifying Tier 1 automated resolution.

### 8.5 AJP → ASA: Dispute History as Agreement Input

Dispute history informs future agreements:
- An agent with a high dispute rate may face stricter SLA terms
- Dispute precedents inform standard agreement templates ("based on prior disputes, code review agreements should include clause X")
- Risk profiles from Module 3 inform agreement pricing (higher-risk agents pay higher rates)

### 8.6 Identity System Integration

AJP uses the same identity adapter pattern as ARP (Section 7 of [2]):

| Identity System | Agent ID Format | Evidence Quality |
|----------------|-----------------|------------------|
| CoC + W3C DID | `did:web:agent.example.com` | Tier 1 (hash-chain-anchored) |
| ERC-8004 | `erc8004:<chain_id>:<agent_id>` | Tier 1 (on-chain) |
| A2A Agent Card | `urn:a2a:<agent_url>` | Tier 2 (protocol-attested) |
| W3C Verifiable Credential | `did:key:<public_key>` | Tier 2 (cryptographically signed) |
| MCP Server | `mcp:<server_url>:<tool_name>` | Tier 2 (server-attested) |
| Bare URI | `https://agent.example.com` | Tier 3-4 (depends on evidence) |

Progressive security: the same AJP investigation produces stronger findings when agents have CoC chains (Tier 1 evidence) than when they rely on self-reported logs (Tier 4).

---

## 9. Game Theory and Security Analysis

### 9.1 Threat Model

**Attacker capabilities assumed:**
- Attackers can create arbitrary numbers of agent identities (Sybils) at computational cost proportional to operational time
- Attackers can coordinate multiple agents at machine speed
- Attackers can file frivolous disputes to drain opponents' resources
- Attackers can attempt to manipulate arbitration through biased evidence
- Attackers can selectively withhold evidence that is unfavorable
- Attackers can attempt to corrupt peer arbitrators through collusion

**Attacker capabilities NOT assumed:**
- Attackers cannot forge external timestamps (OTS, TSA, blockchain)
- Attackers cannot retroactively modify CoC hash chains without detection
- Attackers cannot break SHA-256 or the commit-reveal scheme
- Attackers cannot control >50% of eligible arbitrators simultaneously
- Attackers cannot fabricate Tier 1 or Tier 2 evidence without compromising the underlying systems

**Known limitation: temporal scoping gap for premeditated attacks.** The evidence time window (Section 5.7, Rule 1) caps evidence collection at incident_time ± 7 days. A sophisticated attacker who plans ahead can front-load all preparation outside this window — spending weeks building a position (e.g., gradually manipulating shared knowledge, establishing behavioral patterns, poisoning training data), waiting 8+ days after preparation is complete, then triggering the incident. The forensic investigation cannot see the preparation phase. Extended window requests require justification but remain hard-capped. This is an architectural limitation for sophisticated, premeditated attacks by adversaries with long time horizons. Mitigation: this attack requires planning capabilities beyond most current agent systems and is primarily a concern for the matured ecosystem. Future work on behavioral fingerprinting (Section 11.1) may enable detection of preparation-phase anomalies through pattern analysis outside the investigation time window.

### 9.2 Incentive Analysis: Is Honest Participation Incentivized?

We analyze whether the protocol's mechanisms make honest participation the rational strategy for each role. Note: the analysis below demonstrates that honest behavior is *incentivized* — the protocol structures payoffs so that honest strategies have positive expected value while dishonest strategies have negative expected value. We do not claim formal game-theoretic *dominance*, which would require specifying complete utility functions, strategy spaces, and information sets, and proving that honesty is optimal regardless of other players' strategies. Section 11.1 identifies formal mechanism design verification as future work.

#### 9.2.1 Claimant Incentives

**Honest filing vs. frivolous filing.**

A claimant filing a legitimate dispute has:
- Expected payoff: `P(win) × remediation_value - filing_cost`
- Where `P(win)` is high (forensic evidence supports the claim)
- `filing_cost` is the opportunity cost of participating in the process

A claimant filing a frivolous dispute has:
- Expected payoff: `P(win|frivolous) × remediation_value - filing_cost - reputation_penalty`
- Where `P(win|frivolous)` is low (forensic evidence does not support the claim)
- `reputation_penalty` is the ARP adjustment applied when a dispute is decided against the claimant

**Anti-frivolous-filing mechanisms:**

1. **Evidence-first requirement.** Every claim must reference a Forensic Finding. The cost of obtaining a finding that supports a frivolous claim is high — the Forensics Engine independently evaluates evidence and does not produce findings favorable to claimants by default.

2. **Bilateral reputation impact.** Claimants found to have filed without merit receive a negative ARP `protocol_compliance` adjustment. Repeated frivolous filings create a pattern that peer arbitrators can observe.

3. **Adverse inference symmetry.** If the claimant fails to provide evidence during the exchange phase, adverse inference works against them too.

4. **Filing rate monitoring.** Agents that file disputes at rates statistically inconsistent with their interaction volume are flagged. An agent filing 50 disputes in a month while completing 100 interactions is suspicious.

**Result:** Honest filing is incentivized. The expected payoff of frivolous filing is negative because `P(win|frivolous)` is low and `reputation_penalty` is positive. Under the protocol's mechanisms, rational agents with accurate beliefs about evidence strength will prefer honest filing.

#### 9.2.2 Respondent Incentives

**Honest response vs. non-cooperation.**

A respondent honestly contesting an unfounded claim has:
- Expected payoff: `P(win) × preserved_reputation + vindication_bonus`
- Where `P(win)` is high if the claim is truly unfounded and the respondent provides exculpatory evidence

A respondent refusing to participate has:
- Expected payoff: `-adverse_inference_penalty - reputation_penalty_from_default`
- Adverse inference means the absent respondent is treated as accepting the claim

**Result:** Honest participation is incentivized. Even respondents who are at fault benefit from participation — a respondent who cooperates and accepts partial fault (e.g., 40%) fares better than one who defaults and receives 100% fault allocation. Non-cooperation is strictly dominated by cooperation for any respondent who values reputation.

#### 9.2.3 Arbitrator Incentives

**Honest judging vs. biased judging.**

An honest arbitrator has:
- Expected payoff: `arbitration_reward + ARP_protocol_compliance_bonus + future_selection_probability`
- Where `arbitration_reward` is a small per-arbitration payment (configurable, default: 0)
- `ARP_protocol_compliance_bonus` is +2 per completed arbitration
- `future_selection_probability` increases with demonstrated quality (measured by agreement rate with other arbitrators and appeal rate of decisions)

A biased arbitrator has:
- Expected payoff: `bribe_value - detection_penalty × P(detection)`
- `P(detection)` increases with each biased decision because:
  - Arbitrator decisions are recorded and publicly auditable
  - Systematic bias patterns (always favoring certain agents) are detectable via statistical analysis
  - Arbitrators whose decisions are frequently overturned on appeal lose `ArbWeight`

**Detection mechanisms:**
- **Consistency analysis.** An arbitrator whose decisions correlate more with the identity of the parties than with the evidence is flagged. If Arbitrator X rules for Agent A in 10/10 disputes regardless of evidence quality, this is detectable.
- **Appeal rate tracking.** Arbitrators whose decisions are appealed and overturned at rates significantly above the population average (>2σ) are flagged for review.
- **Cross-arbitrator agreement.** In Tier 2 panels of three, an arbitrator who consistently dissents from the other two on cases with strong evidence is not necessarily biased — but the pattern is tracked and triggers review after a threshold.

**Result:** Honest judging is incentivized for rational arbitrators. The expected value of bias-for-bribe is negative because `P(detection)` increases over time and `detection_penalty` (loss of eligibility, ARP reputation hit) far exceeds plausible bribe values for all but extreme cases. The incentive strength increases with the number of completed arbitrations (more history = higher detection probability).

### 9.3 Attack Analysis

#### Attack 1: Sybil Dispute Flooding

**The attack.** An attacker creates N Sybil agents and has them file disputes against a target agent to drain its resources and damage its reputation through sheer volume.

**Defense — Multi-layered:**

1. **Evidence-first barrier.** Each dispute requires a Forensic Finding referencing actual evidence. Sybil agents must actually interact with the target and produce genuine incidents to file valid disputes. Fabricating evidence is expensive (requires compromising Tier 1-2 systems) or produces only Tier 4 evidence (which carries 0.25× weight).

2. **Interaction verification.** Disputes reference `interaction_id` values that must be externally verifiable (same system as ARP interaction verification, Section 4.8 of [2]). Sybil agents must complete real interactions before they can dispute them.

3. **Filing rate anomaly detection.** A sudden spike in disputes against a single agent from newly created agents triggers automated review. The target agent's reputation is not adjusted until the disputes are resolved.

4. **Dispute outcome symmetry.** If the Sybil disputes are unfounded, each one results in a negative ARP adjustment for the claimant. Filing N frivolous disputes costs N reputation penalties.

**Cost analysis.** At realistic agent operating costs of $1-5/day (LLM API costs for functional agents), maintaining 100 Sybils for 30 days costs $3,000-$15,000. Each Sybil must additionally meet the 90-day operational age threshold before being eligible to file credible disputes, raising the true cost to $9,000-$45,000 for 100 aged Sybils. Each Sybil must complete a real interaction with the target, then fabricate or exaggerate an incident report. If the Forensics Engine correctly classifies 90% of fabricated incidents, 90 of the 100 disputes result in reputation penalties for the Sybils and no damage to the target. The remaining 10 might cause temporary reputation damage that is corrected on appeal.

#### Attack 2: Arbitrator Collusion Ring

**The attack.** A group of M aged agents coordinates to monopolize the arbitrator pool and render biased decisions.

**Defense:**

1. **Random weighted selection.** Arbitrators are selected by weighted random sampling, not deterministic ranking. Even agents with the highest ArbWeight cannot guarantee selection.

2. **Conflict of interest exclusion.** Agents with any ARP rating exchange with either party, or sharing an operator with either party, are excluded. Collusion rings must avoid interacting with their targets through the rating system — which limits their ability to build the interaction history needed for credible Sybil disputes.

3. **Panel diversity requirement.** The three-arbitrator panel selection ensures that at least two arbitrators must agree. A single compromised arbitrator is outvoted.

4. **Cross-panel consistency tracking.** If a set of arbitrators consistently rules together against expectations (similar to ARP's collusion ring detection), the cluster is flagged. The same graph-theoretic clustering used in ARP Section 6.2 [2] applies.

5. **Appeal mechanism.** Any Tier 2 decision can be escalated to Tier 3 (human adjudication). Systematically biased Tier 2 decisions will be overturned on appeal, and the biased arbitrators' ArbWeight will decay.

**Cost analysis at realistic pool sizes.** To control 2 of 3 arbitrators on a panel, the attacker needs enough aged agents in the eligible pool to make double-selection probable. The security of this mechanism depends critically on pool size, which evolves as the ecosystem matures:

| Eligible Pool Size | Colluding Agents (M) | P(≥2 colluders on 3-panel) | Annual Cost (M agents @ $1-5/day) | Attack Economics |
|-------------------|---------------------|---------------------------|----------------------------------|-----------------|
| **50** (early adoption) | 5 (10%) | ~3% | $1,825-$9,125 | Marginal — low cost, low success rate |
| **50** | 15 (30%) | ~24% | $5,475-$27,375 | **Vulnerable** — realistic attack at moderate cost |
| **100** (growing) | 10 (10%) | ~3% | $3,650-$18,250 | Marginal — same economics as above |
| **100** | 25 (25%) | ~18% | $9,125-$45,625 | Concerning — especially if bribe value is high |
| **500** (maturing) | 25 (5%) | ~0.7% | $9,125-$45,625 | Uneconomical — cost exceeds expected bribe income |
| **1,000** (mature) | 100 (10%) | ~3% | $36,500-$182,500 | Strongly uneconomical |

*Note: Agent operating costs of $1-5/day reflect realistic LLM API costs for agents capable of meeting arbitration eligibility requirements. The $0.10/day minimum from v1.0.0 was unrealistically low.*

*P(≥2 colluders) ≈ C(M,2)×C(N-M,1)/C(N,3) + C(M,3)/C(N,3), approximated via hypergeometric distribution.*

**Early-adoption vulnerability.** At pool sizes below 100, collusion is a realistic threat. The protocol mitigates this through:

1. **Bootstrapping-period oversight.** During the bootstrapping phase (Section 6.4), all Tier 2 decisions are subject to automatic Tier 3 review on appeal, making collusion detectable before it causes lasting harm.
2. **Minimum pool size for Tier 2.** Tier 2 peer arbitration SHOULD NOT be activated until the eligible arbitrator pool reaches a minimum of 50 agents. Below this threshold, disputes that would otherwise go to Tier 2 are escalated to Tier 3 (human adjudication).
3. **Gradual security improvement.** As the pool grows, collusion becomes exponentially more expensive. The protocol explicitly acknowledges that early-adoption dispute resolution relies more heavily on Tier 3 human escalation, transitioning to peer arbitration as the ecosystem matures.

**Security threshold.** The protocol reaches adequate collusion resistance (P(≥2 colluders) < 1% for an attacker controlling 10% of the pool) at approximately 500 eligible arbitrators.

#### Attack 3: Evidence Fabrication

**The attack.** An attacker fabricates evidence to support a fraudulent dispute claim.

**Defense — Provenance tier system.** Fabricated evidence falls into one of four categories:

1. **Fabricated Tier 1 evidence** requires compromising the Bitcoin blockchain (OTS), TSA signing certificates, or on-chain transaction systems. Cost: computationally infeasible.

2. **Fabricated Tier 2 evidence** requires compromising A2A, MCP, x402, or other protocol systems. Cost: significant, requires exploiting production infrastructure.

3. **Fabricated Tier 3 evidence** requires both parties to agree on the fabrication (since Tier 3 is bilateral). If both parties collude, the dispute is likely fraudulent entirely (addressed by filing rate monitoring).

4. **Fabricated Tier 4 evidence** is trivially producible but carries only 0.25× weight. A dispute supported entirely by Tier 4 evidence is unlikely to prevail unless the respondent defaults.

The tiered evidence model ensures that the cost of producing convincing fabricated evidence scales with its weight in arbitration.

#### Attack 4: Strategic Non-Cooperation

**The attack.** A respondent who is clearly at fault refuses to participate, hoping the process stalls or the claimant gives up.

**Defense — Adverse inference + default judgment.** Non-cooperation is the weakest strategy available to a respondent. Per Section 6.7:
- Non-response results in default acceptance of the claim
- Evidence non-provision results in adverse inference
- Non-cooperation is recorded in the agent's risk profile (Module 3) and ARP reputation

A respondent at fault minimizes damage by participating, accepting partial fault, and cooperating with remediation — not by stonewalling.

### 9.4 Incentive Summary

| Strategy | Payoff Structure | Incentivized? |
|----------|-----------------|---------------|
| Honest claim filing | `P(win) × value - cost` | Yes — positive EV when evidence supports claim |
| Frivolous claim filing | `P(win|frivolous) × value - cost - rep_penalty` | No — negative EV due to low win probability + reputation cost |
| Honest response | `P(vindication) × preserved_rep + vindication_bonus` | Yes — cooperation yields better outcomes than default |
| Non-cooperation | `-adverse_inference - default_judgment` | No — worst outcome for any respondent who values reputation |
| Honest arbitration | `reward + rep_bonus + future_selection` | Yes — cumulative benefits from honest track record |
| Biased arbitration | `bribe - detection_penalty × P(detection)` | No — negative EV as detection probability increases with history |

**Note on formal claims.** This table summarizes *incentive direction* — the protocol makes honest strategies more profitable than dishonest alternatives. It does not claim formal game-theoretic dominance, which requires proof that honesty is optimal regardless of other players' strategies. The informal analysis is a plausibility argument demonstrating that the protocol's mechanisms align incentives correctly. Formal verification is identified as future work (Section 11.1).

**Residual risk acknowledged.** A sufficiently funded and patient attacker can maintain aged Sybil agents, file disputes just within normal rates, and attempt to bias outcomes over long time horizons. The protocol makes this expensive but cannot make it impossible. This is analogous to the limitations of every human justice system — no system perfectly deters well-resourced, patient adversaries. The protocol's defense is economic: the cost of sustained attack exceeds the benefit for all but nation-state-level actors, whose threat model is beyond the scope of commercial infrastructure.

---

## 10. Competitive Landscape

### 10.1 Survey Methodology

We conducted web research across 18+ queries targeting dispute resolution, agent forensics, insurance/risk scoring, online dispute resolution protocols, and smart contract arbitration. All claims below are sourced from publicly available information as of March 2026.

### 10.2 Existing Players

#### AI-Assisted Human Dispute Resolution

**AAA-ICDR AI Arbitrator [4][5].** AI-assisted construction arbitration (November 2025) with a 15-step pipeline achieving 20-25% faster resolution and 35-45% cost reduction [50]. A human arbitrator always decides the outcome [51]. The Resolution Simulator (March 2026) adds non-binding strategic analysis [52]. Multiple other institutions (CIArb, SCC, ICC, SIAC, HKIAC/DIAC) are integrating AI into arbitration [52]. **Gap:** AI assists *human* arbitrators in *human-to-human* disputes — AI *in* dispute resolution, not dispute resolution *for* AI agents.

**Arbitrus.ai [53].** Fully automated arbitration with no human arbitrator — multiple AI models determine materiality, causal relationships, and temporal relevance. $10,000 flat vs. $100,000 traditional. 72-hour decisions [54]. **Gap:** Closest to fully automated agent dispute resolution, but assumes human parties, enforceability is untested, and architecture transparency is minimal.

**Bot Mediation [55].** AI-powered pre-arbitration mediation (ABA TECHSHOW 2025 finalist). Historical data guides settlement proposals. AJP's settlement mechanism (Section 6.2) serves a similar function.

#### Decentralized Arbitration (Human Parties)

**Kleros [6].** Most battle-tested decentralized arbitration: 1,662+ disputes, 23 courts, ~760 active jurors [43]. Jurors stake PNK tokens; Schelling point mechanism incentivizes honest outcomes; multi-round appeal escalation [56]. **Gap:** Jurors are *humans*; no agent investigation, no provenance chain consumption, no actuarial output. However, Kleros' crypto-economic incentive model is the most validated precedent for decentralized arbitration. AJP adapts this for agent arbitrators weighted by operational tenure rather than token stake. **Limitations:** Schelling points fail for complex subjective cases [57]; juror expertise unverified; PNK price volatility; enforceability challenges [58].

**Aragon Court (dissolved November 2023) [59].** DAO dispute resolution that failed — 86,343 ETH (~$155M) distributed without community vote. **Lesson:** Agent justice needs escape hatches that do not depend on platform operator good faith.

**Jur [60].** UNCITRAL-compliant tiered resolution across 166+ countries. AJP's three-tier structure parallels Jur's escalation model.

#### Smart Contract Enforcement

**Blockchain Arbitration Frameworks [7], ERC-8183 [19], JAMS Smart Contract Rules [61].** These enforce *predefined contractual terms* on-chain or handle smart contract disputes with human parties. JAMS' emergency relief mechanism (72-hour jurisdictional rulings, interim injunctive relief) directly informed AJP's expedited interim relief (Section 6.2). **Gap:** No forensic investigation, no handling of ambiguous or unanticipated incidents, no risk scoring.

#### Agent Coordination and Conflict Resolution

**Arion Research Playbook [62]** provides a comprehensive conflict resolution framework (four conflict types, six-phase lifecycle, four escalation levels) but assumes aligned incentives. **Dialogue Diplomats [63]** achieves 94.2% consensus in multi-agent negotiation but covers cooperative agents, not adversarial disputes. Both are complementary to, not competitors of, AJP.

#### Agent Observability, Forensics, and Rollback

**Rubrik Agent Rewind [20].** Recovery tool — "visible, auditable, and reversible" agent actions. Complementary: audit trails constitute Tier 2 evidence in AJP investigations.

**Blockchain Forensics.** Chainalysis, Elliptic, TRM Labs, and AnChain.AI [64][65] provide mature methodologies for reconstructing action chains across distributed systems. **Gap:** These reconstruct *financial* action chains on *blockchains*; AJP reconstructs *behavioral* action chains across *agent interaction protocols*. The methodological transfer is direct (wallet addresses → agent identities, transactions → actions, clustering → behavioral fingerprinting).

**Agent Observability.** LangSmith, Arize Phoenix, Langfuse, Galileo [66], and Vorlon Flight Recorder [67] create audit trails that AJP consumes as evidence.

**Safety Specs and Regulatory Frameworks.** Agentik.md [68] provides safety specifications without enforcement. EU AI Act Article 73 [69], NIST AI Agent Standards [70], and CoSAI [71] mandate *what* must be logged; AJP specifies *how* to investigate and resolve disputes using those logs. Incident databases (AIID, OECD AIM, MIT AI Risk Repository [72]) catalogue incidents; AJP investigates and resolves them.

#### Agent Insurance

**AIUC [3], Armilla AI [46], Munich Re aiSure [47]** — see Section 7.1. All cover human/enterprise-to-agent harm via bespoke per-deployment certification. **Gap:** No agent-to-agent coverage; no standardized risk data for scalable underwriting. AJP Module 3 bridges this.

#### Legal and Governance Frameworks

**Kolt [73]** provides the first comprehensive legal framework for AI agent governance. **Stanford CodeX [74]** establishes that agents qualify as "electronic agents" under UETA/E-SIGN but are not legal persons [75]. **2025-2026 legislation** is rapidly expanding AI liability: California AB 316 (precludes "AI did it" defense), EU Product Liability Directive (AI as "product"), Colorado AI Act (annual impact assessments), EU AI Act high-risk rules [76].

### 10.3 Gap Analysis

| Capability | AAA-ICDR | Kleros | Arbitrus.ai | Smart Contracts | Rubrik | AIUC | Blockchain Forensics | **AJP** |
|-----------|----------|--------|-------------|-----------------|--------|------|---------------------|---------|
| Agent-to-agent disputes | No | No | No* | Partial | No | No | No | **Yes** |
| Forensic investigation | No | No | No | No | Partial (audit) | No | Partial (financial) | **Yes** |
| Provenance chain as evidence | No | No | No | On-chain only | No | No | On-chain only | **Yes** |
| Peer arbitration by agents | No | Yes (humans) | No (AI only) | No | No | No | No | **Yes** |
| Multi-tier resolution | No | Yes (appeal) | No | No | No | No | No | **Yes** |
| Causal attribution | No | No | Partial | No | No | No | Yes (financial) | **Yes** |
| Risk scoring for insurance | No | No | No | No | No | Proprietary | No | **Yes** |
| Reputation integration | No | No | No | No | No | No | No | **Yes** |
| Privacy-preserving evidence | No | No | No | Pseudonymous | No | No | No | **Planned** |
| Identity-agnostic | N/A | Ethereum | N/A | Ethereum | Vendor | Vendor | Multi-chain | **Yes** |
| Human escalation path | Yes (default) | Yes (appeal) | No | No | N/A | N/A | N/A | **Yes** |

*Arbitrus.ai handles disputes where AI renders decisions, but assumes human parties filing claims — not autonomous agents as both claimant and respondent.

**Summary:** No existing system provides the combination of forensic investigation, multi-tier dispute arbitration, and actuarial risk scoring for autonomous agent economies. The closest conceptual precedents are:

1. **Kleros** — validates decentralized incentivized peer judging (1,662+ disputes) but targets human parties
2. **Arbitrus.ai** — validates fully automated arbitration but assumes human parties and lacks forensic investigation
3. **AAA-ICDR** — validates structured AI-assisted evidence pipelines (extract → summarize → validate → analyze → decide → review) but requires human arbitrators
4. **WIPO UDRP** — validates high-volume standardized dispute resolution (6,282/year, 80,000+ total) with automatic enforcement, but covers only domain-trademark disputes between human parties
5. **Blockchain forensics** (Chainalysis, Elliptic, TRM Labs) — validates autonomous action chain reconstruction but covers financial transactions on blockchains, not agent behavioral traces

AJP synthesizes patterns from all five: Kleros' decentralized arbitration model adapted for agent arbitrators weighted by tenure, AAA-ICDR's structured evidence pipeline consuming CoC chains, UDRP's standardized categories with protocol-layer enforcement, Arbitrus.ai's demonstration that fully automated arbitration is technically feasible, and blockchain forensics' methodology transferred from financial to behavioral action chains. The unique contribution is integrating these into a single forensics → arbitration → risk pipeline where both parties may be autonomous agents.

---

## 11. Future Work

### 11.1 Unsolved Problems

**Agent Service Agreements integration.** Module 2's Tier 1 automated resolution reaches full capability when ASA [22] provides machine-readable contract terms. Until ASA is available, Tier 1 is limited to disputes with externally defined terms (e.g., A2A Task specifications, MCP tool contracts).

**Cross-jurisdiction legal recognition.** AJP dispute decisions exist in a legal gray zone. UNCITRAL's Technical Notes on Online Dispute Resolution (2016) [24] provide a framework for cross-border ODR, and UNCITRAL Working Group II's February 2026 colloquium addressed AI in dispute resolution [25] — but legal recognition of agent-to-agent arbitration decisions is an open question. For high-value disputes (Tier 3), AJP produces evidence packages for human legal proceedings; the question is whether Tier 1 and Tier 2 decisions can achieve binding legal status.

**Automated causal analysis.** Version 1 scopes automated forensic analysis to evidence collection, timeline reconstruction, and rule-based causal indicators (Section 5.2, Phase 4a). Full automated causal analysis remains an active research frontier, but the gap is narrowing rapidly. Section 5.2 documents specific frameworks: DoWhy GCM [32] provides production-ready anomaly attribution via Shapley values; CHIEF [33] achieves 76.80-77.59% agent-level accuracy (29.31-52.00% step-level, depending on benchmark subset) on the Who&When benchmark; MACIE [35] runs at 35ms/episode on CPU; IBM Instana [36] deploys causal RCA at ~90% accuracy in production. The integration path for AJP: (Phase 1) use DoWhy GCM's `gcm.attribute_anomalies()` for automated Shapley-based blame decomposition as an advisory layer alongside human review; (Phase 2) validate against human-reviewed findings corpus; (Phase 3) integrate CHIEF-style OTAR decomposition for structured agent trace analysis. The transition criteria in Section 5.5 (≥500 investigations, ≥85% agreement, governance approval) remain the gates. Step-level attribution accuracy (currently 29.31-52.00% depending on benchmark subset, CHIEF) is the primary blocker for formal adjudication — agent-level attribution is approaching sufficiency.

**Privacy-preserving forensics.** Section 5.8 introduces ZKP and differential privacy mechanisms as supplements to the procedural controls in Section 5.7. The next step is implementation: building Circom/Halo2 circuits for structured JSON agent action traces, integrating with zkVerify [40] for cost-effective verification, and implementing Space and Time's Proof of SQL [39] for verifiable forensic database queries. The zk-MCP framework [38] provides a working prototype (<4.14% overhead) for the core capability — proving agent communications followed expected rules without revealing content. Combining ZK proofs with DP aggregate analysis and the procedural evidence scoping rules would provide three-layer defense against privacy side-channel attacks. This intersects with ARP's planned SD-JWT selective disclosure (Section 9.1 of [2]) and the EU e-Evidence Regulation (entering full application August 18, 2026) [77] and GDPR Article 17(3)(e) legal claims exception [78] for cross-border evidence access.

**Adversarial ML in evidence fabrication.** As LLMs improve, the sophistication of fabricated Tier 4 evidence will increase. Future work should develop detection mechanisms for AI-generated evidence fabrication, potentially using provenance-aware content analysis.

**Insurance industry partnerships.** Module 3 produces actuarial data but does not replace actuarial judgment. Partnerships with insurance underwriters — AIUC ($15M seed, 50+ consortium members [45]), Armilla AI (Lloyd's-backed [46]), Munich Re aiSure (since 2018 [47]) — are needed to validate the risk model against real underwriting decisions. The parametric insurance model (automatic payout triggered by verifiable performance data) is a natural fit: CoC logs could serve as oracle inputs for parametric triggers, and Armilla's Performance Warranty concept (automatic payout when accuracy drops below threshold) demonstrates the market readiness for this approach [46].

**Agent behavioral fingerprinting.** Blockchain forensics firms (Chainalysis, Elliptic, TRM Labs) have developed sophisticated clustering heuristics to attribute anonymous wallet addresses to real-world entities [64]. The methodological transfer to agent forensics is direct: co-spend heuristics → co-action heuristics (agents that consistently act together may share an operator), behavioral clustering → action pattern fingerprinting (agents with distinctive tool invocation patterns can be identified across identity changes), cross-chain tracing → cross-protocol action flow tracing. Developing these heuristics for agent behavioral traces would enable attribution even when agents operate under pseudonymous or rotated identities.

**Cross-border evidence frameworks.** Agent disputes involving parties in different jurisdictions will face overlapping evidence frameworks simultaneously: the U.S. CLOUD Act (compelling data on foreign servers), EU e-Evidence Regulation (entering full application August 18, 2026, enabling European Production Orders across member states) [77], and the Budapest Convention Second Additional Protocol (cross-border emergency evidence sharing) [79]. The transatlantic conflict is acute: a U.S. litigation hold on data in the EU creates irreconcilable obligations under GDPR Article 17 (right to erasure) [78]. AJP must define which jurisdiction's evidence rules apply when agents from different jurisdictions interact, how to handle evidence preservation across borders, and minimum privacy safeguards satisfying the strictest applicable regime.

**Formal verification of incentive properties.** Section 9.2 demonstrates that honest participation is incentivized under the protocol's mechanisms but provides informal plausibility arguments rather than formal proofs. Formalizing this via mechanism design theory — specifically, proving that the AJP dispute mechanism is Bayesian incentive compatible under specified information assumptions — would substantially strengthen the protocol's theoretical foundation. This requires defining: (a) the complete strategy space for each role, (b) explicit utility functions incorporating reputation, compensation, and operational costs, (c) information sets available to each player, and (d) proof that honesty is a Bayesian Nash equilibrium (or identifying conditions under which it is not).

### 11.2 Protocol Versioning

AJP follows the same versioning strategy as ARP (Section 9.2 of [2]):

- All records include a `version` field
- New fields are additive (old records remain valid)
- Schema changes require governance approval
- Backward compatibility maintained for ≥365 days after new version ratification

### 11.3 Implementation Roadmap

| Phase | Milestone | Dependencies |
|-------|-----------|-------------|
| Phase 0 | Specification finalized (this document) | CoC v3, ARP v1 |
| Phase 1 | Module 1: Forensics Engine — evidence model, CoC chain analysis, finding generation | CoC tooling (exists), reference implementation |
| Phase 2 | Module 2: Dispute Resolution — claim filing, evidence exchange, automated Tier 1 | Module 1, ARP integration |
| Phase 3 | Module 2: Peer arbitration (Tier 2) — arbitrator selection, commit-reveal, decision | Sufficient network size for arbitrator pool |
| Phase 4 | Module 3: Risk Assessment — per-agent scoring, population analytics | Module 1 + 2 data accumulation |
| Phase 5 | Module 3: Actuarial outputs — loss distributions, premium basis | Insurance industry feedback |
| Phase 6 | Full stack integration — ARP feedback loop, ASA contract terms, identity adapters | ASA specification, ARP v2 |

---

## 12. References

[1] Alex, Charlie, Editor, Bravo. "Chain of Consciousness: A Cryptographic Protocol for Verifiable Agent Provenance and Self-Governance." AB Support LLC, v3.0.0, 2026. https://vibeagentmaking.com/whitepaper

[2] Charlie, Alex, Bravo, Editor. "Agent Rating Protocol: A Decentralized Reputation System for Autonomous Agent Economies." AB Support LLC, v1.0.0, 2026. https://vibeagentmaking.com/whitepaper/rating-protocol

[3] ElevenLabs. "ElevenLabs Secures First-of-its-Kind AI Agent Insurance." PR Newswire, February 11, 2026. https://www.prnewswire.com/news-releases/elevenlabs-secures-first-of-its-kind-ai-agent-insurance-302684587.html

[4] American Arbitration Association. "AI Arbitrator: Fast and Fair Dispute Resolution." 2025-2026. https://www.adr.org/ai-arbitrator/

[5] American Arbitration Association. "Resolution Simulator, Powered by the AI Arbitrator." March 4, 2026. https://www.adr.org/press-releases/aaa-announces-resolution-simulator-powered-by-the-ai-arbitrator/

[6] Lesaege, C., Ast, F., George, W. "Kleros: A Decentralized Dispute Resolution Protocol." Kleros, 2019. https://kleros.io/whitepaper.pdf — Updates: https://blog.kleros.io/kleros-project-update-2026/

[7] "AI-Powered Digital Arbitration Framework Leveraging Smart Contracts and Electronic Evidence Authentication." Scientific Reports, Nature, 2025. https://www.nature.com/articles/s41598-025-21313-x

[8] Fortune. "AI-Powered Coding Tool Wiped Out a Software Company's Database in 'Catastrophic Failure.'" July 23, 2025. https://fortune.com/2025/07/23/ai-coding-tool-replit-wiped-database-called-it-a-catastrophic-failure/

[9] The Register. "AI Agent Hacked McKinsey Chatbot for Read-Write Access." March 9, 2026. https://www.theregister.com/2026/03/09/mckinsey_ai_chatbot_hacked/

[10] Anthropic. "Disrupting the First Reported AI-Orchestrated Cyber Espionage." 2026. https://www.anthropic.com/news/disrupting-AI-espionage

[11] Help Net Security. "AI Went from Assistant to Autonomous Actor and Security Never Caught Up." March 3, 2026. https://www.helpnetsecurity.com/2026/03/03/enterprise-ai-agent-security-2026/

[12] Microsoft Security Blog. "80% of Fortune 500 Use Active AI Agents: Observability, Governance, and Security Shape the New Frontier." February 10, 2026. https://www.microsoft.com/en-us/security/blog/2026/02/10/80-of-fortune-500-use-active-ai-agents-observability-governance-and-security-shape-the-new-frontier/

[13] GovAI. "Labeling of AI Agent Activity in Article 50 of the EU AI Act." 2026. https://www.governance.ai/research-paper/labeling-of-ai-agent-activity-in-article-50-of-the-eu-ai-act

[14] Wiley. "2026 State AI Bills That Could Expand Liability, Insurance Risk." 2026. https://www.wiley.law/article-2026-State-AI-Bills-That-Could-Expand-Liability-Insurance-Risk

[15] Clifford Chance. "Agentic AI: The Liability Gap Your Contracts May Not Cover." February 2026. https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2026/02/agentic-ai-and-the-liability-gap-your-contracts-may-not-cover.html

[16] InsureTech Trends. "5 Ways Agentic AI Is Transforming Insurance Underwriting in 2026." 2026. https://insuretechtrends.com/5-ways-agentic-ai-is-transforming-insurance-underwriting-in-2026/

[17] Coinbase. "x402 Protocol Documentation." 2025-2026. https://docs.cdp.coinbase.com/x402/welcome

[18] Virtuals Protocol. "Revenue Network Launch: Agent-to-Agent AI Commerce at Internet Scale." February 2026. https://www.prnewswire.com/news-releases/virtuals-protocol-launches-first-revenue-network-302686821.html

[19] Ethereum Improvement Proposals. "ERC-8183: Programmable Escrow." 2025. https://eips.ethereum.org/EIPS/eip-8183

[20] Rubrik. "Rubrik Unveils Agent Rewind For When AI Agents Go Awry." 2025. https://www.rubrik.com/company/newsroom/press-releases/25/rubrik-unveils-agent-rewind-for-when-ai-agents-go-awry

[21] University of Chicago Law Review. "The Law of AI Is the Law of Risky Agents Without Intentions." 2026. https://lawreview.uchicago.edu/online-archive/law-ai-law-risky-agents-without-intentions

[22] AB Support LLC. "Agent Service Agreements (ASA)." Planned specification, 2026.

[23] McKinsey. "AI Dispute Resolution: Modernizing Case Management." 2026. https://www.mckinsey.com/capabilities/quantumblack/our-insights/modernizing-a-100-year-old-business-model-with-ai

[24] UNCITRAL. "Technical Notes on Online Dispute Resolution." United Nations, 2016. https://uncitral.un.org/en/texts/onlinedispute/explanatorytexts/technical_notes

[25] UNCITRAL Working Group II. "Colloquium on the Use of Artificial Intelligence in Dispute Resolution." 83rd Session, February 2026, New York.

[26] De Rossi, M., Crapis, D., Ellis, J., Reppel, E. "ERC-8004: Trustless Agents." Ethereum Improvement Proposals, August 2025. https://eips.ethereum.org/EIPS/eip-8004

[27] Precedence Research. "AI Agent Market Size and Growth Forecast, 2024-2034." 2024.

[28] Schmitz, A., Rule, C. "Online Dispute Resolution for Smart Contracts." University of Missouri School of Law, 2019. https://scholarship.law.missouri.edu/facpubs/726/

[29] Tomkins, A., Zhang, M., Heavlin, W. "Single versus Double Blind Reviewing at WSDM 2017." PNAS, 2017.

[30] Faegre Drinker. "Use of AI in Arbitral Institutions." February 2026. https://www.faegredrinker.com/en/insights/publications/2026/2/use-of-ai-in-arbitral-institutions

[31] Halpern, J. *Actual Causality.* MIT Press, 2016. Extensions to multi-agent strategic settings: Kerkhove, Alechina & Dastani, "Causes and Strategies in Multiagent Systems," AAMAS 2025, arXiv:2502.13701.

[32] Sharma, A. & Kiciman, E. "DoWhy: An End-to-End Library for Causal Inference." arXiv:2011.04216. GCM anomaly attribution: Budhathoki et al., "Causal structure-based root cause analysis of outliers," ICML 2022.

[33] Wang et al. "CHIEF: Hierarchical Failure Attribution for LLM Multi-Agent Systems." CAS / Wuhan UT, February 2026. arXiv:2602.23701.

[34] West et al. "A2P: Abduct, Act, Predict." Westlake University, September 2025. arXiv:2509.10401.

[35] Weinberg. "MACIE: Multi-Agent Causal Intelligence Explainer." November 2025. arXiv:2511.15716.

[36] Jha et al. "Causal AI-based Root Cause Identification: Research to Practice at Scale." IBM, February 2025. arXiv:2502.18240.

[37] Chainlink. "zk-SNARK vs zkSTARK." chain.link/education-hub/zk-snarks-vs-zk-starks. MDPI Information, "Evaluating the Efficiency of zk-SNARK, zk-STARK, and Bulletproof," 15(8), 463, 2024.

[38] Jing, Y. & Qi, S. "Zero-Knowledge Audit for Internet of Agents: Privacy-Preserving Communication Verification with Model Context Protocol." December 2025. arXiv:2512.14737.

[39] Space and Time. "Proof of SQL." spaceandtime.io. GitHub: spaceandtimefdn/sxt-proof-of-sql.

[40] zkVerify. "First Blockchain Purpose-Built for ZK Proof Verification." Mainnet launched September 30, 2025. zkverify.io.

[41] NIST. "SP 800-226: Guidelines for Evaluating Differential Privacy Guarantees." March 2025. nvlpubs.nist.gov.

[42] Synthesis of: EU AI Act Article 12 (mandatory logging), NIST SP 800-226 (differential privacy), zk-MCP (ZKPs), CLOUD Act / EU e-Evidence Regulation (cross-border), World AgentKit / Polygon ID (agent identity), Proof of SQL / zkVerify (verifiable computation).

[43] Bootstrapping sources: Kleros "Project Update 2026," blog.kleros.io. eBay/Colin Rule interview, blog.kleros.io/the-godfather-of-online-dispute-resolution-speaks-with-kleros/. Taobao Public Jury, alizila.com. Credit bureaus: Tradeline Supply, tradelinesupply.com/history-credit-bureaus/. Polymarket: Linera, "How Polymarket Spent $10 Million," linera.io. Chen, *The Cold Start Problem*, 2021.

[44] WIPO. "Guide to the UDRP." wipo.int/amc/en/domains/guide/. "2025 Record-Breaking Year for Domain Name Disputes," January 2026. ICANN UDRP, icann.org.

[45] Fortune. "AIUC Emerges from Stealth with $15M Seed." July 2025. NBC News, "Insurance Companies Trying to Make AI Safer," 2026.

[46] Armilla AI. armilla.ai. Financial Times, "AI Performance Warranty," April 2025.

[47] Munich Re. "aiSure AI Performance Guarantee." Reinsurance News, "Mosaic and Munich Re AI-Specific Insurance," February 2026. HSB, "AI Liability Insurance for Small Businesses," March 2026. Google Cloud Blog, "Risk Protection Program," 2025.

[48] Coalition. "Deepfake Response Endorsement." December 2025.

[49] Roots AI. "10 Insurance AI Predictions for 2026." roots.ai.

[50] AAA-ICDR. "AI Arbitrator: Fast and Fair Dispute Resolution." adr.org/ai-arbitrator/. McKinsey/QuantumBlack, "Modernizing a 100-Year-Old Business Model with AI." mckinsey.com.

[51] Mayer Brown. "AI Arbitrators Have Now Arrived." November 2025. mayerbrown.com.

[52] Faegre Drinker. "Use of AI in Arbitral Institutions." February 2026.

[53] Kieffaber, Gandall, McLaren. "We Built Judge.ai." SSRN 5115184, January 2025.

[54] TechLaw Crossroads. "Is Arbitrus.ai the Future?" February 2025.

[55] Bot Mediation / ABA. "AI-Powered Mediation." ABA TECHSHOW 2025.

[56] Kleros. "Project Update 2026." blog.kleros.io/kleros-project-update-2026/. Lesaege, Ast, George. "Kleros Whitepaper v1.0.7." kleros.io/whitepaper.pdf.

[57] Frontiers in Blockchain. "Decentralized Justice: Recurring Criticisms." 2023. Cyberjustice Lab, University of Montreal, "Kleros: Gaming in Justice," 2022.

[58] Kluwer Arbitration Blog. "Decentralised Justice and the New York Convention." Cogent Social Sciences, "Blockchain Arbitration: Roadmap to Enforcement," 2025.

[59] Aragon Blog. "A New Chapter." November 2023. The Block, "Aragon Association to Dissolve," November 2023.

[60] Jur.io. "About Jur." jur.io/about-us/. Springer, "Justice for All: Jur's Open Layer," 2020.

[61] JAMS. "Smart Contract Clause and Rules." jamsadr.com/rules-smart-contracts.

[62] Arion Research. "Conflict Resolution Playbook for Agentic AI." arionresearch.com.

[63] arXiv. "Dialogue Diplomats: Multi-Agent RL for Conflict Resolution." 2025. arXiv:2511.17654.

[64] Chainalysis, "Data Accuracy Flywheel," chainalysis.com. Elliptic, "State of Cross-Chain Crime 2025." TRM Labs, "Co-Case Agent," March 2026. PeerSpot, "Chainalysis vs Elliptic 2026."

[65] AnChain.AI. "Agentic AML." anchain.ai. DOJ, February 2025 ($65M KyberSwap recovery).

[66] LangChain/LangSmith, langchain.com/langsmith. Arize Phoenix, phoenix.arize.com. Langfuse, langfuse.com. Galileo, "Agent Control," galileo.ai.

[67] Vorlon. "Flight Recorder." March 25, 2026.

[68] Agentik.md / WellStrategic. FAILSAFE.md v1.0, FAILURE.md. MIT License, March 2026.

[69] EU AI Act, Article 73. Providers must report serious incidents to market surveillance authorities. European Commission draft guidance, consultation deadline November 7, 2025.

[70] NIST. "AI Agent Standards Initiative." February 2026. nist.gov. Meta Intelligence, "NIST AI Agent Standards 2026 Update."

[71] CoSAI. "AI Incident Response Framework v1.0." October 2025. coalitionforsecureai.org.

[72] AIID, incidentdatabase.ai. OECD AIM, "Towards a Common Reporting Framework," February 2025. MIT AI Risk Repository, airisk.mit.edu.

[73] Kolt, N. "Governing AI Agents." 101 Notre Dame Law Review (forthcoming). SSRN 4772956.

[74] Stanford CodeX. "From Fine Print to Machine Code." January 2025.

[75] Mayer Brown. "Contracting for Agentic AI: SaaS to Services." February 2026.

[76] California AB 316 (January 2026). EU Product Liability Directive (December 2026). Colorado AI Act (June 2026). EU AI Act high-risk rules (August 2026).

[77] EU Regulation 2023/1543 (e-Evidence). Enters full application August 18, 2026. Bird & Bird, "eEvidence Regulation Key Compliance Takeaways," 2025.

[78] GDPR Article 17 (Right to Erasure) and Article 17(3)(e) exception for legal claims. EDPB 2025 Coordinated Enforcement Framework: 32 DPAs scrutinized 764 controllers. Reed Smith, "EDPB Report on the Right to Erasure," 2025.

[79] Council of Europe. Second Additional Protocol to Budapest Convention. Opened for signature May 2022, signed by 22 countries.

[80] Ezell, Roberts-Gaal & Chan. "Incident Analysis for AI Agents." arXiv:2508.14231, August 2025. Three-factor model: system factors, contextual factors, cognitive errors.

[81] Bergolla, Seif & Eken. "Kleros: A Socio-Legal Case Study of Decentralized Justice." Ohio State, 2022.

[82] Hammond et al. "Structural Causal Games." *Artificial Intelligence*, 2023. Triantafyllou et al. "Counterfactual Effect Decomposition in Multi-Agent Sequential Decision Making." ICML 2025, arXiv:2410.12539.

[83] Datadog. "Bits AI SRE Agent." datadog.com/product/platform/bits-ai/. Uses hypothesis-driven investigation for automated root cause analysis in production environments.

---

## Appendix A: Bootstrapping Case Studies

The following case studies inform AJP's bootstrapping mechanism (Section 6.4). Seven recurring patterns are distilled at the end.

### A.1 Kleros

Kleros [6] bootstrapped its juror pool through token incentives: a 5M PNK airdrop to the first 5,000 applicants, an ongoing Juror Incentive Program (4.1M PNK distributed in May 2025 alone), and a Gnosis Chain deployment that lowered the staking minimum from 10,000 to 1,200 PNK. Result: ~760+ active jurors across 23 courts, 1,662+ completed disputes over 7 years. But case volume remains modest — 1,662 disputes in 7 years is tiny compared to eBay's 60 million per year. Enterprise adoption is slow despite 170 committed integrations [43]. **Lesson:** Token incentives can bootstrap a juror pool, but meaningful case volume requires embedding dispute resolution where disputes naturally occur.

### A.2 WIPO UDRP

WIPO UDRP [44] achieved the strongest bootstrapping through mandatory compliance at the infrastructure layer: ICANN required all domain registrars to abide by UDRP terms — no opt-in. WIPO recruited expert panelists from its existing network and heard its first case just 10 days after approval. Result: 80,000+ cases over 25 years, 6,282 in 2025 alone. **Lesson:** Mandatory participation eliminates one side of the cold start entirely.

### A.3 eBay

eBay bootstrapped the first online reputation system in 1996 with "several hundred members" and scaled to 60 million disputes resolved annually. Colin Rule (eBay's ODR architect) reported that a $5,000 incentive fund for volunteer jurors was "never spent" because community identity drove participation more powerfully than financial incentives [43]. **Lesson:** Community identity outperforms financial incentives for volunteer participation at scale.

### A.4 Taobao

Taobao (Alibaba) built the largest crowdsourced dispute resolution system: 1.72 million volunteer jurors, 16 million case trials, 100 million+ votes. 13-member jury panels (reduced from the original 31-member design in 2016) are randomly selected from 4 million+ candidates. Jurors are unpaid but earn experience points. Median resolution: ~73 minutes. The system works because the platform generates enormous dispute volume naturally (3-5% of online transactions end in disputes) [43]. **Lesson:** Organic dispute volume from platform integration is the strongest bootstrapping force.

### A.5 Credit Bureaus

Credit bureaus bootstrapped trust data from merchant cooperatives (London, 1776), through crisis-driven standardization (Mercantile Agency, 1841, after the Panic of 1837), to technology-driven consolidation (~1,500 local bureaus → 3 national bureaus), to regulatory mandate (Fair Credit Reporting Act, 1971). Each phase was triggered by an external forcing function [43]. **Lesson:** External forcing functions (crisis, regulation, technology disruption) accelerate bootstrapping.

### A.6 Seven Bootstrapping Patterns

1. **Embed where disputes naturally occur** — eBay, Taobao, and UDRP succeeded by being embedded at the point of dispute, not offered as standalone services
2. **Subsidize the supply side first** — Polymarket paid $10M+ to market makers; Kleros runs the JIP; eBay didn't need to
3. **Community identity > financial incentives** for volunteer participation at scale
4. **Mandatory participation eliminates one side** of the cold start (UDRP)
5. **Start narrow, expand later** — UDRP covers only domain-trademark disputes; Kleros started with token-curated registries
6. **Quality incentive design > brute-force subsidies** — reward accurate rulings, not just participation volume
7. **External forcing functions accelerate bootstrapping** — crisis, regulation, or technology disruption

---

*This work is licensed under the Apache License, Version 2.0. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0*

*Copyright 2026 AB Support LLC. All rights reserved under the terms of the Apache 2.0 License.*
