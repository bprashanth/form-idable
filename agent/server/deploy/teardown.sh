#!/usr/bin/env bash
# Tear down all AWS resources created by setup.sh + deploy.sh for this POC.
#
# Run this when graduating the functionality to good-shepherd or retiring the POC.
# Only touches resources named after APP_NAME in config.sh — nothing shared,
# no other POCs, no good-shepherd resources are affected.
#
# Deletes:
#   - Lambda function (also removes its Function URL + reserved concurrency)
#   - ECR repository named ${APP_NAME} and all images within it
#     (each POC has its own isolated repo — other repos are untouched)
#   - IAM role ${APP_NAME}-role and its inline policy
#   - CloudWatch log group /aws/lambda/${APP_NAME}
#
# Does NOT delete:
#   - The Lambda budget alert (account-level, shared — remove manually if desired)
#   - Any other POC's or good-shepherd's resources
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

DRY_RUN=false
for arg in "$@"; do
  [ "$arg" = "--dry-run" ] && DRY_RUN=true
done

if [ "$DRY_RUN" = true ]; then
  echo "=== DRY RUN — nothing will be deleted ==="
else
  echo "=== Teardown: ${APP_NAME} (${AWS_REGION}) ==="
fi
echo ""
echo "  Resources scoped to APP_NAME=\"${APP_NAME}\" in config.sh:"
echo ""

# ── helper: check existence and print / act ────────────────────────────────────
# Usage: handle <label> <exists:bool> <delete_cmd...>
handle() {
  local label="$1" exists="$2"
  shift 2
  if [ "$exists" = "true" ]; then
    if [ "$DRY_RUN" = true ]; then
      echo "  [would delete] ${label}"
    else
      echo "→ ${label}"
      "$@"
      echo "  deleted"
    fi
  else
    if [ "$DRY_RUN" = true ]; then
      echo "  [not found]    ${label}"
    else
      echo "→ ${label} — not found, skipping"
    fi
  fi
}

# ── 1. Lambda function ─────────────────────────────────────────────────────────
LAMBDA_EXISTS=false
aws lambda get-function --function-name "$LAMBDA_FUNCTION" \
  --region "$AWS_REGION" &>/dev/null && LAMBDA_EXISTS=true || true

delete_lambda() {
  aws lambda delete-function \
    --function-name "$LAMBDA_FUNCTION" \
    --region "$AWS_REGION"
}
handle "Lambda function: ${LAMBDA_FUNCTION}  (+ Function URL, reserved concurrency)" \
  "$LAMBDA_EXISTS" delete_lambda

# ── 2. ECR repository ──────────────────────────────────────────────────────────
ECR_EXISTS=false
aws ecr describe-repositories --repository-names "$ECR_REPO" \
  --region "$AWS_REGION" &>/dev/null && ECR_EXISTS=true || true

delete_ecr() {
  aws ecr delete-repository \
    --repository-name "$ECR_REPO" \
    --force \
    --region "$AWS_REGION" \
    --output text >/dev/null
}
handle "ECR repository: ${ECR_REPO}  (images for this POC only)" \
  "$ECR_EXISTS" delete_ecr

# ── 3. IAM role + inline policy ───────────────────────────────────────────────
IAM_EXISTS=false
aws iam get-role --role-name "$LAMBDA_ROLE_NAME" &>/dev/null && IAM_EXISTS=true || true

delete_iam() {
  aws iam delete-role-policy \
    --role-name "$LAMBDA_ROLE_NAME" \
    --policy-name "${LAMBDA_ROLE_NAME}-policy" 2>/dev/null || true
  aws iam delete-role --role-name "$LAMBDA_ROLE_NAME"
}
handle "IAM role: ${LAMBDA_ROLE_NAME}  (+ inline policy)" \
  "$IAM_EXISTS" delete_iam

# ── 4. CloudWatch log group ────────────────────────────────────────────────────
LOG_GROUP="/aws/lambda/${LAMBDA_FUNCTION}"
CW_EXISTS=false
FOUND=$(aws logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --region "$AWS_REGION" \
  --query "logGroups[?logGroupName=='${LOG_GROUP}'] | length(@)" \
  --output text 2>/dev/null || echo "0")
[ "$FOUND" = "1" ] && CW_EXISTS=true

delete_cw() {
  aws logs delete-log-group \
    --log-group-name "$LOG_GROUP" \
    --region "$AWS_REGION"
}
handle "CloudWatch log group: ${LOG_GROUP}" \
  "$CW_EXISTS" delete_cw

echo ""
echo "  Will NOT touch:"
echo "    Lambda budget alert (account-level — delete manually if desired)"
echo "    Any other Lambda, ECR repo, or IAM role"

if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=== Dry run complete — verify the list above matches only ${APP_NAME} assets ==="
  echo "Run without --dry-run to delete for real."
  exit 0
fi

echo ""
read -r -p "Proceed with deletion? [y/N] " confirm
[[ "$confirm" =~ ^[yY]$ ]] || { echo "Aborted."; exit 0; }
echo ""

# Re-run the deletions now that user confirmed
# (handle() already printed labels above; re-invoke delete functions directly)

if [ "$LAMBDA_EXISTS" = true ]; then
  echo "→ Deleting Lambda: ${LAMBDA_FUNCTION}"
  delete_lambda && echo "  done"
fi
if [ "$ECR_EXISTS" = true ]; then
  echo "→ Deleting ECR: ${ECR_REPO}"
  delete_ecr && echo "  done"
fi
if [ "$IAM_EXISTS" = true ]; then
  echo "→ Deleting IAM role: ${LAMBDA_ROLE_NAME}"
  delete_iam && echo "  done"
fi
if [ "$CW_EXISTS" = true ]; then
  echo "→ Deleting CloudWatch log group: ${LOG_GROUP}"
  delete_cw && echo "  done"
fi

rm -f "$SCRIPT_DIR/outputs.env"

echo ""
echo "=== Teardown complete ==="
echo "Note: Lambda budget alert (lambda-monthly) was not deleted."
echo "Remove it manually in AWS Console > Billing > Budgets if no longer needed."
