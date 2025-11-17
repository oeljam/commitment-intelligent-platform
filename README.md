# Commitment Intelligent Platform v0.3

An AI-powered platform for analyzing PDF documents and generating intelligent recommendations with integrated calendar and email management.

## 🆕 What's New in v0.3

### Enhanced Dashboard & UX
- **Compact Layout**: Streamlined interface with better space utilization
- **Toast Notifications**: Real-time feedback for user actions
- **Setup Process**: Guided preparation phase before analysis
- **Visual Feedback**: Improved button states and loading indicators

### Business Workflow Integration
- **Email Configuration**: Predefined teams and custom email lists
- **Outlook Calendar**: Real Microsoft Graph API integration with OAuth2
- **Event Management**: Select and create calendar events from recommendations
- **History Tracking**: Complete audit trail for recommendations and attestations

### Advanced Features
- **PDF Upload Repositioning**: Better file management workflow
- **Email Distribution**: SMTP-based email sending with HTML templates
- **Event Selection Modal**: Bulk operations with "Select All" functionality
- **Spend Monitoring**: Track and monitor recommendation implementations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Microsoft Graph API credentials (for calendar integration)
- SMTP server access (for email features)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd commitment-intelligent-platform-v0.3

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python dashboard.py
```

### Setup Process
1. **Upload PDFs**: Add documents for analysis
2. **Configure Email**: Set up team distributions and custom lists
3. **Connect Calendar**: Authenticate with Microsoft Outlook (optional)
4. **Run Analysis**: Generate AI-powered recommendations
5. **Take Action**: Accept recommendations and create calendar events

## 📋 Features

### Core Functionality
- **PDF Analysis**: Extract and analyze document content
- **AI Recommendations**: Generate intelligent suggestions
- **Learning System**: Adaptive recommendations based on user feedback
- **Multi-format Support**: Handle various document types

### Integration Capabilities
- **Microsoft Outlook**: Calendar event creation and management
- **Email Distribution**: Automated notifications to stakeholders
- **Event History**: Track all recommendation and attestation activities
- **User Preferences**: Personalized experience and settings

### User Interface
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live feedback and status indicators
- **Modal Dialogs**: Intuitive interaction patterns
- **Progress Tracking**: Visual indicators for long-running operations

## 🔧 Configuration

### Email Setup
Configure email settings in the dashboard:
- **Predefined Teams**: Select from common distribution lists
- **Custom Lists**: Add specific email addresses
- **SMTP Configuration**: Set up email server credentials

### Calendar Integration
Set up Microsoft Graph API:
1. Register application in Azure AD
2. Configure OAuth2 permissions
3. Add credentials to environment variables
4. Test connection in dashboard

### Environment Variables
```bash
# Microsoft Graph API
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT_ID=your_tenant_id

# Email Configuration
SMTP_SERVER=smtp.your-server.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
```

## 📊 Usage Workflow

### 1. Preparation Phase
- Upload PDF documents
- Configure email distribution lists
- Set up calendar integration (optional)

### 2. Analysis Phase
- Run AI analysis on uploaded documents
- Review generated recommendations
- Customize recommendation parameters

### 3. Action Phase
- Accept/reject recommendations
- Create calendar events for implementation
- Send email notifications to stakeholders
- Monitor progress and outcomes

### 4. Tracking Phase
- View recommendation history
- Track attestation events
- Monitor spend and ROI
- Generate reports

## 🛠️ Technical Architecture

### Backend Components
- **Flask Application**: Web server and API endpoints
- **AI Analysis Engine**: Document processing and recommendation generation
- **Learning System**: Adaptive algorithms for personalization
- **Integration Layer**: External service connections

### Frontend Components
- **Dashboard Interface**: Main user interaction layer
- **Modal System**: Dialog management for complex operations
- **Event Management**: Calendar and email interaction components
- **History Tracking**: Audit trail and reporting interfaces

### Data Flow
1. **Document Upload** → PDF processing and content extraction
2. **AI Analysis** → Recommendation generation and scoring
3. **User Interaction** → Acceptance/rejection and customization
4. **Integration** → Calendar events and email notifications
5. **Tracking** → History logging and progress monitoring

## 🔍 API Endpoints

### Core Operations
- `POST /upload` - Upload PDF documents
- `POST /analyze` - Run AI analysis
- `POST /accept_recommendation` - Accept recommendation
- `GET /recommendations` - Get recommendation history

### Integration Endpoints
- `POST /create_calendar_events` - Create Outlook calendar events
- `POST /send_emails` - Send email notifications
- `GET /events` - Get event history
- `POST /configure_email` - Set up email distribution

### Management Endpoints
- `GET /attestation_history` - Get attestation events
- `POST /update_preferences` - Update user settings
- `GET /system_status` - Check integration status

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### Manual Testing
1. Upload sample PDF documents
2. Run analysis and verify recommendations
3. Test calendar integration with test events
4. Verify email notifications are sent correctly

## 🚀 Deployment

### Local Development
```bash
python dashboard.py
```

### Production Deployment
1. Set up production environment variables
2. Configure reverse proxy (nginx/Apache)
3. Set up SSL certificates
4. Configure monitoring and logging

## 📝 Version History

### v0.3 (Current)
- Enhanced dashboard with compact layout
- Integrated Outlook calendar with Microsoft Graph API
- Added email configuration and distribution system
- Implemented event history tracking
- Improved user workflow with setup process

### v0.2
- Added learning system for adaptive recommendations
- Implemented user preferences and customization
- Enhanced PDF processing capabilities
- Added basic email notifications

### v0.1
- Initial release with PDF analysis
- Basic recommendation generation
- Simple web interface
- Core AI processing engine

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation wiki
- Review the troubleshooting guide

## 🔮 Roadmap

### Upcoming Features
- Advanced analytics and reporting
- Multi-language support
- Mobile application
- Advanced AI models
- Enterprise integrations
