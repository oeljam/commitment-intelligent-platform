# Changelog

All notable changes to the Commitment Intelligent Platform.

## [1.1.0] - 2026-08-24

### Added
- **CSV/Excel spend upload** — Account Managers and TAMs without direct Cost Explorer access can upload spend data as CSV or Excel files. Supports multiple formats: simple (Service,Amount), monthly pivot (Service,2024-01,2024-02,...), CUR-style (Service,Date,Amount), and Cost Explorer export format.
- **Multi-account filtering** — configure linked account IDs to scope Cost Explorer queries and Bedrock analysis to specific accounts within a payer organization.
- **Credit ledger** — track approved credits with running totals. Auto-populates when attestations are completed with approved amounts. Cumulative progress feeds back into Bedrock analysis.
- **Attestation submission history** — full audit trail of completed attestations including filled fields, approved amounts, and timestamps.
- **Configurable AI service definitions** — environment variable `AI_SERVICES` controls which services are counted as AI/GenAI spend (default: Bedrock, SageMaker, Trainium, Inferentia).
- **Learning loop** — past accept/reject decisions and credit ledger history are injected into the Bedrock prompt, improving future recommendations based on user preferences.
- **Session persistence** — frontend saves API URL and analysis state in localStorage, survives browser refresh.
- **Credit tracking dashboard** — frontend shows approved credits, running totals, and progress vs maximum available credit.

### Changed
- Frontend: improved chart rendering with cumulative spend visualization and progress bars.
- Bedrock prompt: now includes AI service definitions, decision history, and credit ledger context.
- `/spend` endpoint: returns uploaded CSV data when available, with full monthly breakdown and AI spend isolation.
- `/attestations` POST: completing an attestation with `approved_amount > 0` auto-adds a credit ledger entry.

### Infrastructure
- 4 new Lambda functions: CsvUploadFunction, CreditLedgerFunction, AccountsFunction, ReminderFunction
- 4 new API routes: `/csv-upload`, `/credit-ledger`, `/accounts`, EventBridge schedule for reminders
- Total: 13 Lambda handlers, 11 API endpoints

## [1.0.0] - 2026-04-21

### Added
- Complete serverless architecture deployed via single CloudFormation/SAM template.
- Amazon Bedrock (Claude Haiku 4.5) integration for AI document analysis.
- Live AWS Cost Explorer integration — YTD spend, monthly breakdown, by-service detail.
- Credit coupling engine — maps active services to credit qualification programs (Graviton, Serverless, GenAI, Analytics).
- Async analysis pipeline: API trigger → Lambda worker (300s timeout) → DynamoDB results.
- JSON repair utility for handling truncated Bedrock responses.
- What-if scenarios per recommendation — shows impact of spend shifts on credit qualification.
- Attestation tracking — extracts governance requirements from PPA, auto-populates fields from CE data.
- Recurring attestations — auto-generates next occurrence on completion.
- EventBridge-scheduled attestation reminders — daily check, emails 7 days before due.
- Accept/reject workflow with decision notes and full audit history.
- HTML email notifications via Amazon SES.
- Single-page responsive dashboard with setup wizard.
- Interactive Chart.js visualizations — spend vs target, savings by credit type.
- Toast notification system for real-time user feedback.
- Automated end-to-end test script (`test_platform.sh`).
- Sample PPA/EDP document (`acme_ppa_edp_2026.pdf`) and PDF generator script.
- Customer-facing testing guide (`CUSTOMER_TESTING_EMAIL.md`).

### Infrastructure
- S3 buckets for documents and frontend hosting
- CloudFront distribution with OAC
- DynamoDB table (on-demand billing)
- HTTP API Gateway with CORS
- 9 Lambda functions (Python 3.12)
- SES sender identity verification
- One-command deploy script (`deploy.sh`)

## [0.3.0] - 2024-11-17

### Added
- Flask web dashboard with inline HTML/JS.
- PDF upload and simulated analysis workflow.
- Accept/reject recommendation buttons with in-memory history.
- Chart.js monthly spend vs commitment target visualization.
- Microsoft Outlook calendar integration via Graph API (MCP server).
- SMTP-based email notifications.
- Credit coupling server module.

## [0.2.0] - 2024-11-15

### Added
- Learning system for adaptive recommendations based on user feedback.
- User preferences and customization settings.
- Enhanced PDF text extraction.

## [0.1.0] - 2024-11-10

### Added
- Initial release.
- PDF document upload and basic text extraction.
- Rule-based recommendation generation.
- Simple web interface.
