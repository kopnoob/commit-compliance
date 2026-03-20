#!/usr/bin/env python3
"""Test suite for the statusline script."""

import os
import subprocess
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "hooks" / "statusline.sh")


def run_statusline(env_override=None):
    """Run the statusline script and return its stdout."""
    env = os.environ.copy()
    # Clear any existing tier-related vars
    for key in ("COMMIT_COMPLIANCE_SIMULATE_TIER", "CLAUDE_CODE_USE_BEDROCK",
                "AWS_REGION", "ANTHROPIC_MODEL"):
        env.pop(key, None)
    if env_override:
        env.update(env_override)

    result = subprocess.run(
        ["/bin/bash", SCRIPT],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
        timeout=5,
    )
    return result.stdout, result.returncode


def strip_ansi(text):
    """Remove ANSI escape codes for easier assertion."""
    import re
    return re.sub(r"\033\[[^m]*m", "", text)


class TestStatuslineOutput(unittest.TestCase):

    def test_default_is_global(self):
        stdout, code = run_statusline()
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("GLOBAL", clean)
        self.assertIn("tier", clean)

    def test_simulate_eu(self):
        stdout, code = run_statusline({"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"})
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("EU", clean)
        self.assertIn("tier", clean)

    def test_simulate_global(self):
        stdout, code = run_statusline({"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"})
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("GLOBAL", clean)

    def test_bedrock_eu_by_model(self):
        stdout, code = run_statusline({
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6",
            "AWS_REGION": "eu-central-1",
        })
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("EU", clean)

    def test_bedrock_eu_by_region(self):
        stdout, code = run_statusline({
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "AWS_REGION": "eu-west-1",
        })
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("EU", clean)

    def test_bedrock_non_eu(self):
        stdout, code = run_statusline({
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "AWS_REGION": "us-east-1",
            "ANTHROPIC_MODEL": "us.anthropic.claude-sonnet-4-6",
        })
        self.assertEqual(code, 0)
        clean = strip_ansi(stdout)
        self.assertIn("BEDROCK", clean)

    def test_output_is_single_line(self):
        stdout, _ = run_statusline()
        lines = stdout.strip().split("\n")
        self.assertEqual(len(lines), 1)

    def test_output_has_ansi_colors(self):
        stdout, _ = run_statusline()
        self.assertIn("\033[", stdout)

    def test_eu_has_blue_icon(self):
        stdout, _ = run_statusline({"COMMIT_COMPLIANCE_SIMULATE_TIER": "eu"})
        self.assertIn("🔵", stdout)

    def test_global_has_red_icon(self):
        stdout, _ = run_statusline({"COMMIT_COMPLIANCE_SIMULATE_TIER": "global"})
        self.assertIn("🔴", stdout)

    def test_bedrock_has_yellow_icon(self):
        stdout, _ = run_statusline({
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "AWS_REGION": "us-east-1",
        })
        self.assertIn("🟡", stdout)


class TestStatuslineScript(unittest.TestCase):

    def test_script_exists(self):
        self.assertTrue(Path(SCRIPT).exists())

    def test_script_is_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_script_has_shebang(self):
        with open(SCRIPT) as f:
            first_line = f.readline()
        self.assertTrue(first_line.startswith("#!/bin/bash"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
