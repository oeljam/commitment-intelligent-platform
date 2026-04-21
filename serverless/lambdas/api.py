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


# --- Analyze with Bedrock ---
def handle_analyze(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        doc_id = body.get('doc_id')
        s3_key = body.get('s3_key')

        # Get PDF from S3
        pdf_obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
        pdf_bytes = pdf_obj['Body'].read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode()

        # Send to Bedrock for analysis
        prompt = """Analyze this PDF document for AWS commitment and credit qualification opportunities.

Return a JSON array of recommendations. Each recommendation must have:
- id: unique string
- title: short descriptive title
- workload: what AWS workload this covers
- usage_pattern: observed usage pattern
- qualification: "qualified", "partially_qualified", or "not_qualified"
- credit_type: type of AWS credit (e.g. "Reserved Instance", "Savings Plan", "Graviton", "Serverless")
- potential_savings: estimated annual savings as a number
- confidence: "high", "medium", or "low"
- reasoning: 2-3 sentence explanation

Return ONLY the JSON array, no other text."""

        bedrock_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
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

        # Parse recommendations from AI response
        # Strip markdown code fences if present
        cleaned = ai_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        recommendations = json.loads(cleaned)

        # Store in DynamoDB
        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        for rec in recommendations:
            rec_id = rec.get('id', str(uuid.uuid4()))
            table.put_item(Item={
                'PK': f'ANALYSIS#{analysis_id}', 'SK': f'REC#{rec_id}',
                'doc_id': doc_id, 'status': 'pending', 'created_at': now,
                **{k: str(v) if isinstance(v, (int, float)) else v for k, v in rec.items()}
            })

        # Update doc status
        table.update_item(Key={'PK': 'DOC', 'SK': doc_id}, UpdateExpression='SET #s = :s, analysis_id = :a', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'analyzed', ':a': analysis_id})

        return resp(200, {'analysis_id': analysis_id, 'recommendations': recommendations})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Get Recommendations ---
def handle_recommendations(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        analysis_id = params.get('analysis_id')

        if analysis_id:
            result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ANALYSIS#{analysis_id}') & boto3.dynamodb.conditions.Key('SK').begins_with('REC#'))
        else:
            # Get latest analysis
            docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'), ScanIndexForward=False)
            analyzed = [d for d in docs['Items'] if d.get('analysis_id')]
            if not analyzed:
                return resp(200, {'recommendations': []})
            aid = analyzed[-1]['analysis_id']
            result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ANALYSIS#{aid}') & boto3.dynamodb.conditions.Key('SK').begins_with('REC#'))

        return resp(200, {'recommendations': result['Items']})
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


# --- Live Spend Data from Cost Explorer ---
def handle_spend(event, context):
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        now = datetime.utcnow()
        year_start = f'{now.year}-01-01'
        today = now.strftime('%Y-%m-%d')
        month_start = f'{now.year}-{now.month:02d}-01'

        # Monthly spend breakdown for the year
        monthly = ce.get_cost_and_usage(
            TimePeriod={'Start': year_start, 'End': today},
            Granularity='MONTHLY', Metrics=['BlendedCost']
        )
        months = [{'period': r['TimePeriod']['Start'][:7], 'spend': float(r['Total']['BlendedCost']['Amount'])} for r in monthly['ResultsByTime']]
        total_spend = sum(m['spend'] for m in months)

        # Spend by service (current month)
        by_service = ce.get_cost_and_usage(
            TimePeriod={'Start': month_start, 'End': today},
            Granularity='MONTHLY', Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        services = {}
        for r in by_service['ResultsByTime']:
            for g in r['Groups']:
                cost = float(g['Metrics']['BlendedCost']['Amount'])
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
