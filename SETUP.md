# Setup Guide - Commitment Intelligent Platform v0.3

## 🎯 Overview
This guide will walk you through setting up the Commitment Intelligent Platform v0.3 with all its new features including Outlook calendar integration and email distribution.

## 📋 Prerequisites Checklist

### System Requirements
- [ ] Python 3.8 or higher
- [ ] Git installed
- [ ] Internet connection for API integrations
- [ ] Web browser (Chrome, Firefox, Safari, Edge)

### Optional Integrations
- [ ] Microsoft 365 account (for Outlook calendar)
- [ ] SMTP server access (for email notifications)
- [ ] Azure AD application registration (for Graph API)

## 🚀 Installation Steps

### 1. Clone and Setup Project
```bash
# Clone the repository
git clone <your-repository-url>
cd commitment-intelligent-platform-v0.3

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Configuration
Create a `.env` file in the project root:
```bash
# Basic Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Optional: Microsoft Graph API (for calendar integration)
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_REDIRECT_URI=http://localhost:5000/auth/callback

# Optional: Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
```

### 3. Test Basic Installation
```bash
# Run the application
python dashboard.py

# Open browser and navigate to:
# http://localhost:5000
```

## 🔧 Advanced Configuration

### Microsoft Outlook Calendar Integration

#### Step 1: Azure AD App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in the details:
   - **Name**: Commitment Intelligence Platform
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Web - `http://localhost:5000/auth/callback`

#### Step 2: Configure API Permissions
1. In your app registration, go to "API permissions"
2. Click "Add a permission" > "Microsoft Graph" > "Delegated permissions"
3. Add these permissions:
   - `Calendars.ReadWrite`
   - `User.Read`
   - `offline_access`
4. Click "Grant admin consent"

#### Step 3: Get Credentials
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Copy the **Value** (this is your `MICROSOFT_CLIENT_SECRET`)
4. Go to "Overview" and copy:
   - **Application (client) ID** → `MICROSOFT_CLIENT_ID`
   - **Directory (tenant) ID** → `MICROSOFT_TENANT_ID`

#### Step 4: Update Environment Variables
Add to your `.env` file:
```bash
MICROSOFT_CLIENT_ID=your_application_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_REDIRECT_URI=http://localhost:5000/auth/callback
```

### Email Configuration

#### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Generate password for "Mail"
3. Update `.env`:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
EMAIL_FROM=your_email@gmail.com
```

#### Outlook/Office 365 Setup
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
EMAIL_FROM=your_email@outlook.com
```

#### Corporate SMTP Setup
```bash
SMTP_SERVER=your_corporate_smtp_server
SMTP_PORT=587  # or 25, 465, 2525
SMTP_USERNAME=your_corporate_email
SMTP_PASSWORD=your_password
EMAIL_FROM=your_corporate_email
```

## 🧪 Testing Your Setup

### 1. Basic Functionality Test
1. Start the application: `python dashboard.py`
2. Open http://localhost:5000
3. Upload a sample PDF file
4. Run analysis and verify recommendations appear

### 2. Calendar Integration Test
1. Go to the dashboard
2. Click "Connect Calendar" in the setup section
3. Authenticate with Microsoft
4. Try creating a test calendar event

### 3. Email Configuration Test
1. Configure email settings in the dashboard
2. Add your email to a test distribution list
3. Accept a recommendation and send test notification

## 🔍 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

#### Calendar authentication fails
- Verify Azure AD app permissions are granted
- Check redirect URI matches exactly
- Ensure tenant ID is correct
- Try incognito/private browsing mode

#### Email sending fails
- Verify SMTP credentials are correct
- Check if 2FA/App passwords are required
- Test SMTP connection separately
- Check firewall/network restrictions

#### PDF upload issues
- Ensure upload directory exists and is writable
- Check file size limits
- Verify PDF is not corrupted or password-protected

### Debug Mode
Enable detailed logging by setting in `.env`:
```bash
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

## 📊 Usage Workflow

### First Time Setup
1. **Upload Documents**: Add your PDF files for analysis
2. **Configure Email**: Set up distribution lists and SMTP settings
3. **Connect Calendar**: Authenticate with Microsoft Outlook (optional)
4. **Test Integration**: Run a complete workflow test

### Daily Usage
1. **Upload New Documents**: Add files as needed
2. **Run Analysis**: Generate recommendations
3. **Review Results**: Accept/reject recommendations
4. **Create Events**: Schedule implementation activities
5. **Send Notifications**: Inform stakeholders

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate credentials regularly
- Use app-specific passwords when available

### Network Security
- Use HTTPS in production
- Configure proper firewall rules
- Monitor access logs
- Implement rate limiting

### Data Protection
- Encrypt sensitive data at rest
- Use secure file upload validation
- Implement proper access controls
- Regular security audits

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment variables
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=strong_production_secret_key

# Use production URLs
MICROSOFT_REDIRECT_URI=https://yourdomain.com/auth/callback
```

### Web Server Configuration
Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 dashboard:app
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Support

If you encounter issues:
1. Check this setup guide thoroughly
2. Review the troubleshooting section
3. Check application logs for error details
4. Create an issue in the repository with:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Log excerpts (without sensitive data)

## ✅ Setup Verification Checklist

- [ ] Python environment activated
- [ ] All dependencies installed
- [ ] Application starts without errors
- [ ] Can access dashboard at localhost:5000
- [ ] PDF upload and analysis works
- [ ] Calendar integration configured (if needed)
- [ ] Email configuration tested (if needed)
- [ ] All features tested and working
- [ ] Environment variables secured
- [ ] Ready for production deployment (if applicable)
