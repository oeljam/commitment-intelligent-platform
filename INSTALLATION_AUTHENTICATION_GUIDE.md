# 🔐 Installation & Authentication Guide

## 📦 Installation Methods

### Method 1: Quick Install (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/company/commitment-intelligent-platform.git
cd commitment-intelligent-platform-v0.3

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure authentication (see below)
# 4. Start platform
python3 complete_intelligent_dashboard.py
```

### Method 2: Docker Install
```bash
# 1. Pull image
docker pull company/commitment-platform:v0.3

# 2. Run with environment variables
docker run -p 5000:5000 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  company/commitment-platform:v0.3
```

### Method 3: AWS ECS Deploy
```bash
# 1. Deploy CloudFormation template
aws cloudformation deploy \
  --template-file deployment/ecs-template.yaml \
  --stack-name commitment-platform \
  --capabilities CAPABILITY_IAM

# 2. Update task definition with your AWS credentials
```

## 🔐 Authentication Setup

### 1. AWS Authentication (REQUIRED)

#### Option A: AWS CLI Configuration
```bash
# Configure AWS credentials
aws configure
# AWS Access Key ID: [Enter your key]
# AWS Secret Access Key: [Enter your secret]
# Default region: us-east-1
# Default output format: json

# Verify connection
aws sts get-caller-identity
```

#### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

#### Option C: IAM Role (Production)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetDimensionValues",
                "ce:GetUsageReport",
                "ce:ListCostCategoryDefinitions"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. MCP Server Authentication

#### AWS Billing MCP Server (Port 3010)
```bash
# Start with AWS credentials
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
python3 mcp-servers/aws_billing_server.py --port 3010
```

#### Outlook Calendar MCP Server (Port 3011)
```bash
# Microsoft Graph API credentials
export OUTLOOK_CLIENT_ID="your_client_id"
export OUTLOOK_CLIENT_SECRET="your_client_secret"
export OUTLOOK_TENANT_ID="your_tenant_id"
python3 mcp-servers/outlook_calendar_server.py --port 3011
```

#### Document Processing MCP Server (Port 3012)
```bash
# No external auth required - processes local files
python3 mcp-servers/document_processing_server.py --port 3012
```

#### Learning Analytics MCP Server (Port 3013)
```bash
# Database connection
export DATABASE_URL="postgresql://user:pass@host:port/db"
python3 mcp-servers/learning_analytics_server.py --port 3013
```

#### Notification MCP Server (Port 3014)
```bash
# Multi-channel notification credentials
export SMTP_SERVER="smtp.company.com"
export SMTP_USERNAME="notifications@company.com"
export SMTP_PASSWORD="your_password"
export SLACK_BOT_TOKEN="xoxb-..."
export TEAMS_WEBHOOK_URL="https://company.webhook.office.com/..."
python3 mcp-servers/notification_server.py --port 3014
```

## 🔧 Configuration Files

### 1. Main Application Config
```python
# config.py
import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # AWS settings
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # MCP server endpoints
    MCP_SERVERS = {
        'aws_billing': os.environ.get('AWS_BILLING_MCP', 'http://localhost:3010'),
        'outlook_calendar': os.environ.get('OUTLOOK_MCP', 'http://localhost:3011'),
        'document_processing': os.environ.get('DOC_PROCESSING_MCP', 'http://localhost:3012'),
        'learning_analytics': os.environ.get('LEARNING_MCP', 'http://localhost:3013'),
        'notification': os.environ.get('NOTIFICATION_MCP', 'http://localhost:3014')
    }
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///commitment_platform.db')
```

### 2. Environment File (.env)
```bash
# .env file (create in project root)
SECRET_KEY=your-secret-key-here
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# MCP Server URLs (if different from defaults)
AWS_BILLING_MCP=http://localhost:3010
OUTLOOK_MCP=http://localhost:3011
DOC_PROCESSING_MCP=http://localhost:3012
LEARNING_MCP=http://localhost:3013
NOTIFICATION_MCP=http://localhost:3014

# Database
DATABASE_URL=postgresql://user:pass@host:port/commitment_platform

# Microsoft Graph (for Outlook integration)
OUTLOOK_CLIENT_ID=your_client_id
OUTLOOK_CLIENT_SECRET=your_client_secret
OUTLOOK_TENANT_ID=your_tenant_id

# Notification services
SMTP_SERVER=smtp.company.com
SMTP_USERNAME=notifications@company.com
SMTP_PASSWORD=your_password
SLACK_BOT_TOKEN=xoxb-...
TEAMS_WEBHOOK_URL=https://company.webhook.office.com/...
```

## 🚀 Step-by-Step Installation

### Step 1: Prerequisites
```bash
# Check Python version (3.8+ required)
python3 --version

# Check pip
pip3 --version

# Check AWS CLI (optional but recommended)
aws --version
```

### Step 2: Download Platform
```bash
# Option A: Git clone
git clone https://github.com/company/commitment-intelligent-platform.git
cd commitment-intelligent-platform-v0.3

# Option B: Download ZIP
wget https://github.com/company/commitment-platform/archive/v0.3.zip
unzip v0.3.zip
cd commitment-intelligent-platform-v0.3
```

### Step 3: Install Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(flask|boto3|pdfplumber)"
```

### Step 4: Configure Authentication
```bash
# Create .env file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor

# Configure AWS credentials
aws configure  # Follow prompts
```

### Step 5: Start MCP Servers
```bash
# Start in separate terminals or use screen/tmux

# Terminal 1: AWS Billing MCP
python3 mcp-servers/aws_billing_server.py --port 3010

# Terminal 2: Outlook Calendar MCP (if available)
python3 mcp-servers/outlook_calendar_server.py --port 3011

# Add other MCP servers as they become available
```

### Step 6: Start Main Application
```bash
# In main terminal
python3 complete_intelligent_dashboard.py

# Should see:
# * Running on http://127.0.0.1:5000
# * Debug mode: on
```

### Step 7: Verify Installation
```bash
# Test main application
curl http://localhost:5000

# Test MCP servers
curl http://localhost:3010/health
curl http://localhost:3011/health

# Open browser
open http://localhost:5000
```

## 🔒 Security Best Practices

### 1. Credential Management
```bash
# Never commit credentials to git
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore

# Use AWS IAM roles in production
# Use environment variables, not hardcoded values
# Rotate credentials regularly
```

### 2. Network Security
```bash
# Use HTTPS in production
export FLASK_ENV=production
export SSL_CERT_PATH="/path/to/cert.pem"
export SSL_KEY_PATH="/path/to/key.pem"

# Restrict MCP server access
# Use firewall rules to limit port access
# Consider VPN for internal MCP servers
```

### 3. Application Security
```python
# Enable CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Set secure headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## 🧪 Testing Installation

### 1. Health Check Script
```python
# test_installation.py
import requests
import sys

def test_main_app():
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def test_mcp_servers():
    servers = {
        'AWS Billing': 'http://localhost:3010/health',
        'Outlook Calendar': 'http://localhost:3011/health',
        'Document Processing': 'http://localhost:3012/health',
        'Learning Analytics': 'http://localhost:3013/health',
        'Notification': 'http://localhost:3014/health'
    }
    
    results = {}
    for name, url in servers.items():
        try:
            response = requests.get(url, timeout=5)
            results[name] = response.status_code == 200
        except:
            results[name] = False
    
    return results

if __name__ == "__main__":
    print("🧪 Testing Commitment Platform Installation...")
    
    # Test main app
    if test_main_app():
        print("✅ Main application: HEALTHY")
    else:
        print("❌ Main application: FAILED")
        sys.exit(1)
    
    # Test MCP servers
    mcp_results = test_mcp_servers()
    for name, status in mcp_results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}: {'HEALTHY' if status else 'OFFLINE'}")
    
    print("\n🎉 Installation test complete!")
```

### 2. Run Tests
```bash
# Run installation test
python3 test_installation.py

# Run unit tests (if available)
python3 -m pytest tests/

# Test AWS connection
python3 -c "import boto3; print(boto3.client('ce').get_cost_and_usage(TimePeriod={'Start':'2024-01-01','End':'2024-01-02'},Granularity='DAILY',Metrics=['BlendedCost']))"
```

## 🆘 Troubleshooting

### Common Issues

#### 1. AWS Authentication Failed
```bash
# Check credentials
aws sts get-caller-identity

# Check permissions
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-02 --granularity DAILY --metrics BlendedCost

# Fix: Update credentials or add Cost Explorer permissions
```

#### 2. MCP Server Connection Failed
```bash
# Check if server is running
netstat -tlnp | grep :3010

# Check logs
tail -f mcp-servers/aws_billing_server.log

# Fix: Restart MCP server with correct credentials
```

#### 3. Port Already in Use
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python3 complete_intelligent_dashboard.py --port 5001
```

#### 4. Permission Denied
```bash
# Check file permissions
ls -la complete_intelligent_dashboard.py

# Fix permissions
chmod +x complete_intelligent_dashboard.py

# Check Python path
which python3
```

## 📞 Support

### Installation Support
- **Documentation**: This guide + README.md
- **GitHub Issues**: Report installation problems
- **Slack**: #commitment-platform-support

### Authentication Support
- **AWS IAM**: Contact your AWS administrator
- **Microsoft Graph**: Contact your Office 365 administrator
- **Internal APIs**: Contact platform team

---

**🔐 Security Note**: Never share credentials or commit them to version control. Use environment variables and proper secret management in production.
