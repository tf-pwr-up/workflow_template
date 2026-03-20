#!/usr/bin/env bash
# council-check.sh — Verify all council review prerequisites are in place.
#
# Checks: council-config.json, Python 3, Codex CLI, API keys (env + ~/.zprofile),
# and network connectivity to each API endpoint.
#
# Usage:
#   ./scripts/council-check.sh
#
# Exit codes:
#   0 — All checks passed
#   1 — One or more checks failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS=0
FAIL=0

pass() {
    printf "  ✓ %s\n" "$1"
    PASS=$((PASS + 1))
}

fail() {
    printf "  ✗ %s\n" "$1"
    if [[ -n "${2:-}" ]]; then
        printf "    → Fix: %s\n" "$2"
    fi
    FAIL=$((FAIL + 1))
}

warn() {
    printf "  ⚠ %s\n" "$1"
}

# Source API keys from ~/.zprofile if not already in environment.
source_key_from_profile() {
    local key_name="$1"
    if [[ -n "${!key_name:-}" ]]; then
        return 0
    fi
    if [[ -f "$HOME/.zprofile" ]]; then
        local val
        val=$(grep -E "^export ${key_name}=" "$HOME/.zprofile" 2>/dev/null \
              | head -1 \
              | sed -E "s/^export ${key_name}=[\"']?([^\"']+)[\"']?$/\1/")
        if [[ -n "$val" ]]; then
            export "${key_name}=${val}"
            return 0
        fi
    fi
    return 1
}

# Check network connectivity to a host (HTTPS).
check_endpoint() {
    local label="$1"
    local url="$2"
    if curl -sf --max-time 5 -o /dev/null "$url" 2>/dev/null; then
        pass "Network: can reach $label"
    else
        # Some API endpoints return 4xx without auth, which is fine — we just
        # need to confirm DNS + TLS works. Use --head and accept any HTTP code.
        local http_code
        http_code=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [[ "$http_code" != "000" ]]; then
            pass "Network: can reach $label (HTTP $http_code)"
        else
            fail "Network: cannot reach $label ($url)" \
                 "Check your internet connection or firewall/proxy settings."
        fi
    fi
}

# ---------------------------------------------------------------------------
# Script root — find project root (parent of scripts/)
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

printf "Council Review Prerequisites Check\n"
printf "===================================\n"
printf "Project root: %s\n\n" "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# 1. council-config.json
# ---------------------------------------------------------------------------

printf "Configuration\n"
printf "-------------\n"

if [[ -f "$PROJECT_ROOT/council-config.json" ]]; then
    # Validate it is parseable JSON
    if python3 -c "import json; json.load(open('$PROJECT_ROOT/council-config.json'))" 2>/dev/null; then
        member_count=$(python3 -c "
import json
with open('$PROJECT_ROOT/council-config.json') as f:
    c = json.load(f)
print(len(c.get('members', [])))
" 2>/dev/null || echo "?")
        pass "council-config.json exists and is valid JSON ($member_count members)"
    else
        fail "council-config.json exists but is not valid JSON" \
             "Fix the JSON syntax in $PROJECT_ROOT/council-config.json"
    fi
else
    fail "council-config.json not found" \
         "Create $PROJECT_ROOT/council-config.json with your council composition."
fi

printf "\n"

# ---------------------------------------------------------------------------
# 2. Python 3
# ---------------------------------------------------------------------------

printf "Runtime\n"
printf "-------\n"

if command -v python3 &>/dev/null; then
    py_version=$(python3 --version 2>&1)
    pass "Python 3 available ($py_version)"
else
    fail "Python 3 not found" \
         "Install Python 3: brew install python3 (macOS) or apt install python3 (Ubuntu)"
fi

# ---------------------------------------------------------------------------
# 3. Codex CLI
# ---------------------------------------------------------------------------

printf "\n"
printf "Codex CLI\n"
printf "---------\n"

if command -v codex &>/dev/null; then
    codex_version=$(codex --version 2>&1 || echo "unknown version")
    pass "codex CLI installed ($codex_version)"
else
    fail "codex CLI not found" \
         "Install Codex CLI: npm install -g @openai/codex"
fi

if [[ -d "$HOME/.codex" ]]; then
    pass "~/.codex/ directory exists (Codex configured)"
else
    warn "~/.codex/ directory not found — Codex may not be authenticated"
    printf "    → Fix: Run 'codex auth' to authenticate.\n"
fi

# ---------------------------------------------------------------------------
# 4-6. API Keys
# ---------------------------------------------------------------------------

printf "\n"
printf "API Keys\n"
printf "--------\n"

# Google API Key
if source_key_from_profile "GOOGLE_API_KEY"; then
    # Mask the key for display
    key_preview="${GOOGLE_API_KEY:0:8}..."
    pass "GOOGLE_API_KEY set ($key_preview)"
else
    fail "GOOGLE_API_KEY not set" \
         "Set via: export GOOGLE_API_KEY='your-key' in ~/.zprofile or environment"
fi

# Anthropic API Key
if source_key_from_profile "ANTHROPIC_API_KEY"; then
    key_preview="${ANTHROPIC_API_KEY:0:8}..."
    pass "ANTHROPIC_API_KEY set ($key_preview)"
else
    fail "ANTHROPIC_API_KEY not set" \
         "Set via: export ANTHROPIC_API_KEY='your-key' in ~/.zprofile or environment"
fi

# OpenAI API Key
if source_key_from_profile "OPENAI_API_KEY"; then
    key_preview="${OPENAI_API_KEY:0:8}..."
    pass "OPENAI_API_KEY set ($key_preview)"
else
    fail "OPENAI_API_KEY not set" \
         "Set via: export OPENAI_API_KEY='your-key' in ~/.zprofile or environment"
fi

# ---------------------------------------------------------------------------
# 7. Network connectivity
# ---------------------------------------------------------------------------

printf "\n"
printf "Network Connectivity\n"
printf "--------------------\n"

check_endpoint "Google Gemini API" \
    "https://generativelanguage.googleapis.com/"

check_endpoint "Anthropic Claude API" \
    "https://api.anthropic.com/"

check_endpoint "OpenAI API" \
    "https://api.openai.com/"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

printf "\n"
printf "===================================\n"
TOTAL=$((PASS + FAIL))
printf "Results: %d/%d passed" "$PASS" "$TOTAL"

if [[ "$FAIL" -gt 0 ]]; then
    printf " (%d failed)\n" "$FAIL"
    printf "\nSome prerequisites are not met. Fix the failures above before running council reviews.\n"
    exit 1
else
    printf "\n\nAll prerequisites met. Council reviews are ready to run.\n"
    exit 0
fi
