#!/usr/bin/env bash
# Push image to ECR and create/update the Lambda function.
# Also sets reserved concurrency and Lambda Function URL on first run.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# ── ECR login + push ───────────────────────────────────────────────────────────
echo "=== ECR login ==="
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "=== Tag + push ==="
docker tag "$IMAGE" "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"

# ── Lambda function ────────────────────────────────────────────────────────────
ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" \
  --query 'Role.Arn' --output text)

echo "=== Lambda: ${LAMBDA_FUNCTION} ==="
if aws lambda get-function --function-name "$LAMBDA_FUNCTION" \
    --region "$AWS_REGION" &>/dev/null; then
  echo "  updating code..."
  aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION" \
    --image-uri "${ECR_URI}:latest" \
    --region "$AWS_REGION" \
    --output text >/dev/null
else
  echo "  creating function..."
  aws lambda create-function \
    --function-name "$LAMBDA_FUNCTION" \
    --package-type Image \
    --code "ImageUri=${ECR_URI}:latest" \
    --role "$ROLE_ARN" \
    --memory-size "$LAMBDA_MEMORY_MB" \
    --timeout "$LAMBDA_TIMEOUT_S" \
    --region "$AWS_REGION" \
    --output text >/dev/null
fi

echo "  waiting for function to be active..."
aws lambda wait function-active-v2 \
  --function-name "$LAMBDA_FUNCTION" --region "$AWS_REGION"
aws lambda wait function-updated-v2 \
  --function-name "$LAMBDA_FUNCTION" --region "$AWS_REGION" 2>/dev/null || true

# ── Reserved concurrency (hard per-function cost cap) ─────────────────────────
echo "=== Reserved concurrency: ${RESERVED_CONCURRENCY} ==="
aws lambda put-function-concurrency \
  --function-name "$LAMBDA_FUNCTION" \
  --reserved-concurrent-executions "$RESERVED_CONCURRENCY" \
  --region "$AWS_REGION" \
  --output text >/dev/null
echo "  set — max simultaneous executions: ${RESERVED_CONCURRENCY}"

# ── Lambda Function URL (public HTTPS endpoint, no API Gateway) ────────────────
CORS_EXPOSE="${CORS_EXPOSE_HEADERS:-Content-Disposition}"

ensure_lambda_permission() {
  local statement_id="$1"
  shift

  local policy
  policy="$(aws lambda get-policy \
    --function-name "$LAMBDA_FUNCTION" \
    --region "$AWS_REGION" \
    --query 'Policy' --output text 2>/dev/null || true)"

  if printf '%s' "$policy" | grep -q "\"Sid\":\"${statement_id}\""; then
    echo "  permission ${statement_id} already exists"
    return 0
  fi

  aws lambda add-permission \
    --function-name "$LAMBDA_FUNCTION" \
    --statement-id "$statement_id" \
    --region "$AWS_REGION" \
    "$@" \
    --output text >/dev/null
  echo "  added permission ${statement_id}"
}

echo "=== Function URL ==="
if aws lambda get-function-url-config \
    --function-name "$LAMBDA_FUNCTION" \
    --region "$AWS_REGION" &>/dev/null; then
  echo "  updating existing config"
  aws lambda update-function-url-config \
    --function-name "$LAMBDA_FUNCTION" \
    --auth-type NONE \
    --cors "{
      \"AllowOrigins\": [\"*\"],
      \"AllowMethods\": [\"GET\",\"POST\",\"PUT\",\"DELETE\"],
      \"AllowHeaders\": [\"content-type\"],
      \"ExposeHeaders\": [\"${CORS_EXPOSE}\"],
      \"MaxAge\": 3600
    }" \
    --region "$AWS_REGION" \
    --output text >/dev/null
else
  FUNCTION_URL=$(aws lambda create-function-url-config \
    --function-name "$LAMBDA_FUNCTION" \
    --auth-type NONE \
    --cors "{
      \"AllowOrigins\": [\"*\"],
      \"AllowMethods\": [\"GET\",\"POST\",\"PUT\",\"DELETE\"],
      \"AllowHeaders\": [\"content-type\"],
      \"ExposeHeaders\": [\"${CORS_EXPOSE}\"],
      \"MaxAge\": 3600
    }" \
    --region "$AWS_REGION" \
    --query 'FunctionUrl' --output text)

  echo "  created: ${FUNCTION_URL}"
fi

# Allow unauthenticated public invocation via the Function URL.
ensure_lambda_permission \
  "FunctionURLAllowPublicAccess" \
  --action "lambda:InvokeFunctionUrl" \
  --principal "*" \
  --function-url-auth-type NONE

ensure_lambda_permission \
  "FunctionURLInvokeAllowPublicAccess" \
  --action "lambda:InvokeFunction" \
  --principal "*" \
  --invoked-via-function-url

# Print the URL for netlify.toml
FUNCTION_URL=$(aws lambda get-function-url-config \
  --function-name "$LAMBDA_FUNCTION" \
  --region "$AWS_REGION" \
  --query 'FunctionUrl' --output text)
# Strip trailing slash
FUNCTION_URL="${FUNCTION_URL%/}"

# Write outputs
cat > "$SCRIPT_DIR/outputs.env" <<EOF
LAMBDA_FUNCTION=${LAMBDA_FUNCTION}
FUNCTION_URL=${FUNCTION_URL}
EOF

echo ""
echo "=== Deploy complete ==="
echo "Function URL: ${FUNCTION_URL}"
echo ""
echo "Add to netlify.toml (replace /your-prefix with your server's path prefix):"
echo ""
echo "  [[redirects]]"
echo "    from = \"/your-prefix/*\""
echo "    to = \"${FUNCTION_URL}/your-prefix/:splat\""
echo "    status = 200"
echo "    force = true"
