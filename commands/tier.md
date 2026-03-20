---
name: tier
description: "Vis eller bytt tier for data residency. Usage: /commit-compliance:tier [eu|global|status]"
allowed-tools: ["Bash", "Read", "Write"]
---

# /commit-compliance:tier — Data Residency Tier

You are a compliance assistant for Commit AS's data residency plugin.

When the user runs `/commit-compliance:tier`, do the following based on the argument:

## /commit-compliance:tier status (default if no argument)

Show the current tier configuration without changing anything.

1. Check the tier state file at `~/.claude/commit-compliance/tier` (if it exists)
2. Check environment variables (`COMMIT_COMPLIANCE_SIMULATE_TIER`, `CLAUDE_CODE_USE_BEDROCK`, `AWS_REGION`, `ANTHROPIC_MODEL`)
3. Determine the active tier using the same priority as the hooks:
   - State file > SIMULATE env var > Bedrock env vars > default GLOBAL
4. Display a clear summary:

```
╔══════════════════════════════════════╗
║   Commit Compliance — Tier Status   ║
╠══════════════════════════════════════╣
║ Aktiv tier:      GLOBAL             ║
║ Kilde:           Standard           ║
║ Region:          Anthropic (US)     ║
║ Data residency:  Global             ║
║ PII-skanner:     Aktiv              ║
╚══════════════════════════════════════╝
```

The "Kilde" field shows where the tier was determined from:
- `~/.claude/commit-compliance/tier` — if the state file is present
- `COMMIT_COMPLIANCE_SIMULATE_TIER` — if the env var is set
- `Bedrock-konfigurasjon` — if CLAUDE_CODE_USE_BEDROCK=1
- `Standard` — if using the default (GLOBAL)

## /commit-compliance:tier eu

Switch to EU tier. This updates the tier state file so that the status line and all hooks immediately reflect the change.

1. Create the directory `~/.claude/commit-compliance/` if it doesn't exist (use `mkdir -p`).
2. Write `eu` to the file `~/.claude/commit-compliance/tier`.
3. Display:

```
╔══════════════════════════════════════════════╗
║  🔵 Tier byttet til EU                      ║
╠══════════════════════════════════════════════╣
║  Statuslinja og hooks bruker nå EU tier.    ║
╚══════════════════════════════════════════════╝
```

4. Explain:
   - ✅ Statuslinja viser nå 🔵 EU tier
   - ✅ PII-skanneren bruker EU-kontekst for advarsler
   - ⚠️ Merk: dette endrer **visning og advarsler**, ikke faktisk API-ruting
   - ⚠️ For faktisk EU-ruting via Bedrock kreves AWS-konto med Bedrock-tilgang
   - 🔧 Kontakt Commit AS for hjelp med full EU-oppsett: post@commit.no

## /commit-compliance:tier global

Switch to GLOBAL tier. This updates the tier state file.

1. Create the directory `~/.claude/commit-compliance/` if it doesn't exist (use `mkdir -p`).
2. Write `global` to the file `~/.claude/commit-compliance/tier`.
3. Display:

```
╔══════════════════════════════════════════════╗
║  🔴 Tier byttet til GLOBAL                  ║
╠══════════════════════════════════════════════╣
║  Statuslinja og hooks bruker nå GLOBAL tier.║
╚══════════════════════════════════════════════╝
```

4. Explain:
   - ✅ Statuslinja viser nå 🔴 GLOBAL tier
   - ⚠️ Data kan prosesseres utenfor EU
   - ⚠️ Ikke bruk for persondata eller sensitive opplysninger

## /commit-compliance:tier reset

Remove the tier state file so that tier detection falls back to environment variables.

1. Delete `~/.claude/commit-compliance/tier` if it exists.
2. Display:
```
✅ Tier-preferanse fjernet. Faller tilbake til miljøvariabler.
```

## Important rules

- **NEVER modify `~/.claude/settings.json` or environment variables** — only write to the state file `~/.claude/commit-compliance/tier`
- `/commit-compliance:tier` uten argument = vis status
- The state file only controls display/warnings, not actual API routing
- If the user asks about "tier 1" or "lokal", explain that local on-premise inference is a separate concept
