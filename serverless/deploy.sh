#!/bin/bash
set -e

STACK_NAME="commitment-intelligent-platform"
REGION="${AWS_REGION:-us-east-1}"
SENDER_EMAIL="${1:?Usage: ./deploy.sh <sender-email>}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Deploying $STACK_NAME to $REGION"
echo "   Sender email: $SENDER_EMAIL"
echo ""

# 1. Create SAM build bucket if needed
DEPLOY_BUCKET="$STACK_NAME-deploy-$(aws sts get-caller-identity --query Account --output text)"
if ! aws s3 ls "s3://$DEPLOY_BUCKET" --region "$REGION" 2>/dev/null; then
  echo "📦 Creating deployment bucket: $DEPLOY_BUCKET"
  aws s3 mb "s3://$DEPLOY_BUCKET" --region "$REGION"
fi

# 2. Package & Deploy CloudFormation
echo "📋 Packaging SAM template..."
aws cloudformation package \
  --template-file "$DIR/template.yaml" \
  --s3-bucket "$DEPLOY_BUCKET" \
  --output-template-file "$DIR/.packaged.yaml" \
  --region "$REGION"

echo "☁️  Deploying stack..."
aws cloudformation deploy \
  --template-file "$DIR/.packaged.yaml" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides SenderEmail="$SENDER_EMAIL" \
  --region "$REGION"

# 3. Get outputs
echo "📡 Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
FRONTEND_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text)
FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)
DIST_ID=$(aws cloudformation describe-stack-resources --stack-name "$STACK_NAME" --region "$REGION" --query "StackResources[?LogicalResourceId=='CloudFrontDist'].PhysicalResourceId" --output text)

# 4. Upload frontend
echo "🌐 Uploading frontend to S3..."
aws s3 cp "$DIR/frontend/index.html" "s3://$FRONTEND_BUCKET/index.html" --content-type "text/html" --region "$REGION"

# 4b. Invalidate CloudFront
if [ -n "$DIST_ID" ]; then
  echo "🔄 Invalidating CloudFront cache..."
  aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" --region "$REGION" > /dev/null
fi

# 5. Verify SES sender
echo "📧 Verifying SES sender email..."
aws ses verify-email-identity --email-address "$SENDER_EMAIL" --region "$REGION" 2>/dev/null || true

echo ""
echo "✅ Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend:  $FRONTEND_URL"
echo "📡 API:       $API_URL"
echo "📧 SES:       Check $SENDER_EMAIL inbox to verify"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Open the frontend URL and paste the API URL when prompted."

rm -f "$DIR/.packaged.yaml"
