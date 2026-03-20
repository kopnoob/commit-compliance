#!/usr/bin/env python3
"""
Commit Compliance — Tier Indicator (Startup Hook)

Displays a clear tier indicator when Claude Code starts, so the user
always knows which data residency tier they're operating on.

Runs as a Notification hook with runOnce=true.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_tier_state_file():
    """Read tier preference from state file, if it exists."""
    state_path = Path.home() / ".claude" / "commit-compliance" / "tier"
    try:
        return state_path.read_text().strip().lower()
    except (OSError, IOError):
        return ""


def get_tier_info():
    """Detect current tier from environment."""
    sim = read_tier_state_file() or os.environ.get("COMMIT_COMPLIANCE_SIMULATE_TIER", "").lower()
    if sim == "eu":
        return {
            "tier": "EU",
            "color": "blue",
            "region": os.environ.get("AWS_REGION", "eu-central-1 (simulert)"),
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6 (simulert)"),
            "icon": "🔵",
            "residency": "EU kun (Frankfurt, Stockholm, Paris)",
            "warning": None,
        }
    elif sim == "global":
        return {
            "tier": "GLOBAL",
            "color": "red",
            "region": "Anthropic (US)",
            "model": os.environ.get("ANTHROPIC_MODEL", "standard"),
            "icon": "🔴",
            "residency": "Global — data kan prosesseres utenfor EU",
            "warning": "Ikke bruk for persondata eller sensitive opplysninger",
        }

    if os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1":
        region = os.environ.get("AWS_REGION", "unknown")
        model = os.environ.get("ANTHROPIC_MODEL", "")

        if "eu." in model or region.startswith("eu-"):
            return {
                "tier": "EU",
                "color": "blue",
                "region": region,
                "model": model.split(".")[-1] if "." in model else model,
                "icon": "🔵",
                "residency": "EU kun (Frankfurt, Stockholm, Paris)",
                "warning": None,
            }
        else:
            return {
                "tier": "BEDROCK",
                "color": "yellow",
                "region": region,
                "model": model.split(".")[-1] if "." in model else model,
                "icon": "🟡",
                "residency": f"AWS {region}",
                "warning": "Ikke EU-spesifikk — vurder eu.* inferensprofil",
            }
    else:
        return {
            "tier": "GLOBAL",
            "color": "red",
            "region": "Anthropic (US)",
            "model": os.environ.get("ANTHROPIC_MODEL", "standard"),
            "icon": "🔴",
            "residency": "Global — data kan prosesseres utenfor EU",
            "warning": "Ikke bruk for persondata eller sensitive opplysninger",
        }


def render_box(info):
    """Render a terminal box with tier information."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    if info["color"] == "blue":
        CLR = "\033[38;5;75m"
        BRD = "\033[38;5;24m"
    elif info["color"] == "red":
        CLR = "\033[38;5;203m"
        BRD = "\033[38;5;88m"
    else:
        CLR = "\033[38;5;220m"
        BRD = "\033[38;5;136m"

    W = 52

    def line(left, fill, right):
        return f"{BRD}{left}{fill * W}{right}{RESET}"

    def padded(text, raw_len=None):
        if raw_len is None:
            raw_len = len(text)
        padding = W - raw_len
        return f"{BRD}│{RESET} {text}{' ' * max(0, padding - 1)}{BRD}│{RESET}"

    lines = []
    lines.append("")
    lines.append(line("╭", "─", "╮"))

    tier_text = f"{info['icon']}  {BOLD}{CLR}TIER: {info['tier']}{RESET}"
    tier_raw = f"X  TIER: {info['tier']}"
    lines.append(padded(tier_text, len(tier_raw)))

    lines.append(padded(""))

    region_text = f"{DIM}Region:{RESET}      {info['region']}"
    region_raw = f"Region:      {info['region']}"
    lines.append(padded(region_text, len(region_raw)))

    residency_text = f"{DIM}Residency:{RESET}   {info['residency'][:36]}"
    residency_raw = f"Residency:   {info['residency'][:36]}"
    lines.append(padded(residency_text, len(residency_raw)))

    model_short = info["model"][:30]
    model_text = f"{DIM}Modell:{RESET}      {model_short}"
    model_raw = f"Modell:      {model_short}"
    lines.append(padded(model_text, len(model_raw)))

    pii_text = f"{DIM}PII-skanner:{RESET}  Aktiv"
    pii_raw = "PII-skanner:  Aktiv"
    lines.append(padded(pii_text, len(pii_raw)))

    if info["warning"]:
        lines.append(padded(""))
        lines.append(line("├", "─", "┤"))
        warn_text = f"{CLR}⚠  {info['warning'][:46]}{RESET}"
        warn_raw = f"X  {info['warning'][:46]}"
        lines.append(padded(warn_text, len(warn_raw)))

    lines.append(line("╰", "─", "╯"))
    lines.append("")

    return "\n".join(lines)


def main():
    try:
        # Consume stdin (hook system may send input)
        try:
            sys.stdin.read()
        except Exception:
            pass

        info = get_tier_info()
        box = render_box(info)
        print(box, file=sys.stderr)
    except Exception as e:
        print(f"commit-compliance tier indicator error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
