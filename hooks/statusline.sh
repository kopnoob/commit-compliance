#!/bin/bash
# Commit Compliance — Status Line
#
# Outputs a colored tier indicator for the Claude Code status bar.
# Reads JSON from stdin (Claude Code statusLine protocol), outputs ANSI text.
#
# Tier detection:
#   1. COMMIT_COMPLIANCE_SIMULATE_TIER env var (for testing)
#   2. CLAUDE_CODE_USE_BEDROCK + AWS_REGION/ANTHROPIC_MODEL
#   3. Default: GLOBAL

# Consume stdin (required by statusLine protocol)
cat > /dev/null

# Determine tier
SIM="${COMMIT_COMPLIANCE_SIMULATE_TIER:-}"

if [ "$SIM" = "eu" ]; then
    TIER="EU"
    COLOR="\033[1;38;2;80;160;255m"
    ICON="🔵"
elif [ "$SIM" = "global" ]; then
    TIER="GLOBAL"
    COLOR="\033[1;38;2;230;80;80m"
    ICON="🔴"
elif [ "$CLAUDE_CODE_USE_BEDROCK" = "1" ]; then
    if echo "$ANTHROPIC_MODEL" | grep -q "^eu\." 2>/dev/null || echo "$AWS_REGION" | grep -q "^eu-" 2>/dev/null; then
        TIER="EU"
        COLOR="\033[1;38;2;80;160;255m"
        ICON="🔵"
    else
        TIER="BEDROCK"
        COLOR="\033[1;38;2;230;200;60m"
        ICON="🟡"
    fi
else
    TIER="GLOBAL"
    COLOR="\033[1;38;2;230;80;80m"
    ICON="🔴"
fi

RESET="\033[0m"
DIM="\033[38;2;90;105;130m"

printf "${ICON} ${COLOR}${TIER}${RESET} ${DIM}tier${RESET}\n"
