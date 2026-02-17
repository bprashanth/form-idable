#!/usr/bin/env bash
# Create a Cognito user with a permanent password (no temp password flow).
# Usage: ./add-user.sh <email> <password>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

EMAIL="${1:?Usage: $0 <email> <password>}"
PASS="${2:?Usage: $0 <email> <password>}"

echo "=== Creating user: ${EMAIL} ==="

aws cognito-idp admin-create-user \
  --user-pool-id "$COGNITO_POOL_ID" \
  --username "$EMAIL" \
  --temporary-password "$PASS" \
  --message-action SUPPRESS \
  --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
  --region "$AWS_REGION" \
  --output text >/dev/null

echo "  user created (temp password suppressed)"

aws cognito-idp admin-set-user-password \
  --user-pool-id "$COGNITO_POOL_ID" \
  --username "$EMAIL" \
  --password "$PASS" \
  --permanent \
  --region "$AWS_REGION"

echo "  permanent password set"
echo "=== Done — user can log in immediately ==="
