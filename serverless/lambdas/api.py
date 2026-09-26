"""Commitment Intelligent Platform — Customer API
Upload PPA/MACC/EDP documents, analyze with Bedrock AI against live Cost Explorer spend."""
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
AI_SERVICES = os.environ.get('AI_SERVICES', 'Amazon Bedrock,Amazon SageMaker,Amazon SageMaker AI,AWS Trainium,AWS Inferentia').split(',')

table = ddb.Table(TABLE)

def resp(status, body):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(body, default=str)}


# --- Upload PDF ---
def handle_upload(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', f'{uuid.uuid4()}.pdf')
        key = f'uploads/{uuid.uuid4()}/{filename}'
        url = s3.generate_presigned_url('put_object', Params={'Bucket': BUCKET, 'Key': key, 'ContentType': 'application/pdf'}, ExpiresIn=300)
        doc_id = str(uuid.uuid4())
        table.put_item(Item={'PK': 'DOC', 'SK': doc_id, 'filename': filename, 's3_key': key, 'status': 'uploaded', 'uploaded_at': datetime.utcnow().isoformat()})
        return resp(200, {'upload_url': url, 'doc_id': doc_id, 's3_key': key})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Fetch spend from Cost Explorer ---
def _get_spend_summary(account_id=None):
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        now = datetime.utcnow()
        month_start = f'{now.year}-{now.month:02d}-01'
        year_start = f'{now.year}-01-01'
        today = now.strftime('%Y-%m-%d')

        ce_filter = {'Not': {'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Credit', 'Refund', 'Tax']}}}
        if account_id:
            accts = account_id.split(',') if isinstance(account_id, str) else [account_id]
            ce_filter = {'And': [ce_filter, {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': accts}}]}

        ytd = ce.get_cost_and_usage(TimePeriod={'Start': year_start, 'End': today}, Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter)
        total = sum(float(r['Total']['AmortizedCost']['Amount']) for r in ytd['ResultsByTime'])

        by_svc = ce.get_cost_and_usage(TimePeriod={'Start': month_start, 'End': today}, Granularity='MONTHLY', Metrics=['AmortizedCost'], Filter=ce_filter, GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
        services = {}
        for r in by_svc['ResultsByTime']:
            for g in r['Groups']:
                cost = float(g['Metrics']['AmortizedCost']['Amount'])
                if cost > 0.01:
                    services[g['Keys'][0]] = round(cost, 2)

        ai_spend = sum(v for k, v in services.items() if any(ai.lower() in k.lower() for ai in AI_SERVICES))
        return {'ytd_spend': round(total, 2), 'current_month_by_service': services, 'ai_spend': round(ai_spend, 2), 'source': 'cost_explorer'}
    except Exception:
        return {'ytd_spend': 'unavailable', 'current_month_by_service': {}, 'source': 'error'}


# --- Analyze: async trigger ---
def handle_analyze(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        doc_id = body.get('doc_id')
        s3_key = body.get('s3_key')
        analysis_id = str(uuid.uuid4())
        table.update_item(Key={'PK': 'DOC', 'SK': doc_id}, UpdateExpression='SET #s = :s, analysis_id = :a', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'processing', ':a': analysis_id})
        boto3.client('lambda').invoke(
            FunctionName=os.environ.get('ANALYZE_WORKER_ARN', ''),
            InvocationType='Event',
            Payload=json.dumps({'doc_id': doc_id, 's3_key': s3_key, 'analysis_id': analysis_id})
        )
        return resp(200, {'analysis_id': analysis_id, 'status': 'processing'})
    except Exception as e:
        return resp(500, {'error': str(e)})


def _repair_json(text):
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    fixed = text.rstrip().rstrip(',')
    if fixed.count('"') % 2 == 1: fixed += '"'
    opens = fixed.count('{') - fixed.count('}')
    open_arr = fixed.count('[') - fixed.count(']')
    fixed += ']' * max(open_arr, 0) + '}' * max(opens, 0)
    try: return json.loads(fixed)
    except json.JSONDecodeError: pass
    for marker in ['},\n', '},', '}\n', '}']:
        last_pos = text.rfind(marker)
        if last_pos > len(text) * 0.3:
            candidate = text[:last_pos + 1]
            o = candidate.count('{') - candidate.count('}')
            a = candidate.count('[') - candidate.count(']')
            candidate += ']' * max(a, 0) + '}' * max(o, 0)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict): return parsed
            except json.JSONDecodeError: continue
    raise ValueError(f"Cannot parse Bedrock response (length {len(text)})")


# --- Analyze: worker ---
def handle_analyze_worker(event, context):
    try:
        doc_id, s3_key, analysis_id = event['doc_id'], event['s3_key'], event['analysis_id']
        pdf_bytes = s3.get_object(Bucket=BUCKET, Key=s3_key)['Body'].read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode()

        acct_result = table.get_item(Key={'PK': 'CONFIG', 'SK': 'ACCOUNTS'})
        accounts = json.loads(acct_result['Item']['data']) if 'Item' in acct_result else None
        spend = _get_spend_summary(account_id=accounts)

        hist_result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('HISTORY'), ScanIndexForward=False, Limit=20)
        history_ctx = ''
        if hist_result['Items']:
            decisions = [f"- {h.get('action','').upper()}: {h.get('rec_id','')} — {h.get('notes','')}" for h in hist_result['Items']]
            history_ctx = f"\n\nPAST USER DECISIONS:\n{chr(10).join(decisions)}"

        prompt = f"""You are a cloud commitment tracking expert. Analyze the attached PPA/MACC/EDP document AND the customer's live spend data.

The spend data uses amortized cost, excluding tax/credits/refunds.{history_ctx}

AI SERVICE DEFINITIONS: {', '.join(AI_SERVICES)}
Current AI spend: ${spend.get('ai_spend', 0)}

LIVE SPEND DATA (source: {spend.get('source', 'unknown')}):
- YTD Spend: ${spend['ytd_spend']}
- Current month by service: {json.dumps(spend['current_month_by_service'], indent=2)}

Analyze for:
1. CREDIT PROGRAMS — identify all credit buckets with qualification status and max values
2. SPENDING COMMITMENTS — multi-year targets per contract year
3. GOVERNANCE — attestation requirements with deadlines

For each credit program, include a what-if scenario showing how to improve qualification.

Return JSON with keys: "recommendations" (array), "attestations" (array), "commitment_summary" (object).

Each recommendation: id, title, credit_type, workload, usage_pattern, qualification ("qualified"/"partially_qualified"/"not_qualified"), max_credit_value (number), current_progress (number), attestation_window, potential_savings (number), confidence, reasoning, what_if (scenario, new_savings, effort).

Each attestation: id, name, category, frequency, next_due (YYYY-MM-DD), owner, description, fields (array with label, type, auto_source).

commitment_summary: contract_start, contract_end, total_commitment, years (array with year, label, start, end, minimum_commitment), discount_rate.

Return ONLY the JSON object. Keep text fields concise."""

        bedrock_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31", "max_tokens": 32768,
            "messages": [{"role": "user", "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": prompt}
            ]}]
        })

        bedrock_resp = bedrock.invoke_model(modelId=MODEL, body=bedrock_body, contentType='application/json')
        result = json.loads(bedrock_resp['body'].read())
        ai_text = result['content'][0]['text'].strip()
        if ai_text.startswith('```'): ai_text = ai_text.split('\n', 1)[1] if '\n' in ai_text else ai_text[3:]
        if ai_text.rstrip().endswith('```'): ai_text = ai_text.rstrip()[:-3].strip()

        parsed = _repair_json(ai_text)
        if isinstance(parsed, list): recommendations, attestations, commitment_summary = parsed, [], {}
        else: recommendations, attestations, commitment_summary = parsed.get('recommendations', []), parsed.get('attestations', []), parsed.get('commitment_summary', {})

        now = datetime.utcnow().isoformat()
        for rec in recommendations:
            rec_id = rec.get('id', str(uuid.uuid4()))
            item = {'PK': f'ANALYSIS#{analysis_id}', 'SK': f'REC#{rec_id}', 'doc_id': doc_id, 'status': 'pending', 'created_at': now}
            for k, v in rec.items():
                item[k] = json.dumps(v) if isinstance(v, (dict, list)) else str(v) if isinstance(v, (int, float)) else v
            table.put_item(Item=item)

        for att in attestations:
            att_id = att.get('id', str(uuid.uuid4()))
            table.put_item(Item={'PK': f'ATTESTATION#{analysis_id}', 'SK': f'ATT#{att_id}', 'doc_id': doc_id, 'status': 'pending', 'created_at': now,
                **{k: json.dumps(v) if isinstance(v, (list, dict)) else str(v) if isinstance(v, (int, float)) else v for k, v in att.items()}})

        if commitment_summary:
            table.put_item(Item={'PK': f'ANALYSIS#{analysis_id}', 'SK': 'COMMITMENT_SUMMARY', 'doc_id': doc_id, 'created_at': now, 'data': json.dumps(commitment_summary)})

        table.update_item(Key={'PK': 'DOC', 'SK': doc_id}, UpdateExpression='SET #s = :s, analysis_id = :a', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'analyzed', ':a': analysis_id})
        return {'analysis_id': analysis_id, 'status': 'complete', 'recommendations': len(recommendations)}
    except Exception as e:
        try:
            if event.get('doc_id'):
                table.update_item(Key={'PK': 'DOC', 'SK': event['doc_id']}, UpdateExpression='SET #s = :s, #e = :e', ExpressionAttributeNames={'#s': 'status', '#e': 'error'}, ExpressionAttributeValues={':s': 'error', ':e': str(e)[:500]})
        except: pass
        raise


# --- Recommendations ---
def handle_recommendations(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        analysis_id = params.get('analysis_id')
        if not analysis_id:
            docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'), ScanIndexForward=False)
            analyzed = [d for d in docs['Items'] if d.get('analysis_id')]
            if not analyzed: return resp(200, {'recommendations': []})
            doc = analyzed[-1]; analysis_id = doc['analysis_id']
        else:
            docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'))
            doc = next((d for d in docs['Items'] if d.get('analysis_id') == analysis_id), {})

        status = doc.get('status', 'unknown')
        if status == 'processing': return resp(200, {'status': 'processing', 'analysis_id': analysis_id})
        if status == 'error': return resp(200, {'status': 'error', 'error': doc.get('error', 'Analysis failed')})

        result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ANALYSIS#{analysis_id}') & boto3.dynamodb.conditions.Key('SK').begins_with('REC#'))
        recs = result['Items']
        for r in recs:
            for k in ('what_if',):
                if isinstance(r.get(k), str):
                    try: r[k] = json.loads(r[k])
                    except: pass

        commitment = {}
        try:
            cs = table.get_item(Key={'PK': f'ANALYSIS#{analysis_id}', 'SK': 'COMMITMENT_SUMMARY'})
            if 'Item' in cs: commitment = json.loads(cs['Item'].get('data', '{}'))
        except: pass

        return resp(200, {'status': 'complete', 'analysis_id': analysis_id, 'recommendations': recs, 'commitment_summary': commitment})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Decision ---
def handle_decision(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        analysis_id, rec_id, action = body['analysis_id'], body['rec_id'], body['action']
        table.update_item(Key={'PK': f'ANALYSIS#{analysis_id}', 'SK': f'REC#{rec_id}'}, UpdateExpression='SET #s = :s, decided_at = :d',
            ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': action, ':d': datetime.utcnow().isoformat()})
        table.put_item(Item={'PK': 'HISTORY', 'SK': f'{datetime.utcnow().isoformat()}#{rec_id}', 'analysis_id': analysis_id, 'rec_id': rec_id, 'action': action, 'notes': body.get('notes', '')})
        return resp(200, {'status': action, 'rec_id': rec_id})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- History ---
def handle_history(event, context):
    try:
        result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('HISTORY'), ScanIndexForward=False)
        return resp(200, {'history': result['Items']})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Spend ---
def handle_spend(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        account_id = params.get('account_id')
        spend = _get_spend_summary(account_id)
        return resp(200, spend)
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Attestations ---
def handle_attestations(event, context):
    try:
        method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        params = event.get('queryStringParameters') or {}

        if method == 'GET':
            analysis_id = params.get('analysis_id')
            if not analysis_id:
                docs = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('DOC'), ScanIndexForward=False)
                analyzed = [d for d in docs['Items'] if d.get('analysis_id')]
                if not analyzed: return resp(200, {'attestations': []})
                analysis_id = analyzed[-1]['analysis_id']

            result = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(f'ATTESTATION#{analysis_id}') & boto3.dynamodb.conditions.Key('SK').begins_with('ATT#'))
            atts = result['Items']
            spend = _get_spend_summary()
            for a in atts:
                if isinstance(a.get('fields'), str):
                    try: a['fields'] = json.loads(a['fields'])
                    except: pass
                for f in (a.get('fields') or []):
                    src = f.get('auto_source')
                    if not src: continue
                    if src == 'ce_ytd_spend': f['auto_value'] = spend.get('ytd_spend', '')
                    elif src == 'ce_service_count': f['auto_value'] = len(spend.get('current_month_by_service', {}))
                    elif src.startswith('ce_service:'):
                        svc_name = src.split(':', 1)[1]
                        f['auto_value'] = next((v for k, v in spend.get('current_month_by_service', {}).items() if svc_name.lower() in k.lower()), '')
            return resp(200, {'attestations': atts, 'analysis_id': analysis_id})

        body = json.loads(event.get('body', '{}'))
        analysis_id, att_id, action = body['analysis_id'], body['att_id'], body.get('action', 'update')
        update_expr = 'SET #s = :s, updated_at = :u'
        expr_vals = {':s': 'completed' if action == 'complete' else 'in_progress', ':u': datetime.utcnow().isoformat()}
        if body.get('filled_fields'): update_expr += ', filled_fields = :f'; expr_vals[':f'] = json.dumps(body['filled_fields'])
        table.update_item(Key={'PK': f'ATTESTATION#{analysis_id}', 'SK': f'ATT#{att_id}'}, UpdateExpression=update_expr,
            ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues=expr_vals)
        return resp(200, {'status': 'updated', 'att_id': att_id})
    except Exception as e:
        return resp(500, {'error': str(e)})


# --- Accounts Config ---
def handle_accounts(event, context):
    try:
        method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        if method == 'GET':
            result = table.get_item(Key={'PK': 'CONFIG', 'SK': 'ACCOUNTS'})
            return resp(200, {'accounts': json.loads(result['Item']['data']) if 'Item' in result else []})
        body = json.loads(event.get('body', '{}'))
        table.put_item(Item={'PK': 'CONFIG', 'SK': 'ACCOUNTS', 'data': json.dumps(body.get('accounts', []))})
        return resp(200, {'status': 'saved'})
    except Exception as e:
        return resp(500, {'error': str(e)})
