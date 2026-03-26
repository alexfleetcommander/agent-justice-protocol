"""Tests for remediation.py — remedy types and enforcement tracking."""

import pytest
from agent_justice_protocol.schema import ArbitrationDecision
from agent_justice_protocol.remediation import (
    RemediationOrder,
    RemediationTracker,
)


def _make_decision():
    return ArbitrationDecision(
        dispute_id="d-001",
        claim_id="c-001",
        resolution_tier="peer_arbitration",
        respondent_fault_pct=80,
        claimant_fault_pct=10,
        no_fault_pct=10,
        remediation_type="compensation",
        remediation_details="Pay $3000 for service failure",
        compensation_amount=3000.0,
        respondent_rep_adjustment=-5.0,
        dimensions_affected=["reliability"],
    )


class TestRemediationOrder:
    def test_create(self):
        order = RemediationOrder(
            decision_id="d-001",
            respondent_id="resp-01",
            remediation_type="compensation",
            details="Pay $1000",
            compensation_amount=1000.0,
        )
        assert order.order_id
        assert order.status == "pending"
        assert order.is_pending

    def test_lifecycle(self):
        order = RemediationOrder(
            decision_id="d-001",
            respondent_id="resp-01",
            remediation_type="behavioral_restriction",
            details="Limit API calls to 100/min",
        )
        assert order.is_pending
        order.mark_completed()
        assert order.status == "completed"
        assert not order.is_pending

    def test_roundtrip(self):
        order = RemediationOrder(
            decision_id="d-001",
            respondent_id="resp-01",
            remediation_type="reputation_adjustment",
            details="Reduce reliability score by 5",
            reputation_dimensions=["reliability"],
            reputation_adjustment=-5.0,
        )
        d = order.to_dict()
        o2 = RemediationOrder.from_dict(d)
        assert o2.remediation_type == "reputation_adjustment"
        assert o2.reputation_adjustment == -5.0

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="remediation_type"):
            RemediationOrder(
                decision_id="d",
                respondent_id="r",
                remediation_type="invalid",
                details="x",
            )


class TestRemediationTracker:
    def test_create_from_decision(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        order = tracker.create_from_decision(decision, "resp-01")
        assert order.compensation_amount == 3000.0
        assert order.remediation_type == "compensation"

    def test_get_orders(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        tracker.create_from_decision(decision, "resp-01")
        tracker.create_from_decision(decision, "resp-02")
        assert len(tracker.get_orders_for("resp-01")) == 1
        assert len(tracker.get_orders_for("resp-02")) == 1

    def test_complete_order(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        order = tracker.create_from_decision(decision, "resp-01")
        tracker.complete_order(order.order_id)
        assert len(tracker.get_pending_orders("resp-01")) == 0

    def test_compliance_rate(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        o1 = tracker.create_from_decision(decision, "resp-01")
        o2 = tracker.create_from_decision(decision, "resp-01")
        tracker.complete_order(o1.order_id)
        # 1 of 2 completed
        assert tracker.compliance_rate("resp-01") == 0.5

    def test_compliance_rate_no_orders(self):
        tracker = RemediationTracker()
        assert tracker.compliance_rate("nobody") == 1.0

    def test_total_compensation_owed(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        tracker.create_from_decision(decision, "resp-01")
        tracker.create_from_decision(decision, "resp-01")
        assert tracker.total_compensation_owed("resp-01") == 6000.0

    def test_export_import(self):
        tracker = RemediationTracker()
        decision = _make_decision()
        tracker.create_from_decision(decision, "resp-01")
        exported = tracker.export_orders()

        tracker2 = RemediationTracker()
        tracker2.load_orders(exported)
        assert len(tracker2.all_orders) == 1
