"""Tests for cli.py — command-line interface."""

import json
import os
import tempfile
import pytest
from agent_justice_protocol.cli import main
from agent_justice_protocol.schema import AgentReference, ForensicFinding
from agent_justice_protocol.store import JusticeStore


@pytest.fixture
def tmp_store_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "ajp")


class TestCLI:
    def test_no_command_shows_help(self, capsys):
        ret = main([])
        assert ret == 0

    def test_status_empty(self, tmp_store_dir, capsys):
        ret = main(["--store", tmp_store_dir, "status"])
        assert ret == 0
        output = capsys.readouterr().out
        assert "Investigations: 0" in output

    def test_status_json(self, tmp_store_dir, capsys):
        ret = main(["--store", tmp_store_dir, "status", "--json"])
        assert ret == 0
        data = json.loads(capsys.readouterr().out)
        assert data["investigations"]["count"] == 0

    def test_investigate_basic(self, tmp_store_dir, capsys):
        ret = main([
            "--store", tmp_store_dir,
            "investigate",
            "--reporter", "monitor-01",
            "--type", "service_failure",
            "--severity", "high",
            "--description", "Agent failed to respond",
            "--subject", "suspect-01",
        ])
        assert ret == 0
        output = capsys.readouterr().out
        assert "Investigation complete" in output

    def test_investigate_json(self, tmp_store_dir, capsys):
        ret = main([
            "--store", tmp_store_dir,
            "investigate",
            "--reporter", "monitor-01",
            "--type", "data_loss",
            "--description", "Data was deleted",
            "--json",
        ])
        assert ret == 0
        data = json.loads(capsys.readouterr().out)
        assert data["incident"]["incident_type"] == "data_loss"

    def test_file_dispute(self, tmp_store_dir, capsys):
        # First create a finding
        store = JusticeStore(tmp_store_dir)
        f = ForensicFinding(
            investigation_id="inv-001",
            incident_type="service_failure",
            severity="high",
            reported_by=AgentReference(agent_id="reporter"),
            description="Test",
        )
        f.compute_hash()
        store.append_finding(f)

        ret = main([
            "--store", tmp_store_dir,
            "file",
            "--claimant", "claimant-01",
            "--respondent", "respondent-01",
            "--finding", f.finding_id,
            "--harm-type", "financial",
            "--harm-description", "Lost revenue due to failure",
            "--amount", "5000",
        ])
        assert ret == 0
        output = capsys.readouterr().out
        assert "Dispute filed" in output

    def test_file_missing_finding(self, tmp_store_dir, capsys):
        ret = main([
            "--store", tmp_store_dir,
            "file",
            "--claimant", "c",
            "--respondent", "r",
            "--finding", "nonexistent",
            "--harm-type", "financial",
            "--harm-description", "x",
        ])
        assert ret == 1

    def test_query_agent(self, tmp_store_dir, capsys):
        ret = main([
            "--store", tmp_store_dir,
            "query",
            "agent-01",
        ])
        assert ret == 0
        output = capsys.readouterr().out
        assert "Risk Profile" in output

    def test_query_json(self, tmp_store_dir, capsys):
        ret = main([
            "--store", tmp_store_dir,
            "query",
            "agent-01",
            "--json",
        ])
        assert ret == 0
        data = json.loads(capsys.readouterr().out)
        assert "risk_score" in data

    def test_investigate_with_evidence_file(self, tmp_store_dir, capsys):
        # Create a temporary evidence file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({
                "evidence_type": "interaction_log",
                "provenance_tier": 2,
                "source": {
                    "agent_id": "witness-01",
                    "system": "custom",
                    "timestamp": "2026-03-20T10:00:00.000000Z",
                },
                "content": {"action": "request_timeout"},
            }, f)
            evidence_path = f.name

        try:
            ret = main([
                "--store", tmp_store_dir,
                "investigate",
                "--reporter", "monitor-01",
                "--type", "timeout",
                "--description", "Request timed out",
                "--evidence", evidence_path,
            ])
            assert ret == 0
            output = capsys.readouterr().out
            assert "Evidence items: 1" in output
        finally:
            os.unlink(evidence_path)
