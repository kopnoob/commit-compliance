---
name: review
description: "Run a GDPR compliance review of the current project. Scans for hardcoded PII, insecure data flows, and missing privacy controls. Usage: /commit:review [path]"
allowed-tools: ["Read", "Bash", "Grep", "Glob"]
---

# /commit:review — Project Compliance Review

Invoke the `compliance-reviewer` agent to scan the current project (or a specified path) for GDPR and data protection issues.

1. Determine the scan scope:
   - If a path argument is provided, scan that directory
   - Otherwise, scan the current working directory

2. Before starting, show:
   ```
   🔍 Commit Compliance Review
      Scope: [path]
      Tier:  [current tier from env vars]
      Starting scan...
   ```

3. Delegate to the `compliance-reviewer` agent with the determined scope

4. If critical findings are found and the user is on global tier, prominently suggest switching to EU tier.
