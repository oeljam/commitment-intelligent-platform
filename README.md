# 🎯 Commitment Intelligent Platform

AI-powered analysis of cloud commitment agreements. Upload your PPA, MACC, or EDP document, and the platform uses **Amazon Bedrock** to analyze it against your **live spend data** — surfacing credit opportunities, tracking commitment burn rate, and managing attestation deadlines.

## Supported Providers

| Provider | Document | Discount Model |
|----------|----------|----------------|
| **AWS** | PPA / EDP | Stacking — RI/SP + PPA compound |
| **Azure** | MACC / EA | Bundled — isolate from M365/Dynamics |
| **GCP** | EDP / PA | Non-Stacking — deepest discount wins |

## How It Works

1. **Upload** — Drop your commitment document PDF into the dashboard
2. **Analyze** — Bedrock AI reads the document + your live Cost Explorer data
3. **Track** — Dashboard shows burn rate vs commitment target, credit progress, upcoming deadlines
4. **Act** — Accept/reject recommendations, complete attestations, monitor commitment health

## Quick Start

```bash
cd serverless/
./deploy.sh your-email@example.com
```

Open the Frontend URL from the output, paste the API URL, and upload your commitment document.

## Architecture

```
Browser → CloudFront → S3 (frontend)
Browser → API Gateway → Lambda → Bedrock (analysis)
                                → DynamoDB (storage)
                                → Cost Explorer (spend data)
                                → S3 (PDF storage)
                                → SES (email notifications)
```

## Project Structure

```
serverless/
├── template.yaml          # SAM template (entire infrastructure)
├── lambdas/api.py         # All Lambda handlers
├── frontend/index.html    # Dashboard
└── deploy.sh              # One-command deploy
```

## License

MIT
