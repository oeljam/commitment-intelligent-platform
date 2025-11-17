# Production Deployment Guide - v0.3

## 🎯 Overview
This guide covers deploying the Commitment Intelligent Platform v0.3 to production environments with all integrations and security best practices.

## 📋 Pre-deployment Checklist

### Infrastructure Requirements
- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Python 3.8+ installed
- [ ] Nginx web server
- [ ] SSL certificate (Let's Encrypt or commercial)
- [ ] Domain name configured
- [ ] Firewall configured (ports 80, 443, SSH)

### Integration Requirements
- [ ] Azure AD application registered (for calendar)
- [ ] SMTP server access configured
- [ ] DNS records configured
- [ ] Backup strategy planned
- [ ] Monitoring solution ready

## 🚀 Deployment Steps

### 1. Server Preparation

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx git supervisor -y
```

#### Create Application User
```bash
sudo adduser --system --group --home /opt/commitment-platform commitment
sudo mkdir -p /opt/commitment-platform
sudo chown commitment:commitment /opt/commitment-platform
```

### 2. Application Deployment

#### Clone Repository
```bash
sudo -u commitment git clone <repository-url> /opt/commitment-platform/app
cd /opt/commitment-platform/app
```

#### Setup Python Environment
```bash
sudo -u commitment python3 -m venv /opt/commitment-platform/venv
sudo -u commitment /opt/commitment-platform/venv/bin/pip install -r requirements.txt
```

#### Create Production Configuration
```bash
sudo -u commitment tee /opt/commitment-platform/.env << EOF
# Production Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -base64 32)

# Domain Configuration
DOMAIN_NAME=yourdomain.com
MICROSOFT_REDIRECT_URI=https://yourdomain.com/auth/callback

# Microsoft Graph API
MICROSOFT_CLIENT_ID=your_production_client_id
MICROSOFT_CLIENT_SECRET=your_production_client_secret
MICROSOFT_TENANT_ID=your_tenant_id

# Email Configuration
SMTP_SERVER=your_smtp_server
SMTP_PORT=587
SMTP_USERNAME=your_email_username
SMTP_PASSWORD=your_email_password
EMAIL_FROM=noreply@yourdomain.com

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/commitment-platform/logs/app.log
EOF
```

#### Create Directories
```bash
sudo -u commitment mkdir -p /opt/commitment-platform/{logs,uploads,data}
sudo chmod 755 /opt/commitment-platform/{logs,uploads,data}
```

### 3. Web Server Configuration

#### Nginx Configuration
```bash
sudo tee /etc/nginx/sites-available/commitment-platform << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # File Upload Limits
    client_max_body_size 100M;

    # Static Files
    location /static {
        alias /opt/commitment-platform/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/commitment-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificate Setup

#### Using Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Auto-renewal
```bash
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 5. Application Service Configuration

#### Gunicorn Configuration
```bash
sudo tee /opt/commitment-platform/gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
preload_app = True
user = "commitment"
group = "commitment"
tmp_upload_dir = None
errorlog = "/opt/commitment-platform/logs/gunicorn_error.log"
accesslog = "/opt/commitment-platform/logs/gunicorn_access.log"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(O)s "%(f)s" "%(a)s"'
EOF
```

#### Supervisor Configuration
```bash
sudo tee /etc/supervisor/conf.d/commitment-platform.conf << EOF
[program:commitment-platform]
command=/opt/commitment-platform/venv/bin/gunicorn -c /opt/commitment-platform/gunicorn.conf.py dashboard:app
directory=/opt/commitment-platform/app
user=commitment
group=commitment
environment=PATH="/opt/commitment-platform/venv/bin"
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/commitment-platform/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start commitment-platform
```

### 6. Firewall Configuration

#### UFW Setup
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 7. Monitoring & Logging

#### Log Rotation
```bash
sudo tee /etc/logrotate.d/commitment-platform << EOF
/opt/commitment-platform/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 commitment commitment
    postrotate
        supervisorctl restart commitment-platform
    endscript
}
EOF
```

#### Health Check Script
```bash
sudo tee /opt/commitment-platform/health-check.sh << EOF
#!/bin/bash
HEALTH_URL="https://yourdomain.com/health"
RESPONSE=\$(curl -s -o /dev/null -w "%{http_code}" \$HEALTH_URL)

if [ \$RESPONSE -eq 200 ]; then
    echo "Application is healthy"
    exit 0
else
    echo "Application health check failed: HTTP \$RESPONSE"
    # Restart application
    supervisorctl restart commitment-platform
    exit 1
fi
EOF

sudo chmod +x /opt/commitment-platform/health-check.sh
sudo chown commitment:commitment /opt/commitment-platform/health-check.sh
```

#### Cron Health Checks
```bash
sudo -u commitment crontab -e
# Add this line:
*/5 * * * * /opt/commitment-platform/health-check.sh >> /opt/commitment-platform/logs/health-check.log 2>&1
```

## 🔒 Security Hardening

### 1. System Security
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Application Security
```bash
# Set proper file permissions
sudo chmod 600 /opt/commitment-platform/.env
sudo chmod -R 755 /opt/commitment-platform/app
sudo chmod -R 755 /opt/commitment-platform/uploads
sudo chown -R commitment:commitment /opt/commitment-platform
```

### 3. Database Security (if applicable)
```bash
# If using PostgreSQL or MySQL, secure the installation
# Follow database-specific security guidelines
```

## 📊 Monitoring Setup

### 1. System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Setup basic monitoring script
sudo tee /opt/commitment-platform/monitor.sh << EOF
#!/bin/bash
echo "=== System Status ===" >> /opt/commitment-platform/logs/system.log
date >> /opt/commitment-platform/logs/system.log
df -h >> /opt/commitment-platform/logs/system.log
free -m >> /opt/commitment-platform/logs/system.log
supervisorctl status >> /opt/commitment-platform/logs/system.log
echo "" >> /opt/commitment-platform/logs/system.log
EOF

sudo chmod +x /opt/commitment-platform/monitor.sh
```

### 2. Application Monitoring
Add health endpoint to your Flask app:
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

## 🔄 Backup Strategy

### 1. Application Backup
```bash
sudo tee /opt/commitment-platform/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/commitment-platform"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup application data
tar -czf \$BACKUP_DIR/data_\$DATE.tar.gz /opt/commitment-platform/data
tar -czf \$BACKUP_DIR/uploads_\$DATE.tar.gz /opt/commitment-platform/uploads
tar -czf \$BACKUP_DIR/logs_\$DATE.tar.gz /opt/commitment-platform/logs

# Keep only last 30 days of backups
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: \$DATE" >> /opt/commitment-platform/logs/backup.log
EOF

sudo chmod +x /opt/commitment-platform/backup.sh
```

### 2. Automated Backups
```bash
sudo -u commitment crontab -e
# Add this line for daily backups at 2 AM:
0 2 * * * /opt/commitment-platform/backup.sh
```

## 🚀 Deployment Verification

### 1. Functional Tests
```bash
# Test application startup
curl -I https://yourdomain.com

# Test file upload
curl -X POST -F "file=@test.pdf" https://yourdomain.com/upload

# Test health endpoint
curl https://yourdomain.com/health
```

### 2. Integration Tests
- Test Microsoft Graph API authentication
- Verify email sending functionality
- Check calendar event creation
- Validate PDF processing pipeline

### 3. Performance Tests
```bash
# Install Apache Bench for basic load testing
sudo apt install apache2-utils -y

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 https://yourdomain.com/
```

## 🔧 Maintenance

### Regular Tasks
- **Daily**: Check application logs and health
- **Weekly**: Review system resources and performance
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Full backup verification and disaster recovery test

### Update Procedure
```bash
# 1. Backup current version
sudo -u commitment cp -r /opt/commitment-platform/app /opt/commitment-platform/app.backup

# 2. Pull updates
sudo -u commitment git pull origin main

# 3. Update dependencies
sudo -u commitment /opt/commitment-platform/venv/bin/pip install -r requirements.txt

# 4. Restart application
sudo supervisorctl restart commitment-platform

# 5. Verify deployment
curl -I https://yourdomain.com/health
```

## 🆘 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check supervisor logs
sudo tail -f /opt/commitment-platform/logs/supervisor.log

# Check gunicorn logs
sudo tail -f /opt/commitment-platform/logs/gunicorn_error.log

# Restart services
sudo supervisorctl restart commitment-platform
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal
```

#### Performance Issues
```bash
# Check system resources
htop
df -h
free -m

# Check application logs
tail -f /opt/commitment-platform/logs/app.log
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Stop current version
sudo supervisorctl stop commitment-platform

# Restore backup
sudo -u commitment rm -rf /opt/commitment-platform/app
sudo -u commitment mv /opt/commitment-platform/app.backup /opt/commitment-platform/app

# Restart application
sudo supervisorctl start commitment-platform
```

#### Database Recovery (if applicable)
```bash
# Restore from backup
# Follow database-specific recovery procedures
```

This deployment guide ensures a secure, scalable, and maintainable production environment for the Commitment Intelligent Platform v0.3.
