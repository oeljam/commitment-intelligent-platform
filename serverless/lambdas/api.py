"""Commitment Intelligent Platform - Lambda API handlers"""
import json, os, uuid, base64, boto3
from datetime import datetime
from decimal import Decimal

s3 = boto3.client('s3')
ddb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
ses = boto3.client('ses')

TABLE = os.environ['TABLE_NAME']
BUCKET = os.environ['DOCUMENTS_BUCKET']
SENDER = os.environ['SENDER_EMAIL']
MODEL = os.environ['BEDROCK_MODEL_ID']

table = ddb.Table(TABLE)

def resp(status, body):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(body, default=str)}


# --- Upload PDF ---
def handle_upload(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', f'{uuid.uuid4()}.pdf')
        content_type = body.get('content_type', 'application/pdf')
        key = f'uploads/{uuid.uuid4()}/{filename}'

        url = s3.generate_presigned_url('put_object', Params={'Bucket': BUCKET, 'Key': key, 'ContentType': content_type}, ExpiresIn=300)

        # Track document in DynamoDB
        doc_id = str(uuid.uuid4())
        table.put_item(Item={'PK': 'DOC', 'SK': doc_id, 'filename': filename, 's3_key': key, 'status': 'uploaded', 'uploaded_at': datetime.utcnow().isoformat()})

        return resp(200, {'upload_url': url, 'doc_id': doc_id, 's3_key': key})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Fetch live spend summary for Bedrock context ---
def _get_spend_summary():
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        now = datetime.utcnow()
        month_start = f'{now.year}-{now.month:02d}-01'
        year_start = f'{now.year}-01-01'
        today = now.strftime('%Y-%m-%d')

        # Exclude tax, credits, refunds — use amortized cost (matches real PPA tracking)
        ce_filter = {'Not': {'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Credit', 'Refund', 'Tax']}}}

        ytd = ce.get_cost_and_usage(TimePeriod={'Start': year_start, 'End': today}, Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter)
        total = sum(float(r['Total']['AmortizedCost']['Amount']) for r in ytd['ResultsByTime'])

        by_svc = ce.get_cost_and_usage(TimePeriod={'Start': month_start, 'End': today}, Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter, GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
        services = {}
        for r in by_svc['ResultsByTime']:
            for g in r['Groups']:
                cost = float(g['Metrics']['AmortizedCost']['Amount'])
                if cost > 0.01:
                    services[g['Keys'][0]] = round(cost, 2)

        return {'ytd_spend': round(total, 2), 'current_month_by_service': services}
    except Exception:
        return {'ytd_spend': 'unavailable', 'current_month_by_service': {}}


# --- Analyze: async trigger ---
def handle_analyze(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        doc_id = body.get('doc_id')
        s3_key = body.get('s3_key')
        analysis_id = str(uuid.uuid4())

        # Mark as processing
        table.update_item(Key={'PK': 'DOC', 'SK': doc_id}, UpdateExpression='SET #s = :s, analysis_id = :a', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'processing', ':a': analysis_id})

        # Invoke worker async
        boto3.client('lambda').invoke(
            FunctionName=os.environ.get('ANALYZE_WORKER_ARN', context.function_name.replace('AnalyzeFunction', 'AnalyzeWorkerFunction')),
            InvocationType='Event',
            Payload=json.dumps({'doc_id': doc_id, 's3_key': s3_key, 'analysis_id': analysis_id})
        )
        return resp(200, {'analysis_id': analysis_id, 'status': 'processing'})
    except Exception as e:
        return resp(500, {'error': str(e)})


def _repair_json(text):
    """Attempt to parse JSON, repairing truncation if needed."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try closing open braces/brackets
    fixed = text.rstrip().rstrip(',')
    # Close any open string
    if fixed.count('"') % 2 == 1:
        fixed += '"'
    # Close open structures
    opens = fixed.count('{') - fixed.count('}')
    open_arr = fixed.count('[') - fixed.count(']')
    fixed += ']' * max(open_arr, 0)
    fixed += '}' * max(opens, 0)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    # Progressively trim from the end and try to close
    for trim in range(1, 200):
        candidate = text[:-(trim)].rstrip().rstrip(',').rstrip(':')
        if candidate.count('"') % 2 == 1:
            candidate += '"'
        o = candidate.count('{') - candidate.count('}')
        a = candidate.count('[') - candidate.count(']')
        candidate += ']' * max(a, 0)
        candidate += '}' * max(o, 0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Cannot parse Bedrock response (length {len(text)})")


# --- Analyze: worker (invoked async) ---
def handle_analyze_worker(event, context):
    try:
        doc_id = event['doc_id']
        s3_key = event['s3_key']
        analysis_id = event['analysis_id']

        # Get PDF from S3
        pdf_obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
        pdf_bytes = pdf_obj['Body'].read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode()

        # Get live spend from Cost Explorer
        spend = _get_spend_summary()

        # Get past decision history for learning loop
        hist_result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('HISTORY'), ScanIndexForward=False, Limit=20)
        history_ctx = ''
        if hist_result['Items']:
            decisions = [f"- {h.get('action','').upper()}: {h.get('rec_id','')} — {h.get('notes','no notes')}" for h in hist_result['Items']]
            history_ctx = f"""

PAST USER DECISIONS (learn from these — prioritize credit types the user accepted, deprioritize rejected ones):
{chr(10).join(decisions)}"""

        prompt = f"""You are an AWS PPA/EDP commitment tracking expert. Analyze the attached PPA/EDP document AND the customer's live AWS spend data.

The spend data uses amortized cost, excluding tax/credits/refunds. Marketplace purchases are included.{history_ctx}

LIVE AWS SPEND DATA:
- YTD Spend: ${spend['ytd_spend']}
- Current month by service: {json.dumps(spend['current_month_by_service'], indent=2)}

Analyze the PPA document for these real-world PPA structures:

1. CREDIT BUCKETS — PPA/EDP agreements typically have outcome-based credit programs such as:
   - GenAI POC/Adoption credits (Bedrock, SageMaker, GPU usage)
   - Growth Investment credits (tiered spend thresholds per contract year)
   - Graviton Adoption credits (% of EC2 on Graviton instances)
   - Serverless Innovation/Modernization credits (regional deployments)
   - New Region Expansion credits
   - Any other credit programs in the document

2. SPENDING COMMITMENTS — Multi-year minimum spend per contract year, with calculation methods (fixed, % of prior year actual)

3. GOVERNANCE — Attestation requirements, compliance deadlines, case studies, executive engagements

For each credit bucket found, think through what-if scenarios: if the customer shifted or increased spend, would they unlock or improve credit qualification?

Return a JSON object with three keys: "recommendations", "attestations", and "commitment_summary".

"recommendations" — array, one per credit bucket or opportunity found. Each has:
- id: unique string
- title: credit program name
- credit_type: category (e.g. "GenAI POC", "GenAI Adoption", "Growth Investment", "Graviton Adoption", "Serverless", "New Region", "Savings Plan", "Security")
- workload: AWS services involved
- usage_pattern: what the live spend data shows for relevant services
- qualification: "qualified", "partially_qualified", or "not_qualified"
- max_credit_value: maximum credit amount available (number, from the PPA)
- current_progress: estimated current progress toward qualification (number, dollar amount)
- attestation_window: start and end dates for claiming this credit (e.g. "Mar 2025 - Mar 2028")
- potential_savings: estimated credit value achievable based on current trajectory (number)
- confidence: "high", "medium", or "low"
- reasoning: 2-3 sentences cross-referencing live spend against PPA requirements
- what_if: object with:
    - scenario: one sentence describing the change
    - spend_change: object mapping service names to new monthly spend amounts
    - new_qualification: resulting qualification status
    - new_savings: estimated credit value after the change
    - effort: "low", "medium", or "high"

"attestations" — array of governance/compliance requirements. Each has:
- id: unique string
- name: requirement name
- category: "governance" or "credit_attestation"
- frequency: "Monthly", "Quarterly", "Semi-Annual", "Annual", or "During Term"
- next_due: next due date as YYYY-MM-DD (best estimate)
- owner: responsible party
- consequence: what happens if not met
- description: what needs to be submitted
- fields: array of field objects with "label" (string), "type" ("text", "number", "date", "select"), and optionally "auto_source" — a hint for auto-populating from live data. Use these values when applicable:
    - "ce_ytd_spend" for YTD total spend
    - "ce_service:SERVICE_NAME" for a specific service spend (e.g. "ce_service:Amazon EC2")
    - "ce_service_count" for number of active services
    - null if the field must be manually filled

"commitment_summary" — object with:
- contract_start: start date YYYY-MM-DD
- contract_end: end date YYYY-MM-DD
- total_commitment: total minimum over full term (number)
- years: array of objects, each with "year" (number), "label" (e.g. "Year 1"), "start" (YYYY-MM-DD), "end" (YYYY-MM-DD), "minimum_commitment" (number), "calculation_method" (string)
- discount_rate: primary discount percentage (number, e.g. 0.25)
- adjusted_discount_rate: reduced rate if requirements not met (number or null)

Return ONLY the JSON object, no other text."""

        bedrock_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 16384,
            "messages": [
                {"role": "user", "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                    {"type": "text", "text": prompt}
                ]}
            ]
        })

        bedrock_resp = bedrock.invoke_model(modelId=MODEL, body=bedrock_body, contentType='application/json')
        result = json.loads(bedrock_resp['body'].read())
        ai_text = result['content'][0]['text']

        # Parse response
        cleaned = ai_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        parsed = _repair_json(cleaned)

        # Support both old (array) and new (object) response formats
        if isinstance(parsed, list):
            recommendations, attestations, commitment_summary = parsed, [], {}
        else:
            recommendations = parsed.get('recommendations', [])
            attestations = parsed.get('attestations', [])
            commitment_summary = parsed.get('commitment_summary', {})

        # Store in DynamoDB
        now = datetime.utcnow().isoformat()

        for rec in recommendations:
            rec_id = rec.get('id', str(uuid.uuid4()))
            # Convert all nested dicts/lists to JSON strings and numbers to strings for DynamoDB
            item = {'PK': f'ANALYSIS#{analysis_id}', 'SK': f'REC#{rec_id}', 'doc_id': doc_id, 'status': 'pending', 'created_at': now}
            for k, v in rec.items():
                if isinstance(v, (dict, list)):
                    item[k] = json.dumps(v)
                elif isinstance(v, (int, float)):
                    item[k] = str(v)
                else:
                    item[k] = v
            table.put_item(Item=item)

        for att in attestations:
            att_id = att.get('id', str(uuid.uuid4()))
            table.put_item(Item={
                'PK': f'ATTESTATION#{analysis_id}', 'SK': f'ATT#{att_id}',
                'doc_id': doc_id, 'status': 'pending', 'created_at': now,
                **{k: json.dumps(v) if isinstance(v, (list, dict)) else str(v) if isinstance(v, (int, float)) else v for k, v in att.items()}
            })

        # Store commitment summary
        if commitment_summary:
            table.put_item(Item={
                'PK': f'ANALYSIS#{analysis_id}', 'SK': 'COMMITMENT_SUMMARY',
                'doc_id': doc_id, 'created_at': now,
                'data': json.dumps(commitment_summary)
            })

        # Update doc status
        table.update_item(Key={'PK': 'DOC', 'SK': doc_id}, UpdateExpression='SET #s = :s, analysis_id = :a', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'analyzed', ':a': analysis_id})

        return {'analysis_id': analysis_id, 'status': 'complete', 'recommendations': len(recommendations), 'attestations': len(attestations)}
    except Exception as e:
        # Mark doc as failed
        try:
            if event.get('doc_id'):
                table.update_item(Key={'PK': 'DOC', 'SK': event['doc_id']}, UpdateExpression='SET #s = :s, #e = :e', ExpressionAttributeNames={'#s': 'status', '#e': 'error'}, ExpressionAttributeValues={':s': 'error', ':e': str(e)[:500]})
        except: pass
        raise


# --- Get Recommendations ---
def handle_recommendations(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        analysis_id = params.get('analysis_id')

        # If checking status of an analysis
        if not analysis_id:
            docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'), ScanIndexForward=False)
            analyzed = [d for d in docs['Items'] if d.get('analysis_id')]
            if not analyzed:
                return resp(200, {'recommendations': []})
            doc = analyzed[-1]
            analysis_id = doc['analysis_id']
        else:
            # Find the doc for this analysis
            docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'))
            doc = next((d for d in docs['Items'] if d.get('analysis_id') == analysis_id), {})

        status = doc.get('status', 'unknown')
        if status == 'processing':
            return resp(200, {'status': 'processing', 'analysis_id': analysis_id})
        if status == 'error':
            return resp(200, {'status': 'error', 'error': doc.get('error', 'Analysis failed'), 'analysis_id': analysis_id})

        result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ANALYSIS#{analysis_id}') & boto3.dynamodb.conditions.Key('SK').begins_with('REC#'))
        recs = result['Items']
        # Parse JSON fields back
        for r in recs:
            for k in ('what_if', 'spend_change'):
                if isinstance(r.get(k), str):
                    try: r[k] = json.loads(r[k])
                    except: pass

        # Get commitment summary if available
        commitment = {}
        try:
            cs = table.get_item(Key={'PK': f'ANALYSIS#{analysis_id}', 'SK': 'COMMITMENT_SUMMARY'})
            if 'Item' in cs:
                commitment = json.loads(cs['Item'].get('data', '{}'))
        except: pass

        return resp(200, {'status': 'complete', 'analysis_id': analysis_id, 'recommendations': recs, 'commitment_summary': commitment})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Accept/Reject Decision ---
def handle_decision(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        analysis_id = body['analysis_id']
        rec_id = body['rec_id']
        action = body['action']  # 'accepted' or 'rejected'
        notes = body.get('notes', '')

        # Update recommendation status
        table.update_item(
            Key={'PK': f'ANALYSIS#{analysis_id}', 'SK': f'REC#{rec_id}'},
            UpdateExpression='SET #s = :s, decision_notes = :n, decided_at = :d',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': action, ':n': notes, ':d': datetime.utcnow().isoformat()}
        )

        # Log to history
        table.put_item(Item={
            'PK': 'HISTORY', 'SK': f'{datetime.utcnow().isoformat()}#{rec_id}',
            'analysis_id': analysis_id, 'rec_id': rec_id, 'action': action, 'notes': notes
        })

        return resp(200, {'status': action, 'rec_id': rec_id})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Get History ---
def handle_history(event, context):
    try:
        result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('HISTORY'), ScanIndexForward=False)
        return resp(200, {'history': result['Items']})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Send Email ---
def handle_send_email(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        recipients = body['recipients']
        subject = body.get('subject', 'Commitment Platform - Recommendation Update')
        rec_data = body.get('recommendation', {})

        html = f"""<html><body style="font-family:Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:8px;overflow:hidden;">
<div style="background:#232F3E;color:white;padding:20px;"><h2 style="margin:0;">Commitment Intelligent Platform</h2></div>
<div style="padding:20px;">
<h3 style="color:#232F3E;">{rec_data.get('title', 'Recommendation Update')}</h3>
<div style="background:#f8f9fa;padding:15px;border-radius:5px;border-left:4px solid #FF9900;margin:15px 0;">
<p><strong>Credit Type:</strong> {rec_data.get('credit_type', 'N/A')}</p>
<p><strong>Qualification:</strong> {rec_data.get('qualification', 'N/A')}</p>
<p><strong>Potential Savings:</strong> ${rec_data.get('potential_savings', 0):,.0f}</p>
<p><strong>Status:</strong> {rec_data.get('status', 'N/A')}</p>
</div>
<p>{rec_data.get('reasoning', '')}</p>
</div>
<div style="background:#f8f9fa;padding:10px 20px;text-align:center;font-size:12px;color:#666;">
Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
</div></div></body></html>"""

        ses.send_email(
            Source=SENDER,
            Destination={'ToAddresses': recipients},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html}}
            }
        )
        return resp(200, {'message': f'Email sent to {len(recipients)} recipients'})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Attestations: list, update, complete ---
def handle_attestations(event, context):
    try:
        method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        params = event.get('queryStringParameters') or {}

        if method == 'GET':
            analysis_id = params.get('analysis_id')
            if not analysis_id:
                docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'), ScanIndexForward=False)
                analyzed = [d for d in docs['Items'] if d.get('analysis_id')]
                if not analyzed:
                    return resp(200, {'attestations': []})
                analysis_id = analyzed[-1]['analysis_id']

            result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ATTESTATION#{analysis_id}') & boto3.dynamodb.conditions.Key('SK').begins_with('ATT#'))
            atts = result['Items']

            # Fetch live spend for auto-population
            spend = _get_spend_summary()

            for a in atts:
                for k in ('fields',):
                    if isinstance(a.get(k), str):
                        try: a[k] = json.loads(a[k])
                        except: pass
                # Auto-populate fields with auto_source
                for f in (a.get('fields') or []):
                    src = f.get('auto_source')
                    if not src:
                        continue
                    if src == 'ce_ytd_spend':
                        f['auto_value'] = spend.get('ytd_spend', '')
                    elif src == 'ce_service_count':
                        f['auto_value'] = len(spend.get('current_month_by_service', {}))
                    elif src.startswith('ce_service:'):
                        svc_name = src.split(':', 1)[1]
                        svcs = spend.get('current_month_by_service', {})
                        f['auto_value'] = next((v for k, v in svcs.items() if svc_name.lower() in k.lower()), '')

            return resp(200, {'attestations': atts, 'analysis_id': analysis_id})

        # POST — update or complete attestation
        body = json.loads(event.get('body', '{}'))
        analysis_id = body['analysis_id']
        att_id = body['att_id']
        action = body.get('action', 'update')

        update_expr = 'SET #s = :s, updated_at = :u'
        expr_vals = {':s': 'completed' if action == 'complete' else 'in_progress', ':u': datetime.utcnow().isoformat()}
        expr_names = {'#s': 'status'}

        if body.get('filled_fields'):
            update_expr += ', filled_fields = :f'
            expr_vals[':f'] = json.dumps(body['filled_fields'])

        if body.get('notes'):
            update_expr += ', notes = :n'
            expr_vals[':n'] = body['notes']

        table.update_item(
            Key={'PK': f'ATTESTATION#{analysis_id}', 'SK': f'ATT#{att_id}'},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_vals
        )

        # Recurring: create next occurrence on complete
        if action == 'complete':
            att = table.get_item(Key={'PK': f'ATTESTATION#{analysis_id}', 'SK': f'ATT#{att_id}'}).get('Item', {})
            freq = att.get('frequency', '')
            due = att.get('next_due', '')
            if freq and due:
                try:
                    due_dt = datetime.strptime(due, '%Y-%m-%d')
                except: due_dt = None
                if due_dt:
                    months_add = {'Monthly': 1, 'Quarterly': 3, 'Semi-Annual': 6, 'Annual': 12}.get(freq, 0)
                    if months_add:
                        m = due_dt.month - 1 + months_add
                        y = due_dt.year + m // 12
                        m = m % 12 + 1
                        d = min(due_dt.day, [31,29 if y%4==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
                        next_due = f'{y}-{m:02d}-{d:02d}'
                        new_id = f"{att_id}-{next_due}"
                        # Copy attestation with new due date
                        new_item = {k: v for k, v in att.items() if k not in ('filled_fields', 'notes', 'updated_at')}
                        new_item['SK'] = f'ATT#{new_id}'
                        new_item['id'] = new_id
                        new_item['next_due'] = next_due
                        new_item['status'] = 'pending'
                        new_item['created_at'] = datetime.utcnow().isoformat()
                        table.put_item(Item=new_item)

        return resp(200, {'status': 'updated', 'att_id': att_id})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Attestation Reminder (EventBridge scheduled) ---
def handle_reminder(event, context):
    try:
        now = datetime.utcnow()
        week_from_now = (now.replace(day=now.day) + __import__('datetime').timedelta(days=7)).strftime('%Y-%m-%d')
        today_str = now.strftime('%Y-%m-%d')

        # Scan for pending attestations — small table so scan is fine
        result = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('PK').begins_with('ATTESTATION#') & boto3.dynamodb.conditions.Attr('status').eq('pending'))

        due_soon = [a for a in result['Items'] if a.get('next_due', '') <= week_from_now and a.get('next_due', '') >= today_str]
        if not due_soon:
            return {'sent': 0}

        rows = ''.join(f"<tr><td style='padding:8px;border-bottom:1px solid #ddd'>{a['name']}</td><td style='padding:8px;border-bottom:1px solid #ddd'>{a.get('next_due','')}</td><td style='padding:8px;border-bottom:1px solid #ddd'>{a.get('owner','')}</td><td style='padding:8px;border-bottom:1px solid #ddd'>{a.get('frequency','')}</td></tr>" for a in due_soon)

        html = f"""<html><body style="font-family:Arial,sans-serif;padding:20px">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden">
<div style="background:#232F3E;color:#fff;padding:20px"><h2 style="margin:0">⏰ Attestation Reminder</h2></div>
<div style="padding:20px">
<p>The following attestations are due within the next 7 days:</p>
<table style="border-collapse:collapse;width:100%">
<tr style="background:#FF9900;color:#fff"><th style="padding:8px;text-align:left">Attestation</th><th style="padding:8px">Due Date</th><th style="padding:8px">Owner</th><th style="padding:8px">Frequency</th></tr>
{rows}</table>
<p style="margin-top:16px">Log in to the <b>Commitment Intelligent Platform</b> to fill out and submit these attestations.</p>
</div></div></body></html>"""

        ses.send_email(
            Source=SENDER,
            Destination={'ToAddresses': [SENDER]},
            Message={'Subject': {'Data': f'⏰ {len(due_soon)} Attestation(s) Due This Week'}, 'Body': {'Html': {'Data': html}}}
        )
        return {'sent': len(due_soon)}
    except Exception as e:
        return {'error': str(e)}


# --- Live Spend Data from Cost Explorer ---
def handle_spend(event, context):
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        now = datetime.utcnow()
        year_start = f'{now.year}-01-01'
        today = now.strftime('%Y-%m-%d')
        month_start = f'{now.year}-{now.month:02d}-01'

        # Exclude tax, credits, refunds — amortized cost (PPA standard)
        ce_filter = {'Not': {'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Credit', 'Refund', 'Tax']}}}

        # Monthly spend breakdown for the year
        monthly = ce.get_cost_and_usage(
            TimePeriod={'Start': year_start, 'End': today},
            Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter
        )
        months = [{'period': r['TimePeriod']['Start'][:7], 'spend': float(r['Total']['AmortizedCost']['Amount'])} for r in monthly['ResultsByTime']]
        total_spend = sum(m['spend'] for m in months)

        # Spend by service (current month)
        by_service = ce.get_cost_and_usage(
            TimePeriod={'Start': month_start, 'End': today},
            Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter,
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        services = {}
        for r in by_service['ResultsByTime']:
            for g in r['Groups']:
                cost = float(g['Metrics']['AmortizedCost']['Amount'])
                if cost > 0.01:
                    services[g['Keys'][0]] = round(cost, 2)

        # Credit coupling analysis against services
        credit_offerings = {
            'Generative AI Credit': {'discount': '25%', 'primary': ['SageMaker', 'Bedrock', 'Lambda'], 'supporting': ['EC2', 'S3'], 'min_spend': 1000},
            'Graviton Optimization Credit': {'discount': '31%', 'primary': ['EC2'], 'supporting': ['RDS', 'ElastiCache'], 'min_spend': 500},
            'Data Analytics Credit': {'discount': '22%', 'primary': ['Redshift', 'EMR', 'Glue'], 'supporting': ['S3', 'Kinesis'], 'min_spend': 800},
            'Serverless Credit': {'discount': '18%', 'primary': ['Lambda', 'API Gateway'], 'supporting': ['DynamoDB', 'S3'], 'min_spend': 300},
        }
        couplings = []
        for name, c in credit_offerings.items():
            matched = {svc: cost for svc, cost in services.items() if any(p.lower() in svc.lower() for p in c['primary'] + c['supporting'])}
            matched_spend = sum(matched.values())
            has_primary = any(any(p.lower() in svc.lower() for p in c['primary']) for svc in services)
            status = 'qualified' if has_primary and matched_spend >= c['min_spend'] else 'partially_qualified' if has_primary else 'opportunity'
            disc = float(c['discount'].rstrip('%')) / 100
            couplings.append({'credit_name': name, 'discount': c['discount'], 'status': status, 'matched_spend': round(matched_spend, 2), 'min_spend': c['min_spend'], 'potential_savings': round(matched_spend * disc, 2), 'matched_services': matched})

        return resp(200, {'months': months, 'total_spend_ytd': round(total_spend, 2), 'current_month_services': services, 'credit_couplings': couplings})
    except Exception as e:
        return resp(500, {'error': str(e)})
