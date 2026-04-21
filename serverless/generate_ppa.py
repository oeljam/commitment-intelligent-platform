#!/usr/bin/env python3
"""Generate a realistic AWS PPA/EDP commitment PDF based on actual account spend."""
from fpdf import FPDF
from datetime import datetime

class PPA_PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(35, 47, 62)
        self.cell(0, 8, 'AMAZON WEB SERVICES - CONFIDENTIAL', align='R', new_x='LMARGIN', new_y='NEXT')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'AWS Private Pricing Addendum - Page {self.page_no()}/{{nb}}', align='C')

    def section(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(35, 47, 62)
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 51, 51)

    def para(self, text):
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def table_row(self, cols, widths, bold=False):
        self.set_font('Helvetica', 'B' if bold else '', 9)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, str(col), border=1, align='C' if i > 0 else 'L')
        self.ln()

pdf = PPA_PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title
pdf.set_font('Helvetica', 'B', 18)
pdf.set_text_color(35, 47, 62)
pdf.cell(0, 12, 'Private Pricing Addendum', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(255, 153, 0)
pdf.cell(0, 8, 'Enterprise Discount Program (EDP)', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(6)

# Agreement details
pdf.set_text_color(51, 51, 51)
pdf.set_font('Helvetica', '', 10)
w = [45, 145]
details = [
    ('Agreement ID:', 'PPA-2026-EMEA-048291'),
    ('Effective Date:', 'January 1, 2026'),
    ('Term End Date:', 'December 31, 2026'),
    ('Customer:', 'Acme Cloud Solutions Ltd.'),
    ('AWS Account ID:', '893878498710'),
    ('Region:', 'EMEA (Europe, Middle East, Africa)'),
    ('AWS Contact:', 'AWS Enterprise Support - Sr. TAM'),
    ('Document Date:', datetime.now().strftime('%B %d, %Y')),
]
for label, val in details:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(w[0], 6, label)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(w[1], 6, val, new_x='LMARGIN', new_y='NEXT')
pdf.ln(6)

# Section 1
pdf.section('1. COMMITMENT OVERVIEW')
pdf.para(
    'This Private Pricing Addendum ("PPA") establishes the terms of the Enterprise Discount '
    'Program between Acme Cloud Solutions Ltd. ("Customer") and Amazon Web Services, Inc. ("AWS"). '
    'The Customer commits to a minimum annual spend in exchange for tiered discount pricing across '
    'eligible AWS services.'
)

# Commitment table
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, 'Annual Commitment Structure:', new_x='LMARGIN', new_y='NEXT')
cw = [70, 40, 40, 40]
pdf.table_row(['Commitment Tier', 'Annual Spend', 'Discount Rate', 'Status'], cw, bold=True)
pdf.table_row(['Tier 1 - Base', '$5,000', '8%', 'Active'], cw)
pdf.table_row(['Tier 2 - Growth', '$10,000', '12%', 'Target'], cw)
pdf.table_row(['Tier 3 - Scale', '$25,000', '18%', 'Stretch'], cw)
pdf.table_row(['Tier 4 - Enterprise', '$50,000', '23%', 'Aspirational'], cw)
pdf.ln(4)

pdf.para(
    'Current YTD spend as of April 2026: $921.81. The Customer is currently tracking within '
    'Tier 1 and is projected to reach Tier 2 by Q3 2026 based on observed growth trajectory. '
    'Monthly spend trend: Jan $495.58, Feb $214.97, Mar $126.76, Apr $84.50 (month in progress).'
)

# Section 2
pdf.section('2. ELIGIBLE SERVICES & CURRENT USAGE')
pdf.para(
    'The following AWS services are included in the EDP commitment calculation. Services are '
    'grouped by category with current monthly spend as observed in the Customer account.'
)

sw = [90, 35, 35, 30]
pdf.table_row(['Service', 'Monthly Spend', 'YTD Estimate', 'Category'], sw, bold=True)
services = [
    ('Amazon EC2 - Compute', '$44.42', '$533', 'Compute'),
    ('AWS Config', '$13.53', '$162', 'Security'),
    ('AWS Security Hub', '$9.14', '$110', 'Security'),
    ('AWS Key Management Service', '$4.00', '$48', 'Security'),
    ('Amazon CloudWatch', '$2.49', '$30', 'Monitoring'),
    ('Amazon VPC', '$2.41', '$29', 'Networking'),
    ('Amazon GuardDuty', '$1.95', '$23', 'Security'),
    ('Amazon S3', '$1.81', '$22', 'Storage'),
    ('Amazon RDS', '$1.16', '$14', 'Database'),
    ('AWS Secrets Manager', '$1.07', '$13', 'Security'),
    ('Amazon Inspector', '$0.96', '$12', 'Security'),
    ('Amazon Macie', '$0.53', '$6', 'Security'),
]
for s in services:
    pdf.table_row(s, sw)
pdf.ln(4)

pdf.para(
    'Note: The Customer account demonstrates a strong security posture with significant investment '
    'in AWS security services (Config, Security Hub, GuardDuty, Inspector, Macie, KMS). This '
    'security-first approach qualifies for the AWS Security Services Credit Program.'
)

# Section 3
pdf.add_page()
pdf.section('3. CREDIT QUALIFICATION OPPORTUNITIES')
pdf.para(
    'Based on current service usage patterns, the following credit and discount programs are '
    'available or within reach for the Customer:'
)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, '3.1 Graviton Optimization Credit (31% discount)', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
pdf.para(
    'Status: PARTIALLY QUALIFIED. The Customer is running EC2 compute workloads ($44.42/mo). '
    'Migrating to Graviton-based instances (t4g, m7g, c7g families) would unlock a 31% discount '
    'on compute spend. Requirements: (1) Migrate primary EC2 workloads to ARM/Graviton, '
    '(2) Maintain minimum $500/mo in Graviton compute, (3) Add RDS Graviton instances for '
    'additional qualification. Estimated annual savings: $165 at current spend, scaling with growth.'
)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, '3.2 Security Services Credit Program (15% discount)', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
pdf.para(
    'Status: QUALIFIED. The Customer is actively using 6 AWS security services: Config ($13.53), '
    'Security Hub ($9.14), KMS ($4.00), GuardDuty ($1.95), Inspector ($0.96), and Macie ($0.53). '
    'Combined security spend of $30.11/mo qualifies for the Security Services bundle credit. '
    'Estimated annual savings: $54.'
)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, '3.3 Compute Savings Plan (20% discount)', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
pdf.para(
    'Status: RECOMMENDED. With EC2 as the largest spend category ($44.42/mo), a 1-year Compute '
    'Savings Plan with a $30/mo commitment would cover ~68% of compute usage at a 20% discount. '
    'This is recommended once monthly compute spend stabilizes above $50/mo for 3 consecutive months. '
    'Estimated annual savings: $106.'
)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, '3.4 Serverless Optimization Credit (18% discount)', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
pdf.para(
    'Status: OPPORTUNITY. The Customer is not currently using Lambda or API Gateway. Adding '
    'serverless workloads (e.g., event-driven processing, API backends) would unlock the Serverless '
    'Credit at 18% discount. Minimum requirement: $300/mo combined Lambda + API Gateway + DynamoDB spend.'
)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 8, '3.5 Data Analytics Credit (22% discount)', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
pdf.para(
    'Status: OPPORTUNITY. No analytics services (Redshift, EMR, Glue, Athena) detected. '
    'If the Customer plans data analytics workloads, the Data Analytics Credit provides 22% '
    'discount on combined analytics + storage spend. Minimum: $800/mo.'
)

# Section 4
pdf.section('4. SPEND PROJECTIONS & COMMITMENT TRACKING')
pdf.para(
    'Based on the observed spend trajectory and planned workload expansion:'
)

pw = [50, 35, 35, 35, 35]
pdf.table_row(['Quarter', 'Projected', 'Cumulative', 'Target', 'Tier'], pw, bold=True)
pdf.table_row(['Q1 2026 (Actual)', '$837', '$837', '$1,250', 'Tier 1'], pw)
pdf.table_row(['Q2 2026', '$400', '$1,237', '$2,500', 'Tier 1'], pw)
pdf.table_row(['Q3 2026', '$750', '$1,987', '$3,750', 'Tier 1'], pw)
pdf.table_row(['Q4 2026', '$1,500', '$3,487', '$5,000', 'Tier 1'], pw)
pdf.ln(4)

pdf.para(
    'Recommendation: To reach Tier 2 ($10,000 annual / 12% discount), the Customer should '
    'consider: (1) Expanding EC2 workloads or migrating dev/test environments to AWS, '
    '(2) Adding managed database services (RDS, DynamoDB), (3) Implementing serverless '
    'architectures for new applications, (4) Leveraging analytics services for business intelligence.'
)

# Section 5
pdf.add_page()
pdf.section('5. ATTESTATION REQUIREMENTS')
pdf.para(
    'To maintain EDP pricing and claim credits, the Customer must complete the following '
    'attestation activities:'
)

aw = [80, 40, 35, 35]
pdf.table_row(['Attestation', 'Frequency', 'Next Due', 'Owner'], aw, bold=True)
pdf.table_row(['Spend Commitment Review', 'Quarterly', 'Jul 1, 2026', 'Finance'], aw)
pdf.table_row(['Security Credit Verification', 'Semi-Annual', 'Jul 1, 2026', 'Security'], aw)
pdf.table_row(['Graviton Migration Progress', 'Quarterly', 'Jul 1, 2026', 'Engineering'], aw)
pdf.table_row(['Savings Plan Utilization', 'Monthly', 'May 1, 2026', 'FinOps'], aw)
pdf.table_row(['Annual Commitment Renewal', 'Annual', 'Dec 1, 2026', 'Management'], aw)
pdf.ln(4)

pdf.para(
    'Each attestation requires submission of supporting documentation including usage reports, '
    'cost allocation tags, and service utilization metrics. Late attestations may result in '
    'temporary suspension of discount pricing until compliance is restored.'
)

# Section 6
pdf.section('6. TERMS & CONDITIONS')
pdf.para(
    'a) This PPA is subject to the AWS Customer Agreement and any applicable Service Level '
    'Agreements. Discount rates are applied as credits to the Customer billing account.'
)
pdf.para(
    'b) Minimum commitment shortfall: If the Customer does not meet the annual minimum spend '
    'for the committed tier, the difference between actual spend and the tier minimum will be '
    'charged as a shortfall fee at the end of the term.'
)
pdf.para(
    'c) Credits are non-transferable and apply only to the specified AWS account(s). '
    'Multi-account consolidation under AWS Organizations is supported with prior approval.'
)
pdf.para(
    'd) AWS reserves the right to modify eligible service lists with 90 days written notice. '
    'The Customer will be notified of any changes via the registered contact email.'
)

# Signatures
pdf.ln(8)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(95, 6, 'For Customer: Acme Cloud Solutions Ltd.')
pdf.cell(95, 6, 'For AWS: Amazon Web Services, Inc.', new_x='LMARGIN', new_y='NEXT')
pdf.ln(12)
pdf.set_font('Helvetica', '', 10)
pdf.cell(95, 6, '________________________________')
pdf.cell(95, 6, '________________________________', new_x='LMARGIN', new_y='NEXT')
pdf.cell(95, 6, 'Authorized Signatory')
pdf.cell(95, 6, 'AWS Commercial Team', new_x='LMARGIN', new_y='NEXT')
pdf.cell(95, 6, f'Date: {datetime.now().strftime("%B %d, %Y")}')
pdf.cell(95, 6, f'Date: {datetime.now().strftime("%B %d, %Y")}', new_x='LMARGIN', new_y='NEXT')

out = '/home/omarjam/commitment-intelligent-platform/serverless/acme_ppa_edp_2026.pdf'
pdf.output(out)
print(f'Generated: {out}')
