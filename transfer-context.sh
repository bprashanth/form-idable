#!/usr/bin/env bash
# transfer-context.sh
#
# Rsync THIS repo (form-idable) and the sibling backend repo (good-shepherd) to
# another machine so an agent can take over there without re-cloning. Unlike a
# clone, this carries the gitignored out-of-band files the deploy flow needs
# (.env, deploy/test-credentials.env, deploy/outputs.env), so verify_prod and
# the backend can run on the remote immediately.
#
# What it does NOT copy: codex credentials. The remote is expected to run its
# own `codex login` (its ~/.codex/auth.json stays local to that machine). It
# also skips rebuildable/platform-specific dirs (node_modules, venvs, caches)
# so the remote rebuilds those itself.
#
# Paths are derived relative to this script, not hardcoded. Both repos must sit
# side by side under the same parent (…/bprashanth/form-idable and
# …/bprashanth/good-shepherd), which is the layout this script assumes and
# recreates on the remote.
#
# Usage:
#   ./transfer-context.sh USER@HOST [REMOTE_PATH]
#
#   USER@HOST     ssh target, e.g. ubuntu@10.0.0.5  (an ssh alias works too)
#   REMOTE_PATH   base dir on the remote; defaults to ~/src/github.com/bprashanth
#                 (same layout as this machine). ~ expands on the remote.
#
# Examples:
#   ./transfer-context.sh ubuntu@10.0.0.5
#   ./transfer-context.sh devbox '~/work/bprashanth'
set -euo pipefail

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; }

if [ $# -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 1
fi

REMOTE="$1"
REMOTE_PATH="${2:-~/src/github.com/bprashanth}"

# Resolve paths relative to this script so it works from any checkout location.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT="$(cd "$SCRIPT_DIR/.." && pwd)"   # …/github.com/bprashanth

REPOS=(form-idable good-shepherd)

for r in "${REPOS[@]}"; do
  if [ ! -d "$PARENT/$r" ]; then
    echo "ERROR: expected sibling repo not found: $PARENT/$r" >&2
    echo "       This script assumes form-idable and good-shepherd sit side by side." >&2
    exit 1
  fi
done

# .git IS transferred so the remote is a full working repo (history, branches,
# uncommitted changes). Excludes below are protected from --delete, so a
# re-sync never wipes the deps the remote rebuilt for itself.
EXCLUDES=(
  --exclude 'node_modules/'
  --exclude '.venv/'
  --exclude 'venv/'
  --exclude '__pycache__/'
  --exclude '*.pyc'
  --exclude 'dist/'
  --exclude 'build/'
  --exclude '.pytest_cache/'
  --exclude '.mypy_cache/'
  --exclude 'test-results/'
  --exclude '.DS_Store'
  # never transfer codex credentials — the remote uses its own `codex login`
  --exclude '.codex/'
  --exclude 'auth.json'
)

echo "Local parent : $PARENT"
echo "Remote target: $REMOTE:$REMOTE_PATH"
echo "Repos        : ${REPOS[*]}"
echo ""

ssh "$REMOTE" "mkdir -p $REMOTE_PATH"

for r in "${REPOS[@]}"; do
  echo "=== rsync $r  ->  $REMOTE:$REMOTE_PATH/$r ==="
  # trailing slashes: copy the CONTENTS of the source dir into the dest dir of
  # the same name (so form-idable/ lands as REMOTE_PATH/form-idable/).
  rsync -az --delete "${EXCLUDES[@]}" \
    "$PARENT/$r/" "$REMOTE:$REMOTE_PATH/$r/"
done

echo ""
echo "=== Done. On the remote (${REMOTE}): ==="
cat <<EOF
  1. Make sure codex is logged in:        codex login   (then codex --version)
  2. Backend deps (only if you deploy):   cd $REMOTE_PATH/good-shepherd/agents/formidable && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
  3. PWA deps (only if you run the UI):   cd $REMOTE_PATH/form-idable/pwa && npm install
  4. AWS creds must be configured on the remote (aws sts get-caller-identity).
  5. Read $REMOTE_PATH/form-idable/CLAUDE.md — "Taking over on another machine".
EOF
