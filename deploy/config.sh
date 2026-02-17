#!/usr/bin/env bash
# Shared constants for deploy scripts.

export AWS_REGION="ap-south-1"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"

# ECR
export ECR_REPO="form-idable-server"
export ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

# Lambda
export LAMBDA_FUNCTION="form-idable-server"
export LAMBDA_ROLE_NAME="form-idable-lambda-role"

# API Gateway
export APIGW_NAME="form-idable-api"

# Cognito (shared pool — same as photomon / fomomon)
export COGNITO_POOL_ID="ap-south-1_28HVATwK2"
export COGNITO_CLIENT_ID="1j0f2k3top2af4m8da7nbmeu63"
export COGNITO_ISSUER="https://cognito-idp.${AWS_REGION}.amazonaws.com/${COGNITO_POOL_ID}"
