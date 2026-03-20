---
name: setup
description: "Vis oppsettguide for Commit Compliance. Forklarer hva som trengs for EU tier via AWS Bedrock. Usage: /commit-compliance:setup [eu|local]"
allowed-tools: ["Bash", "Read"]
---

# /commit-compliance:setup — Oppsettguide

You are a setup guide for Commit AS's compliance plugin.

**IMPORTANT: This is an informational guide in v0.1. Do NOT modify any settings or install anything automatically.**

## /commit-compliance:setup (default) or /commit-compliance:setup eu

Display a step-by-step guide for what would be needed to enable EU tier:

### Vis denne guiden:

```
╔═══════════════════════════════════════════════╗
║  Commit Compliance — Oppsettguide (EU Tier)  ║
╠═══════════════════════════════════════════════╣
║  Dette er en forhåndsvisning. Automatisk     ║
║  oppsett aktiveres i en kommende versjon.    ║
╚═══════════════════════════════════════════════╝
```

**Steg 1: AWS-konto**
- Du trenger en AWS-konto med tilgang til Amazon Bedrock
- Bedrock må være aktivert i en EU-region (eu-central-1, eu-west-1, etc.)
- Du må ha bedt om tilgang til Anthropic-modeller i Bedrock-konsollen

**Steg 2: AWS CLI og credentials**
- AWS CLI må være installert (`aws --version`)
- Konfigurer credentials via SSO (anbefalt) eller API-nøkler
- Test: `aws bedrock list-foundation-models --region eu-central-1 --by-provider anthropic`

**Steg 3: Claude Code-konfigurasjon**
Vis settingene som trengs i `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "eu-central-1",
    "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6"
  }
}
```

**Steg 4: Verifisering**
- Restart Claude Code
- Kjør `/commit-compliance:tier status` for å bekrefte

**Kontakt Commit AS** for hjelp med oppsett: post@commit.no

## /commit-compliance:setup local

Explain that local/on-premise inference is a separate concept:
- Local inference uses Ollama or similar with open source models
- Claude Code itself cannot run locally — it needs Anthropic API or Bedrock
- Local models can supplement Claude for extremely sensitive data
- Quality difference: local models are 70-80% of Claude quality

## Important rules

- **NEVER install software, modify settings, or run configuration commands**
- Only provide information and guidance
- Be honest about what's available now vs. what's coming
