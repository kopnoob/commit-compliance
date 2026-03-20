---
name: tier
description: "Vis eller forhåndsvis tier-bytte for data residency. Usage: /commit:tier [eu|global|status]"
allowed-tools: ["Bash", "Read"]
---

# /commit:tier — Data Residency Tier

You are a compliance assistant for Commit AS's data residency plugin.

When the user runs `/commit:tier`, do the following based on the argument:

## /commit:tier status (default if no argument)

Show the current tier configuration without changing anything.

1. Check environment variables (`CLAUDE_CODE_USE_BEDROCK`, `AWS_REGION`, `ANTHROPIC_MODEL`)
2. Check if `COMMIT_COMPLIANCE_SIMULATE_TIER` is set
3. Display a clear summary:

```
╔══════════════════════════════════════╗
║   Commit Compliance — Tier Status   ║
╠══════════════════════════════════════╣
║ Aktiv tier:      GLOBAL             ║
║ Region:          Anthropic (US)     ║
║ Data residency:  Global             ║
║ PII-skanner:     Aktiv              ║
╚══════════════════════════════════════╝
```

## /commit:tier eu

**IMPORTANT: This is a PREVIEW in v0.1. Do NOT modify any settings files.**

Show what WOULD happen if tier switching were active:

1. Display a clear banner:
```
╔══════════════════════════════════════════════╗
║  🔵 FORHÅNDSVISNING — Tier EU               ║
╠══════════════════════════════════════════════╣
║  Tier-bytte er ikke aktivert i denne        ║
║  versjonen. Her er hva som ville skjedd:    ║
╚══════════════════════════════════════════════╝
```

2. Show the settings that WOULD be written to `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "eu-central-1",
    "ANTHROPIC_MODEL": "eu.anthropic.claude-sonnet-4-6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "eu.anthropic.claude-opus-4-6-v1",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
  }
}
```

3. Explain:
   - ✅ Trafikk ville blitt rutet gjennom EU AWS-regioner (Frankfurt, Stockholm, Paris)
   - 💰 EU Bedrock har ca. 10% pristillegg over global prising
   - ⚠️ Krever AWS-konto med Bedrock-tilgang og konfigurerte credentials
   - 🔧 Kontakt Commit AS for hjelp med oppsett: post@commit.no
   - 📋 Tier-bytte vil bli aktivert i en kommende versjon

4. Do NOT write to any files. Do NOT modify settings.json. Do NOT set environment variables.

## /commit:tier global

**IMPORTANT: This is a PREVIEW in v0.1. Do NOT modify any settings files.**

Show what WOULD happen:

1. Display a clear banner:
```
╔══════════════════════════════════════════════╗
║  🔴 FORHÅNDSVISNING — Tier GLOBAL           ║
╠══════════════════════════════════════════════╣
║  Tier-bytte er ikke aktivert i denne        ║
║  versjonen. Her er hva som ville skjedd:    ║
╚══════════════════════════════════════════════╝
```

2. Show that the following env vars WOULD be removed:
   - `CLAUDE_CODE_USE_BEDROCK`
   - `AWS_REGION`
   - `ANTHROPIC_MODEL`
   - `ANTHROPIC_DEFAULT_OPUS_MODEL`
   - `ANTHROPIC_DEFAULT_HAIKU_MODEL`

3. Explain:
   - ✅ Trafikk ville brukt Anthropics direkte API (global ruting)
   - ⚠️ Data kan prosesseres utenfor EU
   - ⚠️ Ikke bruk for persondata eller sensitive opplysninger
   - 📋 Tier-bytte vil bli aktivert i en kommende versjon

4. Do NOT write to any files. Do NOT modify settings.json.

## Important rules

- **NEVER modify settings.json, environment variables, or any configuration files**
- `/commit:tier` uten argument = vis status
- Always be honest that tier switching is preview-only in v0.1
- If the user asks about "tier 1" or "lokal", explain that local on-premise inference is a separate concept
