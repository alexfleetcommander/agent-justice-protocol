"""Tests for privacy.py — anti-fishing enforcement."""

import pytest
from agent_justice_protocol.privacy import (
    PrivacyGuard,
    PER_INITIATOR_LIMIT,
    PER_RESPONDENT_LIMIT,
)


class TestPrivacyGuard:
    def test_no_restrictions_initially(self):
        guard = PrivacyGuard()
        result = guard.check_investigation("init-01", "resp-01")
        assert result["approved"]
        assert not result["requires_tier2_approval"]

    def test_rule5_per_initiator_limit(self):
        guard = PrivacyGuard()
        # File 2 investigations (at limit)
        guard.record_investigation("inv-1", "init-01", "resp-01",
                                   "2026-03-20T10:00:00.000000Z")
        guard.record_investigation("inv-2", "init-01", "resp-01",
                                   "2026-03-20T11:00:00.000000Z")
        # Third should be blocked
        result = guard.check_investigation(
            "init-01", "resp-01", "2026-03-20T12:00:00.000000Z",
        )
        assert result["requires_tier2_approval"]
        assert "Rule 5" in result["reason"]
        assert result["per_initiator_count"] == 2

    def test_rule5_different_respondent_ok(self):
        guard = PrivacyGuard()
        guard.record_investigation("inv-1", "init-01", "resp-01",
                                   "2026-03-20T10:00:00.000000Z")
        guard.record_investigation("inv-2", "init-01", "resp-01",
                                   "2026-03-20T11:00:00.000000Z")
        # Different respondent should be fine
        result = guard.check_investigation(
            "init-01", "resp-02", "2026-03-20T12:00:00.000000Z",
        )
        assert result["approved"]

    def test_rule5a_per_respondent_limit(self):
        guard = PrivacyGuard()
        # 5 different initiators targeting same respondent
        for i in range(5):
            guard.record_investigation(
                f"inv-{i}", f"init-{i:02d}", "resp-target",
                f"2026-03-20T{10+i}:00:00.000000Z",
            )
        # 6th investigation against same respondent
        result = guard.check_investigation(
            "init-99", "resp-target", "2026-03-20T16:00:00.000000Z",
        )
        assert result["requires_tier2_approval"]
        assert "Rule 5a" in result["reason"]
        assert result["per_respondent_count"] == 5

    def test_old_records_expire(self):
        guard = PrivacyGuard(window_days=90)
        # Record investigation 91 days ago
        guard.record_investigation(
            "inv-old", "init-01", "resp-01",
            "2026-01-01T10:00:00.000000Z",
        )
        guard.record_investigation(
            "inv-old2", "init-01", "resp-01",
            "2026-01-01T11:00:00.000000Z",
        )
        # Should not count against limit
        result = guard.check_investigation(
            "init-01", "resp-01", "2026-04-05T10:00:00.000000Z",
        )
        assert result["approved"]

    def test_export_import(self):
        guard = PrivacyGuard()
        guard.record_investigation("inv-1", "init-01", "resp-01",
                                   "2026-03-20T10:00:00.000000Z")
        exported = guard.export_records()
        assert len(exported) == 1

        guard2 = PrivacyGuard()
        guard2.load_records(exported)
        result = guard2.check_per_initiator(
            "init-01", "resp-01", "2026-03-20T12:00:00.000000Z",
        )
        assert result[1] == 1  # count
