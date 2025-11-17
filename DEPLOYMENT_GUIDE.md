# Commitment Intelligent Platform - Deployment & Shipping Guide

## Production Deployment Checklist

### Pre-Deployment Requirements
- [ ] Python 3.8+ environment
- [ ] AWS credentials configured
- [ ] SSL certificates for HTTPS
- [ ] Database for learning data persistence
- [ ] Monitoring and logging setup
- [ ] Backup and recovery procedures

### Security Configuration
```bash
# Environment variables for production
export FLASK_ENV=production
export SECRET_KEY="your-secret-key"
export AWS_REGION="us-east-1"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export SSL_CERT_PATH="/path/to/cert.pem"
export SSL_KEY_PATH="/path/to/key.pem"
```

### Production Deployment Steps

#### Step 1: Server Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip nginx postgresql redis-server

# Create application user
sudo useradd -m -s /bin/bash commitment-platform
sudo su - commitment-platform

# Clone repository
git clone <repository-url>
cd commitment-intelligent-platform-v0.3
```

#### Step 2: Application Configuration
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Configure database
createdb commitment_platform
python3 setup_database.py

# Configure SSL
sudo cp ssl/cert.pem /etc/ssl/certs/
sudo cp ssl/key.pem /etc/ssl/private/
```

#### Step 3: Web Server Configuration
```nginx
# /etc/nginx/sites-available/commitment-platform
server {
    listen 443 ssl;
    server_name commitment-platform.company.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Step 4: Service Configuration
```ini
# /etc/systemd/system/commitment-platform.service
[Unit]
Description=Commitment Intelligent Platform
After=network.target

[Service]
Type=simple
User=commitment-platform
WorkingDirectory=/home/commitment-platform/commitment-intelligent-platform-v0.3
ExecStart=/usr/bin/python3 complete_intelligent_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Step 5: Start Services
```bash
# Enable and start services
sudo systemctl enable commitment-platform
sudo systemctl start commitment-platform
sudo systemctl enable nginx
sudo systemctl restart nginx

# Verify deployment
curl -k https://commitment-platform.company.com
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python3", "complete_intelligent_dashboard.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/commitment_platform
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: commitment_platform
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine

volumes:
  postgres_data:
```

## AWS Deployment (ECS/Fargate)

### Task Definition
```json
{
  "family": "commitment-platform",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/commitmentPlatformRole",
  "containerDefinitions": [
    {
      "name": "commitment-platform",
      "image": "your-account.dkr.ecr.region.amazonaws.com/commitment-platform:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/commitment-platform",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Monitoring & Observability

### Health Check Endpoint
```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '0.3.0',
        'aws_connection': check_aws_connection(),
        'database_connection': check_database_connection()
    })
```

### Logging Configuration
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/commitment-platform.log', 
                                     maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
recommendation_counter = Counter('recommendations_generated_total', 
                                'Total recommendations generated')
pdf_processing_time = Histogram('pdf_processing_seconds', 
                               'Time spent processing PDFs')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

## Customer Onboarding Automation

### Onboarding Script
```bash
#!/bin/bash
# customer-onboarding.sh

CUSTOMER_NAME=$1
AWS_ACCOUNT_ID=$2
REGION=$3

echo "Setting up Commitment Platform for $CUSTOMER_NAME..."

# Create customer directory
mkdir -p customers/$CUSTOMER_NAME
cd customers/$CUSTOMER_NAME

# Generate customer configuration
cat > config.json << EOF
{
  "customer_name": "$CUSTOMER_NAME",
  "aws_account_id": "$AWS_ACCOUNT_ID",
  "region": "$REGION",
  "deployment_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Deploy customer instance
docker-compose -f ../../docker-compose.yml up -d

echo "Platform deployed for $CUSTOMER_NAME at https://$CUSTOMER_NAME.commitment-platform.com"
```

## Backup & Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump commitment_platform > $BACKUP_DIR/database.sql

# Application data backup
tar -czf $BACKUP_DIR/app_data.tar.gz /app/data/

# Upload to S3
aws s3 cp $BACKUP_DIR/ s3://commitment-platform-backups/$(date +%Y%m%d)/ --recursive
```

### Recovery Procedure
```bash
#!/bin/bash
# restore.sh
BACKUP_DATE=$1

# Download from S3
aws s3 cp s3://commitment-platform-backups/$BACKUP_DATE/ ./restore/ --recursive

# Restore database
psql commitment_platform < restore/database.sql

# Restore application data
tar -xzf restore/app_data.tar.gz -C /
```

## Performance Optimization

### Caching Configuration
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@app.route('/api/credit-recommendations')
@cache.cached(timeout=300)  # 5 minute cache
def credit_recommendations():
    return jsonify(get_credit_recommendations())
```

### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_recommendations_timestamp ON recommendations(created_at);
CREATE INDEX idx_user_feedback_credit_type ON user_feedback(credit_type);
CREATE INDEX idx_attestation_events_deadline ON attestation_events(deadline_date);
```

## Security Hardening

### API Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/upload-pdf', methods=['POST'])
@limiter.limit("5 per minute")
def upload_pdf():
    # Implementation
```

### Input Validation
```python
from marshmallow import Schema, fields, validate

class RecommendationFeedbackSchema(Schema):
    recommendation_id = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    action = fields.Str(required=True, validate=validate.OneOf(['accepted', 'rejected']))
    credit_type = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    reason = fields.Str(validate=validate.Length(max=1000))
```

## Go-Live Checklist

### Technical Validation
- [ ] All endpoints responding correctly
- [ ] AWS integration working
- [ ] PDF processing functional
- [ ] Database connections stable
- [ ] SSL certificates valid
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested

### Business Validation
- [ ] Customer PPA documents processed successfully
- [ ] Credit recommendations generating
- [ ] Calendar events creating properly
- [ ] Learning system recording feedback
- [ ] Performance metrics within SLA

### Post-Deployment
- [ ] Customer training completed
- [ ] Support documentation delivered
- [ ] Monitoring dashboards configured
- [ ] Success metrics baseline established
- [ ] Escalation procedures documented
