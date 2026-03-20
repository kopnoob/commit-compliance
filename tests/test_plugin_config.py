#!/usr/bin/env python3
"""Test suite that validates the plugin configuration and structure."""

import json
import os
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginStructure(unittest.TestCase):
    """Verify the plugin directory structure is correct."""

    def test_plugin_json_exists(self):
        self.assertTrue((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").exists())

    def test_hooks_json_exists(self):
        self.assertTrue((PLUGIN_ROOT / "hooks" / "hooks.json").exists())

    def test_mcp_json_exists(self):
        self.assertTrue((PLUGIN_ROOT / ".mcp.json").exists())

    def test_pii_scanner_exists(self):
        self.assertTrue((PLUGIN_ROOT / "hooks" / "pii_scanner.py").exists())

    def test_tier_indicator_exists(self):
        self.assertTrue((PLUGIN_ROOT / "hooks" / "tier_indicator.py").exists())

    def test_commands_exist(self):
        commands_dir = PLUGIN_ROOT / "commands"
        self.assertTrue((commands_dir / "tier.md").exists())
        self.assertTrue((commands_dir / "setup.md").exists())
        self.assertTrue((commands_dir / "review.md").exists())
        self.assertTrue((commands_dir / "statusline.md").exists())

    def test_agents_exist(self):
        self.assertTrue((PLUGIN_ROOT / "agents" / "compliance-reviewer.md").exists())

    def test_skills_exist(self):
        self.assertTrue((PLUGIN_ROOT / "skills" / "data-classification.md").exists())


class TestPluginJson(unittest.TestCase):
    """Validate plugin.json contents."""

    def setUp(self):
        with open(PLUGIN_ROOT / ".claude-plugin" / "plugin.json") as f:
            self.config = json.load(f)

    def test_has_required_fields(self):
        for field in ("name", "version", "description"):
            self.assertIn(field, self.config, f"Missing required field: {field}")

    def test_name_is_correct(self):
        self.assertEqual(self.config["name"], "commit-compliance")

    def test_version_format(self):
        parts = self.config["version"].split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())

    def test_hooks_reference(self):
        self.assertIn("hooks", self.config)
        self.assertEqual(self.config["hooks"], "./hooks/hooks.json")

    def test_description_not_empty(self):
        self.assertGreater(len(self.config["description"]), 20)


class TestHooksJson(unittest.TestCase):
    """Validate hooks.json configuration."""

    def setUp(self):
        with open(PLUGIN_ROOT / "hooks" / "hooks.json") as f:
            self.config = json.load(f)

    def test_has_hooks_key(self):
        self.assertIn("hooks", self.config)

    def test_has_pre_tool_use(self):
        self.assertIn("PreToolUse", self.config["hooks"])

    def test_has_notification(self):
        self.assertIn("Notification", self.config["hooks"])

    def test_pre_tool_use_matcher(self):
        ptu = self.config["hooks"]["PreToolUse"][0]
        self.assertIn("matcher", ptu)
        # Should match Write, Edit, MultiEdit but NOT Read
        self.assertIn("Write", ptu["matcher"])
        self.assertIn("Edit", ptu["matcher"])
        self.assertNotIn("Read", ptu["matcher"])

    def test_pre_tool_use_command_uses_plugin_root(self):
        ptu = self.config["hooks"]["PreToolUse"][0]
        command = ptu["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        self.assertIn("pii_scanner.py", command)

    def test_notification_run_once(self):
        notif = self.config["hooks"]["Notification"][0]
        self.assertTrue(notif["hooks"][0].get("runOnce", False))

    def test_notification_command_uses_plugin_root(self):
        notif = self.config["hooks"]["Notification"][0]
        command = notif["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        self.assertIn("tier_indicator.py", command)

    def test_hooks_reference_existing_files(self):
        """Verify all referenced hook scripts actually exist."""
        for hook_type in self.config["hooks"].values():
            for entry in hook_type:
                for hook in entry.get("hooks", []):
                    command = hook.get("command", "")
                    # Extract the python script path after ${CLAUDE_PLUGIN_ROOT}
                    if "${CLAUDE_PLUGIN_ROOT}" in command:
                        relative = command.split("${CLAUDE_PLUGIN_ROOT}/")[1].strip('"')
                        self.assertTrue(
                            (PLUGIN_ROOT / relative).exists(),
                            f"Hook script not found: {relative}"
                        )


class TestMcpJson(unittest.TestCase):
    """Validate .mcp.json configuration."""

    def test_valid_json(self):
        with open(PLUGIN_ROOT / ".mcp.json") as f:
            config = json.load(f)
        self.assertIn("mcpServers", config)

    def test_no_mcp_servers(self):
        """v0.1 doesn't need MCP servers."""
        with open(PLUGIN_ROOT / ".mcp.json") as f:
            config = json.load(f)
        self.assertEqual(len(config["mcpServers"]), 0)


class TestCommandFiles(unittest.TestCase):
    """Validate command markdown files have correct frontmatter."""

    def _read_frontmatter(self, filepath):
        with open(filepath) as f:
            content = f.read()
        if not content.startswith("---"):
            return {}
        end = content.index("---", 3)
        import yaml
        return yaml.safe_load(content[3:end])

    def _read_frontmatter_manual(self, filepath):
        """Parse YAML frontmatter without PyYAML dependency."""
        with open(filepath) as f:
            content = f.read()
        if not content.startswith("---"):
            return {}
        end = content.index("---", 3)
        frontmatter = {}
        for line in content[3:end].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip('"')
        return frontmatter

    def test_tier_command_has_name(self):
        fm = self._read_frontmatter_manual(PLUGIN_ROOT / "commands" / "tier.md")
        self.assertEqual(fm.get("name"), "tier")

    def test_setup_command_has_name(self):
        fm = self._read_frontmatter_manual(PLUGIN_ROOT / "commands" / "setup.md")
        self.assertEqual(fm.get("name"), "setup")

    def test_review_command_has_name(self):
        fm = self._read_frontmatter_manual(PLUGIN_ROOT / "commands" / "review.md")
        self.assertEqual(fm.get("name"), "review")

    def test_statusline_command_has_name(self):
        fm = self._read_frontmatter_manual(PLUGIN_ROOT / "commands" / "statusline.md")
        self.assertEqual(fm.get("name"), "statusline")

    def test_statusline_command_has_write_permission(self):
        """Statusline command needs Write to update settings.json."""
        with open(PLUGIN_ROOT / "commands" / "statusline.md") as f:
            content = f.read()
        for line in content.split("\n"):
            if "allowed-tools" in line:
                self.assertIn("Write", line,
                    "Statusline command needs Write permission to update settings.json")
                break

    def test_statusline_command_reads_installed_plugins(self):
        """Statusline command should look up install path from installed_plugins.json."""
        with open(PLUGIN_ROOT / "commands" / "statusline.md") as f:
            content = f.read()
        self.assertIn("installed_plugins.json", content)

    def test_statusline_command_uses_absolute_path(self):
        """Statusline command should use absolute path, not CLAUDE_PLUGIN_ROOT."""
        with open(PLUGIN_ROOT / "commands" / "statusline.md") as f:
            content = f.read()
        self.assertIn("absolute path", content.lower())

    def test_tier_command_is_readonly(self):
        """Tier command in v0.1 should NOT have Write permission."""
        with open(PLUGIN_ROOT / "commands" / "tier.md") as f:
            content = f.read()
        # Extract allowed-tools line
        for line in content.split("\n"):
            if "allowed-tools" in line:
                self.assertNotIn("Write", line,
                    "Tier command should not have Write permission in v0.1 (dry-run mode)")
                break

    def test_tier_command_mentions_preview(self):
        """Tier command should mention it's a preview/dry-run."""
        with open(PLUGIN_ROOT / "commands" / "tier.md") as f:
            content = f.read()
        content_lower = content.lower()
        self.assertTrue(
            "preview" in content_lower or "forhåndsvisning" in content_lower or "dry" in content_lower,
            "Tier command should mention preview/dry-run mode"
        )

    def test_tier_command_never_modify(self):
        """Tier command instructions must say NEVER modify settings."""
        with open(PLUGIN_ROOT / "commands" / "tier.md") as f:
            content = f.read()
        self.assertIn("NEVER", content)
        self.assertIn("modify", content.lower())


class TestHookScriptsExecutable(unittest.TestCase):
    """Test that hook scripts are valid Python."""

    def test_pii_scanner_syntax(self):
        """Verify pii_scanner.py has no syntax errors."""
        import py_compile
        py_compile.compile(
            str(PLUGIN_ROOT / "hooks" / "pii_scanner.py"),
            doraise=True
        )

    def test_tier_indicator_syntax(self):
        """Verify tier_indicator.py has no syntax errors."""
        import py_compile
        py_compile.compile(
            str(PLUGIN_ROOT / "hooks" / "tier_indicator.py"),
            doraise=True
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
