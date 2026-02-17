#!/usr/bin/env bash
# One-time idempotent infra setup: ECR, IAM, API Gateway + JWT authorizer.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "=== Setting up infra in ${AWS_REGION} (account ${AWS_ACCOUNT_ID}) ==="

# ── 1. ECR repository ──────────────────────────────────────────
echo "→ ECR repository: ${ECR_REPO}"
if aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" &>/dev/null; then
  echo "  already exists"
else
  aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION" --output text
  echo "  created"
fi

# ── 2. IAM role ─────────────────────────────────────────────────
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
echo "→ IAM role: ${LAMBDA_ROLE_NAME}"
if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" &>/dev/null; then
  echo "  already exists"
else
  aws iam create-role \
    --role-name "$LAMBDA_ROLE_NAME" \
    --assume-role-policy-document "file://${SCRIPT_DIR}/trust-policy.json" \
    --output text
  echo "  created"
  echo "  waiting 10s for IAM propagation..."
  sleep 10
fi

echo "→ Inline policy: form-idable-lambda-policy"
aws iam put-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-name "form-idable-lambda-policy" \
  --policy-document "file://${SCRIPT_DIR}/lambda-policy.json"
echo "  applied"

ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query 'Role.Arn' --output text)

# ── 3. API Gateway HTTP API ─────────────────────────────────────
echo "→ API Gateway: ${APIGW_NAME}"
APIGW_ID=$(aws apigatewayv2 get-apis --region "$AWS_REGION" \
  --query "Items[?Name=='${APIGW_NAME}'].ApiId | [0]" --output text 2>/dev/null || echo "None")

if [ "$APIGW_ID" = "None" ] || [ -z "$APIGW_ID" ]; then
  APIGW_ID=$(aws apigatewayv2 create-api \
    --name "$APIGW_NAME" \
    --protocol-type HTTP \
    --cors-configuration "AllowOrigins=*,AllowMethods=GET,POST,OPTIONS,AllowHeaders=content-type,authorization,ExposeHeaders=X-Form-Summary,MaxAge=3600" \
    --region "$AWS_REGION" \
    --query 'ApiId' --output text)
  echo "  created: ${APIGW_ID}"
else
  echo "  already exists: ${APIGW_ID}"
fi

# ── 4. JWT authorizer ───────────────────────────────────────────
echo "→ JWT authorizer"
AUTH_ID=$(aws apigatewayv2 get-authorizers --api-id "$APIGW_ID" --region "$AWS_REGION" \
  --query "Items[?Name=='cognito-jwt'].AuthorizerId | [0]" --output text 2>/dev/null || echo "None")

if [ "$AUTH_ID" = "None" ] || [ -z "$AUTH_ID" ]; then
  AUTH_ID=$(aws apigatewayv2 create-authorizer \
    --api-id "$APIGW_ID" \
    --name "cognito-jwt" \
    --authorizer-type JWT \
    --identity-source '$request.header.Authorization' \
    --jwt-configuration "Issuer=${COGNITO_ISSUER},Audience=${COGNITO_CLIENT_ID}" \
    --region "$AWS_REGION" \
    --query 'AuthorizerId' --output text)
  echo "  created: ${AUTH_ID}"
else
  echo "  already exists: ${AUTH_ID}"
fi

# ── 5. Lambda integration ───────────────────────────────────────
echo "→ Lambda integration"
LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_FUNCTION}"
INTEG_ID=$(aws apigatewayv2 get-integrations --api-id "$APIGW_ID" --region "$AWS_REGION" \
  --query "Items[?IntegrationType=='AWS_PROXY'].IntegrationId | [0]" --output text 2>/dev/null || echo "None")

if [ "$INTEG_ID" = "None" ] || [ -z "$INTEG_ID" ]; then
  INTEG_ID=$(aws apigatewayv2 create-integration \
    --api-id "$APIGW_ID" \
    --integration-type AWS_PROXY \
    --integration-uri "$LAMBDA_ARN" \
    --payload-format-version "2.0" \
    --region "$AWS_REGION" \
    --query 'IntegrationId' --output text)
  echo "  created: ${INTEG_ID}"
else
  echo "  already exists: ${INTEG_ID}"
fi

# ── 6. Routes ────────────────────────────────────────────────────
create_route() {
  local ROUTE_KEY="$1"
  local USE_AUTH="$2"

  local EXISTING
  EXISTING=$(aws apigatewayv2 get-routes --api-id "$APIGW_ID" --region "$AWS_REGION" \
    --query "Items[?RouteKey=='${ROUTE_KEY}'].RouteId | [0]" --output text 2>/dev/null || echo "None")

  if [ "$EXISTING" != "None" ] && [ -n "$EXISTING" ]; then
    echo "  route '${ROUTE_KEY}' already exists"
    return
  fi

  local AUTH_ARGS=""
  if [ "$USE_AUTH" = "true" ]; then
    AUTH_ARGS="--authorization-type JWT --authorizer-id ${AUTH_ID}"
  fi

  aws apigatewayv2 create-route \
    --api-id "$APIGW_ID" \
    --route-key "$ROUTE_KEY" \
    --target "integrations/${INTEG_ID}" \
    $AUTH_ARGS \
    --region "$AWS_REGION" \
    --output text >/dev/null
  echo "  route '${ROUTE_KEY}' created"
}

echo "→ Routes"
create_route "GET /api/health" "false"
create_route "POST /api/{proxy+}" "true"

# ── 7. Stage (prod, auto-deploy) ────────────────────────────────
echo "→ Stage: prod"
STAGE_EXISTS=$(aws apigatewayv2 get-stages --api-id "$APIGW_ID" --region "$AWS_REGION" \
  --query "Items[?StageName=='prod'].StageName | [0]" --output text 2>/dev/null || echo "None")

if [ "$STAGE_EXISTS" = "None" ] || [ -z "$STAGE_EXISTS" ]; then
  aws apigatewayv2 create-stage \
    --api-id "$APIGW_ID" \
    --stage-name "prod" \
    --auto-deploy \
    --region "$AWS_REGION" \
    --output text >/dev/null
  echo "  created"
else
  echo "  already exists"
fi

# ── 8. Write outputs ─────────────────────────────────────────────
# Note: Lambda invoke permission is set by push.sh after the function exists.
APIGW_URL="https://${APIGW_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod"
cat > "$SCRIPT_DIR/outputs.env" <<EOF
APIGW_ID=${APIGW_ID}
APIGW_URL=${APIGW_URL}
LAMBDA_ARN=${LAMBDA_ARN}
ROLE_ARN=${ROLE_ARN}
AUTH_ID=${AUTH_ID}
EOF

echo ""
echo "=== Setup complete ==="
echo "API Gateway URL: ${APIGW_URL}"
echo "Outputs written to: ${SCRIPT_DIR}/outputs.env"
