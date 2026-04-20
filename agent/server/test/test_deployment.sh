#!/usr/bin/env bash
# End-to-end test of the deployed Lambda agent server.
# No auth — the agent Function URL is public (AuthType=NONE).
#
# Run from anywhere — all paths are relative to this script's location.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/../deploy" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "Loading config from: $DEPLOY_DIR/config.sh"
source "$DEPLOY_DIR/config.sh"

echo "Loading outputs from: $DEPLOY_DIR/outputs.env"
source "$DEPLOY_DIR/outputs.env"

SERVER_URL="${FUNCTION_URL}"

echo "  FUNCTION_URL=${FUNCTION_URL}"
echo ""

# Standard test xlsx — must be produced by the good-shepherd upload endpoint
# (contains the "(Good Shepherd) Row ID" column). Generate by uploading a form
# in the PWA, then the file lands at pwa/output.xlsx after download.
DATA_FILE="$REPO_ROOT/pwa/output.xlsx"

TYPE_MAP='{"S.No":{"type":"serial","matched_keyword":"s.no"},"SPP Name/Local Name":{"type":"species","matched_keyword":"spp"}}'

PASS=0
FAIL=0

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS  $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $label (expected $expected, got $actual)"
    FAIL=$((FAIL + 1))
  fi
}

# ── 1. Health ─────────────────────────────────────────────────────────────────
echo "=== 1. Health check ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}/agent/health")
check "GET /agent/health → 200" "200" "$STATUS"

# ── 2. Cheatsheet ─────────────────────────────────────────────────────────────
echo ""
echo "=== 2. Cheatsheet ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}/agent/cheatsheet")
check "GET /agent/cheatsheet → 200" "200" "$STATUS"

# ── 3. Species DB ─────────────────────────────────────────────────────────────
echo ""
echo "=== 3. Species DB ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}/agent/species-db")
check "GET /agent/species-db → 200" "200" "$STATUS"

# ── 4. Lookup species ─────────────────────────────────────────────────────────
echo ""
echo "=== 4. Lookup species ==="
echo "  POST ${SERVER_URL}/agent/lookup-species {query: kage}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${SERVER_URL}/agent/lookup-species" \
  -H "Content-Type: application/json" \
  -d '{"query":"kage"}')
check "POST /agent/lookup-species → 200" "200" "$STATUS"

RESULT=$(curl -s \
  -X POST "${SERVER_URL}/agent/lookup-species" \
  -H "Content-Type: application/json" \
  -d '{"query":"kage"}')
CORRECTED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('corrected','(none)'))" 2>/dev/null || echo "(parse error)")
echo "  corrected: $CORRECTED"

# ── 5. Empty query → 400 ──────────────────────────────────────────────────────
echo ""
echo "=== 5. Lookup species (validation) ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${SERVER_URL}/agent/lookup-species" \
  -H "Content-Type: application/json" \
  -d '{"query":""}')
check "POST /agent/lookup-species (empty query) → 400" "400" "$STATUS"

# ── 6–9: xlsx-dependent tests ─────────────────────────────────────────────────
echo ""
if [ ! -f "$DATA_FILE" ]; then
  echo "SKIP  xlsx tests — $DATA_FILE not found"
  echo "      Upload a form in the PWA to generate it, then re-run."
else
  # ── 6. Infer types ──────────────────────────────────────────────────────────
  echo "=== 6. Infer types ==="
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${SERVER_URL}/agent/infer-types" \
    -F "file=@${DATA_FILE}")
  check "POST /agent/infer-types → 200" "200" "$STATUS"

  RESULT=$(curl -s -X POST "${SERVER_URL}/agent/infer-types" \
    -F "file=@${DATA_FILE}")
  TYPES=$(echo "$RESULT" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(', '.join(f'{k}={v[\"type\"]}' for k,v in d['type_map'].items()))" \
    2>/dev/null || echo "(parse error)")
  echo "  detected: $TYPES"

  # ── 7. Check serial ─────────────────────────────────────────────────────────
  echo ""
  echo "=== 7. Check serial ==="
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${SERVER_URL}/agent/check-serial" \
    -F "file=@${DATA_FILE}" \
    -F "type_map=${TYPE_MAP}")
  check "POST /agent/check-serial → 200" "200" "$STATUS"

  ROW_COUNT=$(curl -s -D - -o /dev/null \
    -X POST "${SERVER_URL}/agent/check-serial" \
    -F "file=@${DATA_FILE}" \
    -F "type_map=${TYPE_MAP}" \
    | grep -i "^x-row-count:" | awk '{print $2}' | tr -d '\r')
  echo "  X-Row-Count: ${ROW_COUNT:-not returned}"

  # ── 8. Check species ────────────────────────────────────────────────────────
  echo ""
  echo "=== 8. Check species ==="
  SPECIES_RESP=$(curl -s -w "\n%{http_code}" \
    -X POST "${SERVER_URL}/agent/check-species" \
    -F "file=@${DATA_FILE}" \
    -F "type_map=${TYPE_MAP}")
  SPECIES_STATUS=$(echo "$SPECIES_RESP" | tail -1)
  SPECIES_BODY=$(echo "$SPECIES_RESP" | head -n -1)

  if [ "$SPECIES_STATUS" = "400" ] && echo "$SPECIES_BODY" | grep -q "Row ID"; then
    echo "  SKIP  POST /agent/check-species — xlsx lacks (Good Shepherd) Row ID column"
    echo "        Re-generate $DATA_FILE by uploading a form through the full PWA flow"
  else
    check "POST /agent/check-species → 200" "200" "$SPECIES_STATUS"
    COUNT=$(echo "$SPECIES_BODY" | python3 -c \
      "import sys,json; print(len(json.load(sys.stdin)['proposals']))" \
      2>/dev/null || echo "?")
    echo "  proposals returned: $COUNT"

    # ── 9. Apply species (round-trip) ─────────────────────────────────────────
    echo ""
    echo "=== 9. Apply species ==="
    CORRECTIONS=$(echo "$SPECIES_BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
proposals = d.get('proposals', [])
if proposals:
    p = proposals[0]
    if p.get('corrected') and p.get('system_serials'):
        out = [{'original': p['original'], 'corrected': p['corrected'], 'system_serials': p['system_serials'][:1]}]
        print(json.dumps(out))
    else:
        print('[]')
else:
    print('[]')
" 2>/dev/null || echo "[]")

    if [ "$CORRECTIONS" = "[]" ]; then
      echo "  SKIP  no correctable proposals"
    else
      STATUS=$(curl -s -o /tmp/agent_test_applied.xlsx -w "%{http_code}" \
        -X POST "${SERVER_URL}/agent/apply-species" \
        -F "file=@${DATA_FILE}" \
        -F "type_map=${TYPE_MAP}" \
        -F "corrections=${CORRECTIONS}")
      check "POST /agent/apply-species → 200" "200" "$STATUS"
      echo "  output written to /tmp/agent_test_applied.xlsx"
    fi
  fi
fi

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -eq 0 ] || exit 1
