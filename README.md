# 🎯 Commitment Intelligent Platform

An AI-powered platform that helps AWS customers maximize the value of their cloud commitments. Upload a PPA (Private Pricing Addendum) or EDP (Enterprise Discount Program) document, and the platform uses **Amazon Bedrock** to analyze it against your **live AWS spend**, surface credit qualification opportunities, and drive action through accept/reject workflows with email notifications.

## 💡 What Problem Does This Solve?

AWS customers with PPA/EDP agreements often struggle to:
- **Track commitment progress** against annual spend targets
- **Identify credit opportunities** they're already qualified for (Graviton, Serverless, Security, Analytics)
- **Connect the dots** between their actual service usage and available discount programs
- **Coordinate across teams** (Finance, Engineering, Operations) to act on recommendations
- **Maintain audit trails** for attestation and compliance requirements

This platform automates all of that — from document analysis to team notification — in a single serverless application.

## 🆕 What's New in v1.0 — Serverless Rebuild

### Complete Serverless Architecture
- **Zero servers to manage** — fully deployed via a single CloudFormation/SAM template
- **Amazon Bedrock** (Claude Haiku 4.5) replaces local AI for document analysis
- **Live Cost Explorer integration** — real spend data, not estimates
- **Credit coupling engine** — automatically maps your services to credit programs

### AI-Powered Analysis
- Upload a PPA/EDP PDF and get instant recommendations
- Confidence scoring and qualification status per recommendation
- Reasoning explanations for each credit opportunity
- Potential savings calculations based on actual usage

### Business Workflow
- **Setup Wizard** — guided 3-step process: Upload → Configure Teams → Analyze
- **Accept/Reject Workflow** — decision tracking with notes and audit history
- **Email Notifications** — HTML emails via SES to predefined teams or custom recipients
- **Spend Dashboard** — YTD spend vs commitment target with monthly charts

## 🏗️ Architecture

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
| FrontendBucket + CloudFront | S3 + CDN | Hosts the dashboard UI over HTTPS |
| RecommendationsTable | DynamoDB (on-demand) | Documents, recommendations, decisions, history |
| Api | HTTP API Gateway | REST endpoints for all operations |
| 7 Lambda Functions | Python 3.12 | Upload, Analyze, Recommendations, Decision, History, Spend, SendEmail |

## 🚀 Quick Start

### Prerequisites
- AWS CLI v2 with admin permissions
- Bedrock model access for **Claude Haiku 4.5** (Bedrock → Model access in console)

### Deploy (one command)

```bash
cd serverless/
./deploy.sh your-ses-verified-email@example.com
```

This will:
1. Create a deployment S3 bucket
2. Package and deploy the CloudFormation stack
3. Upload the frontend to S3
4. Invalidate CloudFront cache
5. Send an SES verification email

**Check your inbox** and click the SES verification link before testing email features.

### Test (automated)

```bash
./test_platform.sh your-ses-verified-email@example.com us-east-1
```

Deploys the stack, uploads the sample PPA document, runs Bedrock analysis, and tests all 7 API endpoints with a pass/fail summary.

### Test (manual via UI)

1. Open the **Frontend URL** from stack outputs
2. Paste the **API URL** when prompted
3. Upload `acme_ppa_edp_2026.pdf` (included)
4. Select notification teams → click **Analyze with Bedrock AI**
5. Review recommendations, accept/reject, send emails

## 📊 Usage Workflow

### 1. Preparation Phase
- Upload PPA/EDP PDF documents
- Configure email distribution (predefined teams + custom recipients)

### 2. Analysis Phase
- Bedrock AI analyzes the document for commitment and credit opportunities
- Recommendations generated with confidence scores, qualification status, and savings estimates
- Live Cost Explorer data mapped to credit programs

### 3. Action Phase
- Accept or reject each recommendation with notes
- Send HTML email notifications to stakeholders
- Track decisions in the audit trail

### 4. Tracking Phase
- View recommendation and decision history
- Monitor YTD spend vs commitment targets
- Review credit coupling analysis against live service usage

## 📋 Features

### Core Functionality
- **AI Document Analysis** — Bedrock Claude analyzes PPA/EDP PDFs and extracts commitment opportunities
- **Credit Coupling Engine** — Maps live Cost Explorer spend to credit qualification programs (Graviton, Serverless, Security, Analytics)
- **Spend Tracking** — YTD spend vs commitment target with monthly breakdown charts
- **Savings Estimation** — Per-recommendation potential savings based on actual usage

### Integration Capabilities
- **Amazon Bedrock** — Claude Haiku 4.5 for intelligent document analysis
- **Cost Explorer** — Real-time spend data and service-level breakdown
- **Amazon SES** — HTML email notifications to teams and custom recipients
- **DynamoDB** — Persistent storage for documents, recommendations, decisions, and history

### User Interface
- **Responsive Dashboard** — Works on desktop and mobile
- **Setup Wizard** — Guided 3-step onboarding
- **Toast Notifications** — Real-time feedback for all actions
- **Interactive Charts** — Spend vs target, savings by credit type

## 🔍 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Returns presigned S3 URL for PDF upload |
| POST | `/analyze` | Sends document to Bedrock, returns recommendations |
| GET | `/recommendations` | Retrieves recommendations for an analysis |
| POST | `/decision` | Accept or reject a recommendation |
| GET | `/history` | Decision audit trail |
| GET | `/spend` | Live Cost Explorer data + credit coupling analysis |
| POST | `/send-email` | HTML email notification via SES |

## 📁 Project Structure

```
serverless/
├── template.yaml              # CloudFormation/SAM template (entire stack)
├── lambdas/api.py             # All Lambda handlers
├── frontend/index.html        # Single-page dashboard UI
├── deploy.sh                  # One-command deploy script
├── test_platform.sh           # Automated end-to-end test
├── acme_ppa_edp_2026.pdf      # Sample PPA/EDP document
├── generate_ppa.py            # Script to generate sample PDFs
└── CUSTOMER_TESTING_EMAIL.md  # Customer-facing testing guide
```

## 🧹 Cleanup

```bash
# Get bucket names from stack outputs
DOCS=$(aws cloudformation describe-stacks --stack-name commitment-intelligent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='DocumentsBucket'].OutputValue" --output text)
FRONT=$(aws cloudformation describe-stacks --stack-name commitment-intelligent-platform \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)

# Empty buckets and delete stack
aws s3 rm "s3://$DOCS" --recursive
aws s3 rm "s3://$FRONT" --recursive
aws cloudformation delete-stack --stack-name commitment-intelligent-platform
```

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| `/analyze` returns 500 | Enable Bedrock model access for Claude Haiku 4.5 in your region |
| `/send-email` returns 500 | Click SES verification link. In sandbox mode, recipients must also be verified |
| `/spend` returns empty | Cost Explorer needs 24-48h of billing data. New accounts may show $0 |
| Frontend shows blank | Paste the API Gateway URL when prompted (check browser console) |
| CloudFront returns 403 | Wait 5-10 min for distribution deployment |

## 📝 Version History

### v1.0 (Current) — Serverless Rebuild
- Complete serverless architecture via CloudFormation/SAM
- Amazon Bedrock (Claude Haiku 4.5) for AI document analysis
- Live Cost Explorer integration with credit coupling engine
- Amazon SES email notifications
- Automated end-to-end test script
- Single-page dashboard with setup wizard

### v0.3 — Flask Dashboard
- Local Flask application with Python backend
- SMTP-based email sending
- Microsoft Outlook calendar integration via Graph API
- MCP server architecture

### v0.2
- Learning system for adaptive recommendations
- User preferences and customization
- Enhanced PDF processing

### v0.1
- Initial release with PDF analysis
- Basic recommendation generation
- Simple web interface

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Review the troubleshooting guide above
- Check `CUSTOMER_TESTING_EMAIL.md` for detailed deployment instructions

## 🔮 Roadmap

- Multi-account support via AWS Organizations
- Cognito authentication
- Step Functions for async analysis pipelines
- QuickSight embedded dashboards
- Slack/Teams integration for notifications
