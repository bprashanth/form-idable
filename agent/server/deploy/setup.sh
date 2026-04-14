#!/usr/bin/env bash
# Idempotent one-time infra setup: ECR repo, IAM role, Lambda budget alert.
# Lambda function itself is created/updated by push.sh.
# Safe to re-run — all steps check before creating.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "=== Setting up ${APP_NAME} in ${AWS_REGION} (account ${AWS_ACCOUNT_ID}) ==="

# ── 1. ECR repository ──────────────────────────────────────────────────────────
echo "→ ECR: ${ECR_REPO}"
if aws ecr describe-repositories --repository-names "$ECR_REPO" \
    --region "$AWS_REGION" &>/dev/null; then
  echo "  already exists"
else
  aws ecr create-repository --repository-name "$ECR_REPO" \
    --region "$AWS_REGION" --output text >/dev/null
  echo "  created"
fi

# ── 2. IAM role ────────────────────────────────────────────────────────────────
echo "→ IAM role: ${LAMBDA_ROLE_NAME}"
if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" &>/dev/null; then
  echo "  already exists"
else
  aws iam create-role \
    --role-name "$LAMBDA_ROLE_NAME" \
    --assume-role-policy-document "file://${SCRIPT_DIR}/trust-policy.json" \
    --output text >/dev/null
  echo "  created — waiting 10s for IAM propagation"
  sleep 10
fi
aws iam put-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "${LAMBDA_ROLE_NAME}-policy" \
  --policy-document "file://${SCRIPT_DIR}/lambda-policy.json"
echo "  policy applied"

# ── 3. Lambda monthly budget alert (covers all Lambda in account) ──────────────
# Alert fires at 80% of BUDGET_LIMIT_USD via email to ALERT_EMAIL.
# Budget name is fixed so re-running updates the threshold rather than
# creating duplicates.
BUDGET_NAME="lambda-monthly"
ALERT_THRESHOLD=80   # percent of limit

echo "→ Budget alert: \$${BUDGET_LIMIT_USD}/month → ${ALERT_EMAIL}"
if aws budgets describe-budget \
    --account-id "$AWS_ACCOUNT_ID" \
    --budget-name "$BUDGET_NAME" &>/dev/null; then
  # Update threshold in case BUDGET_LIMIT_USD changed
  aws budgets update-budget \
    --account-id "$AWS_ACCOUNT_ID" \
    --new-budget "{
      \"BudgetName\": \"${BUDGET_NAME}\",
      \"BudgetLimit\": {\"Amount\": \"${BUDGET_LIMIT_USD}\", \"Unit\": \"USD\"},
      \"TimeUnit\": \"MONTHLY\",
      \"BudgetType\": \"COST\",
      \"CostFilters\": {\"Service\": [\"AWS Lambda\"]}
    }" 2>/dev/null || true
  echo "  already exists (limit updated if changed)"
else
  aws budgets create-budget \
    --account-id "$AWS_ACCOUNT_ID" \
    --budget "{
      \"BudgetName\": \"${BUDGET_NAME}\",
      \"BudgetLimit\": {\"Amount\": \"${BUDGET_LIMIT_USD}\", \"Unit\": \"USD\"},
      \"TimeUnit\": \"MONTHLY\",
      \"BudgetType\": \"COST\",
      \"CostFilters\": {\"Service\": [\"AWS Lambda\"]}
    }" \
    --notifications-with-subscribers "[{
      \"Notification\": {
        \"NotificationType\": \"ACTUAL\",
        \"ComparisonOperator\": \"GREATER_THAN\",
        \"Threshold\": ${ALERT_THRESHOLD},
        \"ThresholdType\": \"PERCENTAGE\"
      },
      \"Subscribers\": [{
        \"SubscriptionType\": \"EMAIL\",
        \"Address\": \"${ALERT_EMAIL}\"
      }]
    }]"
  echo "  created — alert fires at \$$(echo "scale=2; $BUDGET_LIMIT_USD * $ALERT_THRESHOLD / 100" | bc)/month"
fi

echo ""
echo "=== Setup complete ==="
echo "Run ./deploy/deploy.sh to build and deploy the Lambda function."
