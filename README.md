# commit-compliance

**Data residency and GDPR compliance toolkit for Claude Code.**

Built by [Commit AS](https://commit.no) for Norwegian and EU enterprises that need to control where their data is processed when using AI-assisted development.

## What it does

| Feature | Description |
|---------|-------------|
| **PII scanning** | A pre-tool hook scans file content for Norwegian PII (fødselsnummer, bank accounts, health keywords) and warns before sensitive data is written. |
| **Tier indicator** | Shows your current data residency tier (EU/Global) at session start. |
| **Tier switching** | `/commit:tier eu` previews what EU routing would look like. Full switching coming in v0.2. |
| **Data classification** | A skill that classifies data sensitivity and recommends the appropriate tier. |
| **Compliance review** | `/commit:review` scans your codebase for GDPR issues — hardcoded PII, insecure data flows, missing consent. |
| **Audit logging** | All PII detections are logged to `~/.claude/commit-compliance/audit.log`. |

## Installation

```bash
# In Claude Code:
/install-plugin github:commitas/commit-compliance
```

## Quick start

```bash
# Check current tier status
/commit:tier status

# Preview what EU tier switching would do
/commit:tier eu

# Run a compliance review of your project
/commit:review

# First-time setup guide
/commit:setup
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

## v0.1 limitations

- **Tier switching is preview-only.** `/commit:tier eu` shows what would happen, but doesn't change configuration. Full switching requires AWS Bedrock setup and will be enabled in v0.2.
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
