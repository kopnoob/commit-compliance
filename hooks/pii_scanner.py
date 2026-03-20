#!/usr/bin/env python3
"""
Commit Compliance — PII Scanner Hook v0.3

PreToolUse hook that scans content being written/edited by Claude Code
for Norwegian PII patterns. Warns the user if sensitive data is detected,
with stronger warnings when on the global tier.

Hook input: JSON via stdin from Claude Code hook system.
Hook output: warnings to stderr, always exits 0 (never blocks).
"""

import sys
import re
import json
import os
from pathlib import Path
from datetime import datetime, timezone

# ── Fødselsnummer Modulus 11 ─────────────────────────────────

FNR_WEIGHTS_K1 = [3, 7, 6, 1, 8, 9, 4, 5, 2]
FNR_WEIGHTS_K2 = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def validate_fnr_checksum(digits):
    """Validate Norwegian national ID number using Modulus 11 algorithm."""
    if len(digits) != 11 or not digits.isdigit():
        return False
    d = [int(c) for c in digits]
    r1 = sum(d[i] * FNR_WEIGHTS_K1[i] for i in range(9)) % 11
    k1 = 0 if r1 == 0 else 11 - r1
    if k1 == 10 or k1 != d[9]:
        return False
    r2 = sum(d[i] * FNR_WEIGHTS_K2[i] for i in range(10)) % 11
    k2 = 0 if r2 == 0 else 11 - r2
    if k2 == 10 or k2 != d[10]:
        return False
    return True


def validate_fnr_date(digits):
    """Validate date portion of fødselsnummer (supports D-nummer and H-nummer)."""
    if len(digits) < 6:
        return False
    day = int(digits[0:2])
    month = int(digits[2:4])
    # D-nummer: day + 40, H-nummer: month + 40
    real_day = day if day <= 31 else day - 40
    real_month = month if month <= 12 else month - 40
    return 1 <= real_day <= 31 and 1 <= real_month <= 12


def find_valid_fnr(text):
    """Find all valid Norwegian national ID numbers in text."""
    candidates = re.findall(r"\b(\d{6}\s?\d{5})\b", text)
    valid = []
    for c in candidates:
        digits = c.replace(" ", "")
        if len(digits) == 11 and validate_fnr_date(digits) and validate_fnr_checksum(digits):
            valid.append(c)
    return valid


# ── Pattern definitions ──────────────────────────────────────

PATTERNS = {
    "kontonummer": {
        "regex": r"\b(\d{4}\s?\d{2}\s?\d{5})\b",
        "description": "Norsk bankkontonummer",
        "severity": "HIGH"
    },
    "epost_personal": {
        "regex": r"\b[a-zA-ZæøåÆØÅ][a-zA-ZæøåÆØÅ.\-]+\.[a-zA-ZæøåÆØÅ]+@(?!example\.com|test\.com|localhost)[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",
        "description": "Personlig e-postadresse",
        "severity": "MEDIUM"
    },
    "telefon_no": {
        "regex": r"\b(?:\+47\s?)?[49]\d{2}\s?\d{2}\s?\d{3}\b",
        "description": "Norsk mobilnummer",
        "severity": "MEDIUM"
    },
    "helseopplysning": {
        "regex": r"\b(?:diagnose[rn]?|pasient\w*|epikrise[rn]?|henvisning\w*|resept\w*|medisin\w*|sykmelding\w*|helseopplysning\w*|journal\w*|legemiddel\w*)\b",
        "keywords": True,
        "description": "Mulig helseopplysning (nøkkelord)",
        "severity": "HIGH"
    }
}

# ── Core scanning ────────────────────────────────────────────


def get_current_tier():
    """Detect current data residency tier from environment."""
    sim = os.environ.get("COMMIT_COMPLIANCE_SIMULATE_TIER", "").lower()
    if sim in ("eu", "global", "bedrock-other"):
        return sim
    if os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1":
        region = os.environ.get("AWS_REGION", "")
        model = os.environ.get("ANTHROPIC_MODEL", "")
        if "eu." in model or region.startswith("eu-"):
            return "eu"
        return "bedrock-other"
    return "global"


def scan_text(text):
    """Scan text for Norwegian PII patterns. Returns list of findings."""
    findings = []

    # Fødselsnummer (validated with Modulus 11)
    valid_fnr = find_valid_fnr(text)
    if valid_fnr:
        findings.append({
            "type": "fodselsnummer",
            "description": "Norsk fødselsnummer (validert mod11)",
            "severity": "HIGH",
            "count": len(valid_fnr),
            "sample": valid_fnr[0][:6] + "..."
        })

    # Deduplicate: remove fnr matches from kontonummer candidates
    fnr_normalized = {re.sub(r"\s", "", f) for f in valid_fnr}

    for name, pattern in PATTERNS.items():
        if pattern.get("keywords"):
            matches = re.findall(pattern["regex"], text, re.IGNORECASE)
        else:
            matches = re.findall(pattern["regex"], text)

        if name == "kontonummer" and fnr_normalized:
            matches = [m for m in matches if re.sub(r"\s", "", m) not in fnr_normalized]

        if matches:
            findings.append({
                "type": name,
                "description": pattern["description"],
                "severity": pattern["severity"],
                "count": len(matches),
                "sample": matches[0][:20] + "..." if len(matches[0]) > 20 else matches[0]
            })

    return findings


# ── Audit logging ────────────────────────────────────────────


def log_finding(findings, tier, filepath="unknown"):
    """Append PII findings to the audit log."""
    log_dir = os.environ.get(
        "COMMIT_COMPLIANCE_LOG_DIR",
        str(Path.home() / ".claude" / "commit-compliance")
    )
    log_path = Path(log_dir) / "audit.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log_path, "a") as log:
        for f in findings:
            log.write(
                f'{timestamp} | PII_DETECTED | tier={tier} | '
                f'severity={f["severity"]} | type={f["type"]} | '
                f'file={filepath} | count={f["count"]}\n'
            )


# ── Warning output ───────────────────────────────────────────


def format_warning(findings, tier, filepath):
    """Format a human-readable warning message for detected PII."""
    lines = [
        "⚠️  COMMIT COMPLIANCE — PII DETECTED",
        f"   File: {filepath}",
        f"   Current tier: {tier.upper()}",
        "",
    ]
    for f in findings:
        icon = "🔴" if f["severity"] == "HIGH" else "🟡"
        lines.append(f'   {icon} {f["description"]}: {f["count"]} forekomst(er)')
    lines.append("")

    high = [f for f in findings if f["severity"] == "HIGH"]
    medium = [f for f in findings if f["severity"] == "MEDIUM"]

    if tier == "global" and high:
        lines.append("   🚨 Du er på GLOBAL tier — sensitiv data vil sendes utenfor EU!")
        lines.append("   Vurder: /commit:tier eu  for å bytte til EU-ruting")
    elif tier == "eu" and high:
        lines.append("   ℹ️  Data rutes via EU. Vurder om dette er tilstrekkelig for datatypen.")
    elif tier == "global" and medium:
        lines.append("   🟡 Medium-sensitivitet på GLOBAL tier. Vurder EU-tier for ekstra sikkerhet.")
    elif tier == "eu":
        lines.append("   ✅ Data rutes via EU. Medium-sensitivitet er akseptabelt.")

    return "\n".join(lines)


# ── Hook input parsing ───────────────────────────────────────


def extract_content_from_hook_input(raw_input):
    """Extract file path and text content from Claude Code hook input.

    Handles multiple input formats:
    - Claude Code hook JSON: {"hook_type": "PreToolUse", "tool_name": "Write", "tool_input": {...}}
    - Direct tool input JSON: {"file_path": "...", "content": "..."}
    - Plain text (fallback)
    """
    filepath = "unknown"
    text = ""

    try:
        data = json.loads(raw_input)
    except (json.JSONDecodeError, TypeError):
        return filepath, raw_input if isinstance(raw_input, str) else ""

    # Claude Code hook format: tool_input is nested
    tool_input = data.get("tool_input", data)

    filepath = tool_input.get("file_path", tool_input.get("path", "unknown"))

    # Extract text content from various tool input formats
    for key in ("content", "file_text", "new_string", "new_str", "old_string", "old_str"):
        if key in tool_input and tool_input[key]:
            text = tool_input[key]
            break

    return filepath, text


# ── Hook entry point ─────────────────────────────────────────


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)

        filepath, text = extract_content_from_hook_input(raw_input)

        if not text:
            sys.exit(0)

        findings = scan_text(text)
        if not findings:
            sys.exit(0)

        tier = get_current_tier()
        log_finding(findings, tier, filepath)
        print(format_warning(findings, tier, filepath), file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"commit-compliance scanner error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
