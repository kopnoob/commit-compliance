#!/usr/bin/env python3
"""Test suite for commit-compliance PII scanner v0.3."""

import sys
import os
import json
import re
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
import pii_scanner

# Valid test fødselsnummer (generated with Modulus 11)
VALID_FNR = ["01019000083", "15037800071", "28115500009", "01029000073", "30068800036"]
INVALID_FNR = ["12018945678", "12345678901", "99999999999"]


class TestModulus11Validation(unittest.TestCase):
    """Test the fødselsnummer Modulus 11 checksum."""

    def test_valid_fnr_passes(self):
        for fnr in VALID_FNR:
            self.assertTrue(pii_scanner.validate_fnr_checksum(fnr), f"{fnr} should be valid")

    def test_invalid_fnr_fails(self):
        for fnr in INVALID_FNR:
            self.assertFalse(pii_scanner.validate_fnr_checksum(fnr), f"{fnr} should be invalid")

    def test_all_zeros_valid_checksum_but_invalid_date(self):
        """00000000000 passes mod11 but has day=0/month=0, so find_valid_fnr rejects it."""
        self.assertTrue(pii_scanner.validate_fnr_checksum("00000000000"))
        self.assertFalse(pii_scanner.validate_fnr_date("00000000000"))
        self.assertEqual(len(pii_scanner.find_valid_fnr("00000000000")), 0)

    def test_too_short_fails(self):
        self.assertFalse(pii_scanner.validate_fnr_checksum("1234567890"))

    def test_too_long_fails(self):
        self.assertFalse(pii_scanner.validate_fnr_checksum("123456789012"))

    def test_non_digit_fails(self):
        self.assertFalse(pii_scanner.validate_fnr_checksum("0101900008a"))

    def test_date_validation_normal(self):
        self.assertTrue(pii_scanner.validate_fnr_date("010190"))
        self.assertTrue(pii_scanner.validate_fnr_date("311299"))
        self.assertTrue(pii_scanner.validate_fnr_date("150378"))

    def test_date_validation_invalid(self):
        self.assertFalse(pii_scanner.validate_fnr_date("000190"))
        self.assertFalse(pii_scanner.validate_fnr_date("010090"))
        self.assertFalse(pii_scanner.validate_fnr_date("321390"))

    def test_d_nummer_accepted(self):
        self.assertTrue(pii_scanner.validate_fnr_date("410190"))

    def test_find_valid_fnr_in_text(self):
        text = f"Kunden har fnr {VALID_FNR[0]} og bor i Oslo"
        result = pii_scanner.find_valid_fnr(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].replace(" ", ""), VALID_FNR[0])

    def test_find_ignores_invalid_fnr(self):
        text = "Referanse: 12345678901 er ikke et fnr"
        result = pii_scanner.find_valid_fnr(text)
        self.assertEqual(len(result), 0)

    def test_find_multiple_valid_fnr(self):
        text = f"A: {VALID_FNR[0]}, B: {VALID_FNR[1]}, C: {VALID_FNR[2]}"
        result = pii_scanner.find_valid_fnr(text)
        self.assertEqual(len(result), 3)

    def test_fnr_with_space(self):
        spaced = VALID_FNR[0][:6] + " " + VALID_FNR[0][6:]
        text = f"fnr: {spaced}"
        result = pii_scanner.find_valid_fnr(text)
        self.assertEqual(len(result), 1)


class TestScanText(unittest.TestCase):
    """Test the main scan_text function."""

    def test_detects_valid_fodselsnummer(self):
        text = f"Brukerens fnr er {VALID_FNR[0]}"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertIn("fodselsnummer", types)

    def test_ignores_invalid_fodselsnummer(self):
        text = "Referanse: 12018945678 er bare et tall"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertNotIn("fodselsnummer", types)

    def test_kontonummer_detected(self):
        text = "Betal til konto 1234 56 78901"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertIn("kontonummer", types)

    def test_kontonummer_dedup_against_fnr(self):
        text = f"Fnr: {VALID_FNR[0]}"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertIn("fodselsnummer", types)
        konto = [f for f in findings if f["type"] == "kontonummer"]
        for k in konto:
            self.assertEqual(k["count"], 0)

    def test_phone_detected(self):
        text = "Ring +47 912 34 567"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertIn("telefon_no", types)

    def test_email_detected(self):
        text = "Send til kari.nordmann@gmail.com"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertIn("epost_personal", types)

    def test_email_example_ignored(self):
        text = "test@example.com for testing"
        findings = pii_scanner.scan_text(text)
        types = [f["type"] for f in findings]
        self.assertNotIn("epost_personal", types)

    def test_health_keywords(self):
        for keyword in ["diagnose", "pasientjournal", "epikrise", "resept", "sykmelding", "medisinsk"]:
            findings = pii_scanner.scan_text(f"Dokument om {keyword}")
            types = [f["type"] for f in findings]
            self.assertIn("helseopplysning", types, f"Should detect '{keyword}'")

    def test_clean_code_no_high_findings(self):
        text = "def calc(x): return x * 2\ntotal = calc(42)\nprint(f'Result: {total}')"
        findings = pii_scanner.scan_text(text)
        high = [f for f in findings if f["severity"] == "HIGH"]
        self.assertEqual(len(high), 0)

    def test_empty_text(self):
        self.assertEqual(len(pii_scanner.scan_text("")), 0)

    def test_severity_classification(self):
        text = f"Fnr: {VALID_FNR[0]}, email: test.user@firma.no, tlf: +47 912 34 567, diagnose: ok"
        findings = pii_scanner.scan_text(text)
        for f in findings:
            if f["type"] in ("fodselsnummer", "kontonummer", "helseopplysning"):
                self.assertEqual(f["severity"], "HIGH", f"{f['type']} should be HIGH")
            elif f["type"] in ("epost_personal", "telefon_no"):
                self.assertEqual(f["severity"], "MEDIUM", f"{f['type']} should be MEDIUM")


class TestTierDetection(unittest.TestCase):

    def test_global_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "global")

    def test_eu_by_model(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1",
               "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")

    def test_eu_by_region(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")

    def test_bedrock_us(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1",
               "ANTHROPIC_MODEL": "us.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "bedrock-other")

    def test_simulate_eu(self):
        env = {"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")

    def test_simulate_global(self):
        env = {"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "global")

    def test_simulate_overrides_bedrock(self):
        env = {"COMMIT_COMPLIANCE_SIMULATE_TIER": "global",
               "CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(pii_scanner.get_current_tier(), "global")


class TestTierStateFile(unittest.TestCase):
    """Test that the state file takes priority over env vars."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.state_dir = Path(self.tmpdir) / ".claude" / "commit-compliance"
        self.state_dir.mkdir(parents=True)
        self.state_file = self.state_dir / "tier"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_state_file_eu(self):
        self.state_file.write_text("eu")
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir)):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")

    def test_state_file_global(self):
        self.state_file.write_text("global")
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir)):
            self.assertEqual(pii_scanner.get_current_tier(), "global")

    def test_state_file_overrides_env(self):
        self.state_file.write_text("eu")
        with patch.dict(os.environ, {"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir)):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")

    def test_missing_state_file_falls_back(self):
        with patch.dict(os.environ, {"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir) / "nonexistent"):
            self.assertEqual(pii_scanner.get_current_tier(), "eu")


class TestHookInputParsing(unittest.TestCase):
    """Test the hook input parsing for different Claude Code tool formats."""

    def test_write_tool_input(self):
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/test.csv",
                "content": f"navn,fnr\nOla,{VALID_FNR[0]}"
            }
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        self.assertEqual(filepath, "/tmp/test.csv")
        self.assertIn(VALID_FNR[0], text)

    def test_edit_tool_input(self):
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/tmp/test.py",
                "old_string": "placeholder",
                "new_string": f"fnr = '{VALID_FNR[0]}'"
            }
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        self.assertEqual(filepath, "/tmp/test.py")
        self.assertIn(VALID_FNR[0], text)

    def test_direct_tool_input(self):
        """Direct tool_input format (without hook wrapper)."""
        hook_input = json.dumps({
            "file_path": "/tmp/test.txt",
            "content": f"Patient fnr: {VALID_FNR[0]}"
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        self.assertEqual(filepath, "/tmp/test.txt")
        self.assertIn(VALID_FNR[0], text)

    def test_read_tool_no_content(self):
        """Read tool has no content in PreToolUse — should return empty text."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {
                "file_path": "/tmp/test.csv"
            }
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        self.assertEqual(filepath, "/tmp/test.csv")
        self.assertEqual(text, "")

    def test_plain_text_fallback(self):
        filepath, text = pii_scanner.extract_content_from_hook_input("just plain text")
        self.assertEqual(filepath, "unknown")
        self.assertEqual(text, "just plain text")

    def test_empty_input(self):
        filepath, text = pii_scanner.extract_content_from_hook_input("")
        self.assertEqual(filepath, "unknown")
        self.assertEqual(text, "")

    def test_none_input(self):
        filepath, text = pii_scanner.extract_content_from_hook_input(None)
        self.assertEqual(filepath, "unknown")
        self.assertEqual(text, "")

    def test_full_pipeline_write(self):
        """Test end-to-end: hook input -> scan -> findings."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/customers.csv",
                "content": f"navn,fnr,email\nOla Nordmann,{VALID_FNR[0]},ola.nordmann@gmail.com"
            }
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        findings = pii_scanner.scan_text(text)
        types = {f["type"] for f in findings}
        self.assertIn("fodselsnummer", types)
        self.assertIn("epost_personal", types)

    def test_full_pipeline_no_pii(self):
        """Clean code should produce no findings."""
        hook_input = json.dumps({
            "hook_type": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/app.py",
                "content": "def hello():\n    return 'Hello, world!'"
            }
        })
        filepath, text = pii_scanner.extract_content_from_hook_input(hook_input)
        findings = pii_scanner.scan_text(text)
        self.assertEqual(len(findings), 0)


class TestRealFiles(unittest.TestCase):
    MOCK_DIR = Path(__file__).parent / "mock-data"

    def _scan_file(self, filename):
        with open(self.MOCK_DIR / filename) as f:
            return pii_scanner.scan_text(f.read())

    def test_customers_csv(self):
        findings = self._scan_file("customers.csv")
        types = {f["type"] for f in findings}
        self.assertIn("fodselsnummer", types)
        self.assertIn("epost_personal", types)
        self.assertIn("telefon_no", types)
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertEqual(fnr[0]["count"], 5)

    def test_pasientjournal(self):
        findings = self._scan_file("pasientjournal.txt")
        types = {f["type"] for f in findings}
        self.assertIn("helseopplysning", types)
        self.assertIn("fodselsnummer", types)

    def test_adr_clean(self):
        findings = self._scan_file("adr-0042.md")
        high = [f for f in findings if f["severity"] == "HIGH"]
        self.assertEqual(len(high), 0)

    def test_tilbud_helse(self):
        findings = self._scan_file("tilbud_helse.txt")
        types = {f["type"] for f in findings}
        self.assertIn("helseopplysning", types)

    def test_source_code_with_pii(self):
        with open(Path(__file__).parent / "mock-project/src/user_service.py") as f:
            findings = pii_scanner.scan_text(f.read())
        types = {f["type"] for f in findings}
        self.assertIn("fodselsnummer", types)
        self.assertIn("epost_personal", types)

    def test_clean_source_code(self):
        with open(Path(__file__).parent / "mock-project/src/billing.py") as f:
            findings = pii_scanner.scan_text(f.read())
        high = [f for f in findings if f["severity"] == "HIGH"]
        self.assertEqual(len(high), 0)


class TestFalsePositiveReduction(unittest.TestCase):

    def test_random_11_digit_number(self):
        text = "Ordrenr: 98765432109"
        findings = pii_scanner.scan_text(text)
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertEqual(len(fnr), 0)

    def test_org_number_9_digits(self):
        text = "Org.nr. 987654321"
        findings = pii_scanner.scan_text(text)
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertEqual(len(fnr), 0)

    def test_uuid(self):
        text = "id: 550e8400-e29b-41d4-a716-446655440000"
        findings = pii_scanner.scan_text(text)
        high = [f for f in findings if f["severity"] == "HIGH"]
        self.assertEqual(len(high), 0)

    def test_ip_address(self):
        text = "Server: 192.168.1.100"
        findings = pii_scanner.scan_text(text)
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertEqual(len(fnr), 0)

    def test_phone_only_8_digits_not_fnr(self):
        text = "Tlf: 12345678"
        findings = pii_scanner.scan_text(text)
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertEqual(len(fnr), 0)

    def test_large_file_performance(self):
        large_text = "Ingen PII her.\n" * 10000
        large_text += f"Men her: {VALID_FNR[0]}\n"
        large_text += "Mer tekst.\n" * 5000
        start = time.time()
        findings = pii_scanner.scan_text(large_text)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Took {elapsed:.2f}s")
        fnr = [f for f in findings if f["type"] == "fodselsnummer"]
        self.assertGreater(len(fnr), 0)


class TestWarningFormatting(unittest.TestCase):

    def test_global_high_warning(self):
        findings = [{"type": "fodselsnummer", "description": "Fnr", "severity": "HIGH", "count": 1, "sample": "0101..."}]
        msg = pii_scanner.format_warning(findings, "global", "test.csv")
        self.assertIn("GLOBAL", msg)
        self.assertIn("🚨", msg)
        self.assertIn("/commit-compliance:tier eu", msg)

    def test_eu_high_info(self):
        findings = [{"type": "fodselsnummer", "description": "Fnr", "severity": "HIGH", "count": 1, "sample": "0101..."}]
        msg = pii_scanner.format_warning(findings, "eu", "test.csv")
        self.assertIn("EU", msg)
        self.assertIn("ℹ️", msg)
        self.assertNotIn("🚨", msg)

    def test_global_medium_note(self):
        findings = [{"type": "epost_personal", "description": "Email", "severity": "MEDIUM", "count": 1, "sample": "a@b.c"}]
        msg = pii_scanner.format_warning(findings, "global", "test.csv")
        self.assertIn("🟡", msg)
        self.assertNotIn("🚨", msg)

    def test_eu_medium_ok(self):
        findings = [{"type": "epost_personal", "description": "Email", "severity": "MEDIUM", "count": 1, "sample": "a@b.c"}]
        msg = pii_scanner.format_warning(findings, "eu", "test.csv")
        self.assertIn("✅", msg)

    def test_warning_includes_filepath(self):
        findings = [{"type": "fodselsnummer", "description": "Fnr", "severity": "HIGH", "count": 1, "sample": "0101..."}]
        msg = pii_scanner.format_warning(findings, "global", "/path/to/secret.csv")
        self.assertIn("/path/to/secret.csv", msg)


class TestAuditLogging(unittest.TestCase):

    def test_log_creates_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"COMMIT_COMPLIANCE_LOG_DIR": tmpdir}):
                findings = [{"type": "fodselsnummer", "description": "Fnr", "severity": "HIGH", "count": 1, "sample": "0101..."}]
                pii_scanner.log_finding(findings, "global", "test.csv")
                log_path = Path(tmpdir) / "audit.log"
                self.assertTrue(log_path.exists())
                content = log_path.read_text()
                self.assertIn("PII_DETECTED", content)
                self.assertIn("fodselsnummer", content)
                self.assertIn("global", content)

    def test_log_appends(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"COMMIT_COMPLIANCE_LOG_DIR": tmpdir}):
                findings = [{"type": "fodselsnummer", "description": "Fnr", "severity": "HIGH", "count": 1, "sample": "0101..."}]
                pii_scanner.log_finding(findings, "global", "file1.csv")
                pii_scanner.log_finding(findings, "eu", "file2.csv")
                log_path = Path(tmpdir) / "audit.log"
                lines = log_path.read_text().strip().split("\n")
                self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
