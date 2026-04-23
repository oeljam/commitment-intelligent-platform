#!/bin/bash
set -euo pipefail

# ============================================================
# Commitment Intelligent Platform - Deploy & Test
# Deploys the SAM stack, uploads the sample PDF, and exercises
# every API endpoint so you can verify end-to-end.
# Usage: ./test_platform.sh <verified-ses-email> [region]
# ============================================================

SENDER="${1:?Usage: ./test_platform.sh <ses-verified-email> [region]}"
REGION="${2:-us-east-1}"
STACK="commitment-intelligent-platform"
DIR="$(cd "$(dirname "$0")" && pwd)"
PDF="$DIR/acme_ppa_edp_2026.pdf"
PASS=0; FAIL=0

green(){ printf "\033[32m%s\033[0m\n" "$1"; }
red(){ printf "\033[31m%s\033[0m\n" "$1"; }
step(){ printf "\n\033[1;36m▶ %s\033[0m\n" "$1"; }
check(){
  local name=$1 code=$2 body=$3
  if [ "$code" -ge 200 ] && [ "$code" -lt 300 ]; then
    green "  ✅ $name (HTTP $code)"; ((PASS++))
  else
    red "  ❌ $name (HTTP $code)"; echo "     $body"; ((FAIL++))
  fi
}

# ── 1. Deploy ────────────────────────────────────────────────
step "1/7  Deploying stack ($STACK) to $REGION"
ACCT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="$STACK-deploy-$ACCT"
aws s3 mb "s3://$BUCKET" --region "$REGION" 2>/dev/null || true

aws cloudformation package \
  --template-file "$DIR/template.yaml" \
  --s3-bucket "$BUCKET" \
  --output-template-file "$DIR/.packaged.yaml" \
  --region "$REGION"

aws cloudformation deploy \
  --template-file "$DIR/.packaged.yaml" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides SenderEmail="$SENDER" \
  --region "$REGION" 2>&1 | grep -v "No changes to deploy" || true

API=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
FB=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)
DIST=$(aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[?LogicalResourceId=='CloudFrontDist'].PhysicalResourceId" --output text)
FRONTEND=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text)

green "  API:      $API"
green "  Frontend: $FRONTEND"

# ── 2. Upload frontend ──────────────────────────────────────
step "2/7  Uploading frontend"
aws s3 cp "$DIR/frontend/index.html" "s3://$FB/index.html" --content-type "text/html" --region "$REGION"
aws cloudfront create-invalidation --distribution-id "$DIST" --paths "/*" --region "$REGION" > /dev/null 2>&1 || true
green "  ✅ Frontend deployed"

# ── 3. Verify SES ───────────────────────────────────────────
step "3/7  Verifying SES sender"
aws ses verify-email-identity --email-address "$SENDER" --region "$REGION" 2>/dev/null || true
green "  ✅ Verification sent (check $SENDER inbox)"

# ── 4. Test /upload ─────────────────────────────────────────
step "4/7  POST /upload"
UPLOAD_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/upload" \
  -H "Content-Type: application/json" \
  -d '{"filename":"acme_ppa_edp_2026.pdf","content_type":"application/pdf"}')
UPLOAD_CODE=$(echo "$UPLOAD_RESP" | tail -1)
UPLOAD_BODY=$(echo "$UPLOAD_RESP" | sed '$d')
check "/upload" "$UPLOAD_CODE" "$UPLOAD_BODY"

UPLOAD_URL=$(echo "$UPLOAD_BODY" | python3 -c "import sys,json;print(json.load(sys.stdin)['upload_url'])" 2>/dev/null || echo "")
DOC_ID=$(echo "$UPLOAD_BODY" | python3 -c "import sys,json;print(json.load(sys.stdin)['doc_id'])" 2>/dev/null || echo "")
S3_KEY=$(echo "$UPLOAD_BODY" | python3 -c "import sys,json;print(json.load(sys.stdin)['s3_key'])" 2>/dev/null || echo "")

# Upload the actual PDF via presigned URL
if [ -n "$UPLOAD_URL" ] && [ -f "$PDF" ]; then
  curl -s -X PUT "$UPLOAD_URL" -H "Content-Type: application/pdf" --data-binary "@$PDF" > /dev/null
  green "  ✅ PDF uploaded to S3 via presigned URL"
fi

# ── 5. Test /analyze ────────────────────────────────────────
step "5/7  POST /analyze (Bedrock — may take 15-30s)"
ANALYZE_RESP=$(curl -s -w "\n%{http_code}" --max-time 120 -X POST "$API/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"doc_id\":\"$DOC_ID\",\"s3_key\":\"$S3_KEY\"}")
ANALYZE_CODE=$(echo "$ANALYZE_RESP" | tail -1)
ANALYZE_BODY=$(echo "$ANALYZE_RESP" | sed '$d')
check "/analyze" "$ANALYZE_CODE" "$ANALYZE_BODY"

ANALYSIS_ID=$(echo "$ANALYZE_BODY" | python3 -c "import sys,json;print(json.load(sys.stdin).get('analysis_id',''))" 2>/dev/null || echo "")
REC_COUNT=$(echo "$ANALYZE_BODY" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('recommendations',[])))" 2>/dev/null || echo "0")
green "  ℹ️  $REC_COUNT recommendations generated (analysis: $ANALYSIS_ID)"

# Get first rec ID for decision test
REC_ID=$(echo "$ANALYZE_BODY" | python3 -c "import sys,json;r=json.load(sys.stdin).get('recommendations',[]);print(r[0]['id'] if r else '')" 2>/dev/null || echo "")

# ── 6. Test /recommendations, /decision, /history, /spend ──
step "6/7  Testing remaining endpoints"

# GET /recommendations
R_RESP=$(curl -s -w "\n%{http_code}" "$API/recommendations?analysis_id=$ANALYSIS_ID")
check "GET /recommendations" "$(echo "$R_RESP" | tail -1)" "$(echo "$R_RESP" | sed '$d')"

# POST /decision
if [ -n "$REC_ID" ]; then
  D_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/decision" \
    -H "Content-Type: application/json" \
    -d "{\"analysis_id\":\"$ANALYSIS_ID\",\"rec_id\":\"$REC_ID\",\"action\":\"accepted\",\"notes\":\"Test accept\"}")
  check "POST /decision" "$(echo "$D_RESP" | tail -1)" "$(echo "$D_RESP" | sed '$d')"
fi

# GET /history
H_RESP=$(curl -s -w "\n%{http_code}" "$API/history")
check "GET /history" "$(echo "$H_RESP" | tail -1)" "$(echo "$H_RESP" | sed '$d')"

# GET /spend
S_RESP=$(curl -s -w "\n%{http_code}" "$API/spend")
S_CODE=$(echo "$S_RESP" | tail -1)
check "GET /spend" "$S_CODE" "$(echo "$S_RESP" | sed '$d')"

# POST /send-email (only if SES verified)
E_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/send-email" \
  -H "Content-Type: application/json" \
  -d "{\"recipients\":[\"$SENDER\"],\"recommendation\":{\"title\":\"Test Recommendation\",\"credit_type\":\"Savings Plan\",\"qualification\":\"qualified\",\"potential_savings\":1200,\"status\":\"accepted\",\"reasoning\":\"Automated test email.\"}}")
E_CODE=$(echo "$E_RESP" | tail -1)
check "POST /send-email" "$E_CODE" "$(echo "$E_RESP" | sed '$d')"

# ── 7. Summary ──────────────────────────────────────────────
step "7/7  Results"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
green "  Passed: $PASS"
[ "$FAIL" -gt 0 ] && red "  Failed: $FAIL" || echo "  Failed: 0"
echo ""
echo "  🌐 Frontend: $FRONTEND"
echo "  📡 API:      $API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exit "$FAIL"
