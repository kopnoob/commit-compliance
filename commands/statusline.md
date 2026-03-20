---
name: statusline
description: "Enable or disable the tier status line in Claude Code. Usage: /commit-compliance:statusline [on|off]"
allowed-tools: ["Bash", "Read", "Write"]
---

# /commit-compliance:statusline — Tier Status Line

Manage the always-visible tier indicator in the Claude Code status bar.

## /commit-compliance:statusline or /commit-compliance:statusline on

Enable the tier status line.

### Steps:

1. Find the plugin install path by reading `~/.claude/plugins/installed_plugins.json`. Look for an entry where the key contains `commit-compliance`. Extract the `installPath` from the first entry in the array.

2. Verify the statusline script exists at `{installPath}/hooks/statusline.sh`. If not found, tell the user the plugin may not be installed correctly.

3. Read `~/.claude/settings.json`.

4. Check if there's already a `statusLine` configured:
   - If it already points to `statusline.sh` from this plugin: tell the user it's already enabled.
   - If it points to something else: **warn the user** that enabling this will replace their existing status line. Show what's currently configured. Ask for confirmation before proceeding. Do NOT proceed without explicit confirmation.
   - If no statusLine is configured: proceed directly.

5. Write the updated `~/.claude/settings.json` with the statusLine added (merge, don't overwrite other settings):

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash \"{installPath}/hooks/statusline.sh\""
  }
}
```

Use the **absolute path** from `installPath` — do not use `${CLAUDE_PLUGIN_ROOT}` or relative paths, since the statusLine runs outside the plugin context.

6. Confirm to the user:
```
✅ Tier-statuslinje aktivert!

   Statuslinja viser nå ditt aktive tier-nivå:
   🔵 EU    — blå, data forblir i EU
   🔴 GLOBAL — rød, data kan forlate EU
   🟡 BEDROCK — gul, Bedrock men ikke EU

   Endringen gjelder fra neste sesjon.
   For å deaktivere: /commit-compliance:statusline off
```

## /commit-compliance:statusline off

Disable the tier status line.

1. Read `~/.claude/settings.json`.
2. Check if the current statusLine points to this plugin's `statusline.sh`.
   - If yes: remove the `statusLine` key entirely from settings.
   - If no: tell the user the current status line isn't from this plugin and leave it untouched.
3. Write the updated settings.
4. Confirm:
```
✅ Tier-statuslinje deaktivert.
   Endringen gjelder fra neste sesjon.
```

## Important rules

- Always use the **absolute path** from `installed_plugins.json`, never hardcode paths
- Always **merge** with existing settings — never overwrite the entire file
- When replacing an existing statusLine, **always warn and ask for confirmation**
- If `installed_plugins.json` doesn't exist or doesn't contain commit-compliance, tell the user to install the plugin first
