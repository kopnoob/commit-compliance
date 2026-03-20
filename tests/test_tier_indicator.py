#!/usr/bin/env python3
"""Test suite for the tier indicator startup hook."""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
import tier_indicator


class TestTierDetection(unittest.TestCase):

    def test_eu_via_bedrock(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1",
               "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")
            self.assertEqual(info["color"], "blue")
            self.assertIsNone(info["warning"])

    def test_global_default(self):
        with patch.dict(os.environ, {}, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "GLOBAL")
            self.assertEqual(info["color"], "red")
            self.assertIsNotNone(info["warning"])
            self.assertIn("persondata", info["warning"])

    def test_bedrock_non_eu(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1",
               "ANTHROPIC_MODEL": "us.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "BEDROCK")
            self.assertEqual(info["color"], "yellow")
            self.assertIsNotNone(info["warning"])

    def test_simulate_eu(self):
        env = {"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")
            self.assertIsNone(info["warning"])

    def test_simulate_global(self):
        env = {"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "GLOBAL")
            self.assertIsNotNone(info["warning"])

    def test_eu_by_region_prefix(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-west-1"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")


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
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")

    def test_state_file_global(self):
        self.state_file.write_text("global")
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir)):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "GLOBAL")

    def test_state_file_overrides_env(self):
        self.state_file.write_text("eu")
        with patch.dict(os.environ, {"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir)):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")

    def test_missing_state_file_falls_back_to_env(self):
        with patch.dict(os.environ, {"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"}, clear=True), \
             patch.object(Path, "home", return_value=Path(self.tmpdir) / "nonexistent"):
            info = tier_indicator.get_tier_info()
            self.assertEqual(info["tier"], "EU")


class TestRenderBox(unittest.TestCase):

    def test_eu_box_renders(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1",
               "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            box = tier_indicator.render_box(info)
            self.assertIn("EU", box)
            self.assertIn("╭", box)
            self.assertIn("╰", box)
            # No warning section
            self.assertNotIn("├", box)

    def test_global_box_has_warning(self):
        with patch.dict(os.environ, {}, clear=True):
            info = tier_indicator.get_tier_info()
            box = tier_indicator.render_box(info)
            self.assertIn("GLOBAL", box)
            self.assertIn("⚠", box)
            self.assertIn("├", box)

    def test_bedrock_box_has_warning(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1",
               "ANTHROPIC_MODEL": "us.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            box = tier_indicator.render_box(info)
            self.assertIn("BEDROCK", box)
            self.assertIn("⚠", box)

    def test_box_contains_region(self):
        env = {"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "eu-central-1",
               "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6"}
        with patch.dict(os.environ, env, clear=True):
            info = tier_indicator.get_tier_info()
            box = tier_indicator.render_box(info)
            self.assertIn("eu-central-1", box)

    def test_box_contains_pii_scanner_status(self):
        with patch.dict(os.environ, {}, clear=True):
            info = tier_indicator.get_tier_info()
            box = tier_indicator.render_box(info)
            self.assertIn("PII-skanner", box)
            self.assertIn("Aktiv", box)

    def test_box_does_not_crash_on_long_values(self):
        info = {
            "tier": "EU",
            "color": "blue",
            "region": "a" * 100,
            "model": "b" * 100,
            "icon": "🔵",
            "residency": "c" * 100,
            "warning": None,
        }
        box = tier_indicator.render_box(info)
        self.assertIn("╭", box)
        self.assertIn("╰", box)


if __name__ == "__main__":
    unittest.main(verbosity=2)
