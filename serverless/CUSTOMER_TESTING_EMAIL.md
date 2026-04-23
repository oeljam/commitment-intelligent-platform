# Commitment Intelligent Platform — Testing Guide

Hi team,

The **Commitment Intelligent Platform v0.3** is ready for testing. This serverless solution analyzes PPA/EDP documents using Bedrock AI, surfaces credit qualification opportunities against live Cost Explorer data, and lets you accept/reject recommendations with email notifications.

Below is everything you need to deploy and validate in your own AWS account.

---

## What's Included

| File | Purpose |
|------|---------|
| `template.yaml` | SAM/CloudFormation template — deploys the full stack |
| `lambdas/api.py` | All Lambda handlers (upload, analyze, recommendations, decision, history, spend, send-email) |
| `frontend/index.html` | Single-page dashboard (S3 + CloudFront) |
| `deploy.sh` | One-command deploy script |
| `test_platform.sh` | Automated end-to-end test script |
| `acme_ppa_edp_2026.pdf` | Sample PPA/EDP document for testing |

---

## Architecture

```
CloudFront → S3 (frontend)
Browser → API Gateway (HTTP API) → Lambda → Bedrock Claude Haiku 4.5
                                          → DynamoDB
                                          → S3 (document storage)
                                          → SES (email notifications)
                                          → Cost Explorer (live spend)
```

### AWS Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| DocumentsBucket | S3 | Stores uploaded PPA/EDP PDFs |
| FrontendBucket | S3 | Hosts the dashboard UI |
| CloudFrontDist | CloudFront | HTTPS delivery of the frontend |
| RecommendationsTable | DynamoDB (on-demand) | Stores documents, recommendations, decisions, history |
| Api | HTTP API Gateway | REST endpoints for all operations |
| 7 Lambda Functions | Python 3.12 | Upload, Analyze, Recommendations, Decision, History, Spend, SendEmail |

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `SenderEmail` | Yes | An SES-verified email address used for sending notifications |

---

## Prerequisites

- AWS CLI v2 configured with credentials that have admin or equivalent permissions
- SAM CLI **or** just the AWS CLI (the deploy script uses `cloudformation package/deploy`)
- An email address you can verify in SES (you'll receive a verification link)
- Bedrock model access enabled for **Claude Haiku 4.5** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) in your region

### Enable Bedrock Model Access

1. Go to **Amazon Bedrock → Model access** in the AWS Console
2. Request access to **Anthropic → Claude Haiku 4.5**
3. Wait for status to show "Access granted" (usually instant)

---

## Deployment (Option A: One-Command)

```bash
cd serverless/
./deploy.sh your-email@example.com
```

This will:
1. Create a deployment S3 bucket
2. Package and deploy the CloudFormation stack
3. Upload the frontend to S3
4. Invalidate CloudFront cache
5. Send an SES verification email

**Check your inbox** and click the SES verification link before testing email features.

## Deployment (Option B: Manual)

```bash
REGION=us-east-1
STACK=commitment-intelligent-platform

# Package
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket <your-deploy-bucket> \
  --output-template-file .packaged.yaml \
  --region $REGION

# Deploy
aws cloudformation deploy \
  --template-file .packaged.yaml \
  --stack-name $STACK \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides SenderEmail=your-email@example.com \
  --region $REGION

# Get outputs
aws cloudformation describe-stacks --stack-name $STACK --region $REGION \
  --query "Stacks[0].Outputs"
```

---

## Automated Testing

Run the full end-to-end test suite:

```bash
cd serverless/
./test_platform.sh your-email@example.com us-east-1
```

This script will:

| Step | What it does |
|------|-------------|
| 1 | Deploy/update the CloudFormation stack |
| 2 | Upload the frontend to S3 + invalidate CloudFront |
| 3 | Verify SES sender identity |
| 4 | `POST /upload` — get a presigned URL and upload the sample PDF |
| 5 | `POST /analyze` — send the PDF to Bedrock for AI analysis (~15-30s) |
| 6 | `GET /recommendations` — retrieve generated recommendations |
| 6 | `POST /decision` — accept the first recommendation |
| 6 | `GET /history` — verify the decision was recorded |
| 6 | `GET /spend` — pull live Cost Explorer data |
| 6 | `POST /send-email` — send a test notification via SES |
| 7 | Print pass/fail summary |

Expected output: **all endpoints return HTTP 200** with a pass/fail summary at the end.

---

## Manual Testing via the UI

1. Open the **Frontend URL** from the stack outputs (CloudFront HTTPS URL)
2. When prompted, paste the **API URL** from the stack outputs
3. Walk through the setup wizard:
   - **Step 1**: Upload `acme_ppa_edp_2026.pdf` (included in the repo)
   - **Step 2**: Select notification teams and/or add custom email addresses
   - **Step 3**: Click "Analyze with Bedrock AI" — wait ~15-30s
4. On the dashboard, verify:
   - **Overview tab**: YTD spend chart (Cost Explorer), credit coupling analysis, savings metrics
   - **Recommendations tab**: AI-generated recommendations with accept/reject/email actions
   - **History tab**: Decision audit trail

---

## API Endpoints Reference

All endpoints are under the API Gateway base URL.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Returns a presigned S3 URL for PDF upload |
| POST | `/analyze` | Sends document to Bedrock, returns recommendations |
| GET | `/recommendations?analysis_id=<id>` | Retrieves recommendations for an analysis |
| POST | `/decision` | Accept or reject a recommendation |
| GET | `/history` | Returns all decision history |
| GET | `/spend` | Live spend data from Cost Explorer with credit coupling analysis |
| POST | `/send-email` | Sends HTML email notification via SES |

---

## Cleanup

To tear down all resources:

```bash
# Empty the S3 buckets first
DOCS_BUCKET=$(aws cloudformation describe-stacks --stack-name commitment-intelligent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='DocumentsBucket'].OutputValue" --output text)
FRONT_BUCKET=$(aws cloudformation describe-stacks --stack-name commitment-intelligent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)

aws s3 rm "s3://$DOCS_BUCKET" --recursive
aws s3 rm "s3://$FRONT_BUCKET" --recursive

# Delete the stack
aws cloudformation delete-stack --stack-name commitment-intelligent-platform
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `/analyze` returns 500 | Verify Bedrock model access is enabled for Claude Haiku 4.5 in your region |
| `/send-email` returns 500 | Confirm you clicked the SES verification link. In sandbox mode, recipients must also be verified |
| `/spend` returns empty | Cost Explorer needs 24-48h of billing data. New accounts may show $0 |
| Frontend shows blank page | Paste the API Gateway URL when prompted (check browser console for errors) |
| CloudFront returns 403 | Wait 5-10 min for distribution deployment, or run `deploy.sh` again to invalidate cache |

---

Let me know if you hit any issues or need help with the deployment. Happy testing!
