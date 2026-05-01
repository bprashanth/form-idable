#!/bin/bash
# Step 2: pass fuzz proposals + image to gemini for verification.
# Run from repo root.
set -e

AGENT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FUZZ_JSON="$AGENT_ROOT/test/fuzz_proposals.json"
IMAGE="$AGENT_ROOT/test/segmented_000.jpg"
PROMPT_TEMPLATE="$AGENT_ROOT/prompts/species_verify.md"
SCRIPT="$AGENT_ROOT/scripts/run_agent.sh"

if [ ! -f "$FUZZ_JSON" ]; then
  echo "Run Step 1 first: python3 agent/test/fuzz_match.py"
  exit 1
fi

# Build prompt = template + fuzz JSON
PROMPT_FILE="$(mktemp /tmp/verify_prompt_XXXX.md)"
cat "$PROMPT_TEMPLATE" > "$PROMPT_FILE"
cat "$FUZZ_JSON"       >> "$PROMPT_FILE"

echo "── Prompt sent to gemini ──────────────────────────────"
cat "$PROMPT_FILE"
echo ""
echo "── Gemini response ────────────────────────────────────"

"$SCRIPT" "$PROMPT_FILE" "$FUZZ_JSON" "$IMAGE"

rm -f "$PROMPT_FILE"
