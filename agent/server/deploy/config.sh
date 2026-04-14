#!/usr/bin/env bash
# ── config.sh ──────────────────────────────────────────────────────────────────
# Agent server deploy config for form-idable.
# Edit ALERT_EMAIL below, then run:
#   ./deploy/setup.sh    (once)
#   ./deploy/deploy.sh   (on every change)
# ───────────────────────────────────────────────────────────────────────────────

APP_NAME="form-idable-agent"
AWS_REGION="ap-south-1"
ALERT_EMAIL="prashanth@tech4goodcommunity.com"        # <- set your email here
HEALTH_CHECK_PATH="/agent/health"
BUDGET_LIMIT_USD=10                  # all-Lambda account alert threshold
RESERVED_CONCURRENCY=10              # per-function hard cap (~$3/month max)
SERVER_PORT=8070
CORS_EXPOSE_HEADERS="X-Row-Count"    # Custom header returned from row count api
LAMBDA_MEMORY_MB=512
LAMBDA_TIMEOUT_S=60

# ── Derived — do not edit below this line ─────────────────────────────────────
export APP_NAME AWS_REGION SERVER_PORT CORS_EXPOSE_HEADERS
export LAMBDA_MEMORY_MB LAMBDA_TIMEOUT_S RESERVED_CONCURRENCY
export BUDGET_LIMIT_USD ALERT_EMAIL HEALTH_CHECK_PATH

export AWS_ACCOUNT_ID
AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"

export ECR_REPO="${APP_NAME}"
export ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
export LAMBDA_FUNCTION="${APP_NAME}"
export LAMBDA_ROLE_NAME="${APP_NAME}-role"
export IMAGE="${APP_NAME}:latest"
