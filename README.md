# commit-compliance

**Data residency and GDPR compliance toolkit for Claude Code.**

Built by [Commit AS](https://commit.no) for Norwegian and EU enterprises that need to control where their data is processed when using AI-assisted development.

## What it does

| Feature | Description |
|---------|-------------|
| **PII scanning** | A pre-tool hook scans file content for Norwegian PII (fødselsnummer, bank accounts, health keywords) and warns before sensitive data is written. |
| **Tier indicator** | Shows your current data residency tier (EU/Global) at session start. |
| **Status line** | Always-visible colored tier badge in the Claude Code status bar. |
| **Tier switching** | `/commit-compliance:tier eu` switches your tier preference. The status line and hooks update immediately. |
| **Data classification** | A skill that classifies data sensitivity and recommends the appropriate tier. |
| **Compliance review** | `/commit-compliance:review` scans your codebase for GDPR issues — hardcoded PII, insecure data flows, missing consent. |
| **Audit logging** | All PII detections are logged to `~/.claude/commit-compliance/audit.log`. |

## Installation

**Step 1 — Add the marketplace:**

```
/plugin marketplace add kopnoob/commit-compliance
```

**Step 2 — Install the plugin:**

```
/plugin install commit-compliance@commit-compliance
```

**Step 3 — Reload:**

```
/reload-plugins
```

This gives you PII scanning, tier indicator at startup, `/commit-compliance:tier`, `/commit-compliance:review`, and `/commit-compliance:setup`.

**Step 4 (optional) — Enable the status line:**

```
/commit-compliance:statusline on
```

This adds a permanent, color-coded tier badge to the Claude Code status bar. You can disable it anytime with `/commit-compliance:statusline off`.

> **Note:** Claude Code supports one status line at a time. If you already have one configured, the command will warn you before replacing it.

### Uninstall

```
/plugin uninstall commit-compliance@commit-compliance
```

## Quick start

```bash
# Check current tier status
/commit-compliance:tier status

# Switch to EU tier
/commit-compliance:tier eu

# Run a compliance review of your project
/commit-compliance:review

# Enable/disable the status line
/commit-compliance:statusline on
/commit-compliance:statusline off

# First-time setup guide
/commit-compliance:setup
```

## Tier overview

| Tier | Backend | Data residency | Cost |
|------|---------|----------------|------|
| **EU** | AWS Bedrock `eu.*` | EU only (Frankfurt, Stockholm, etc.) | ~10% premium |
| **Global** | Anthropic API | Global (US-based) | Standard pricing |
| **Local** *(optional)* | Ollama on-prem | Your network | GPU hardware |

## PII scanner

The PII scanner runs as a `PreToolUse` hook on Write/Edit operations. It detects:

- 🔴 **Fødselsnummer** — Norwegian national ID with Modulus 11 validation
- 🔴 **Bankkontonummer** — Norwegian bank account numbers
- 🔴 **Helseopplysninger** — Health-related keywords
- 🟡 **Personlige e-poster** — Personal email addresses
- 🟡 **Mobilnumre** — Norwegian phone numbers

The scanner **never blocks** your work — it only warns. On the global tier, warnings are more prominent.

## Status line

The optional status line shows your current tier with color coding:

- 🔵 **EU** — blue, data stays in EU
- 🔴 **GLOBAL** — red, data may leave EU
- 🟡 **BEDROCK** — yellow, Bedrock but not EU-specific

Enable with `/commit-compliance:statusline on`, disable with `/commit-compliance:statusline off`.

## v0.1 limitations

- **Tier switching updates display and warnings only.** `/commit-compliance:tier eu` changes the status line and PII scanner context, but does not configure actual API routing via Bedrock. Full Bedrock routing requires AWS account setup — see `/commit-compliance:setup`.
- **No MCP server.** The plugin uses hooks and commands, not an MCP integration.

## Requirements

- Claude Code with plugin support
- Python 3.9+ (for hook scripts)
- AWS account with Bedrock access (for EU tier, when enabled)

## Running tests

```bash
cd /path/to/commit-compliance
python3 -m unittest discover -s tests -v
```

## For Commit AS partners

This plugin is part of Commit's managed AI compliance offering. Contact us for:

- AWS Bedrock account setup and IAM configuration
- Databehandleravtale (DPA) and DPIA templates
- Custom PII patterns for your industry
- Onboarding and training for your development team

**Contact:** post@commit.no

## License

MIT — see [LICENSE](LICENSE) for details.
