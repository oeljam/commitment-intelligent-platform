# Architecture Overview - v0.3

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMITMENT INTELLIGENT PLATFORM v0.3         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER LAYER    │    │  INTEGRATION    │    │   DATA LAYER    │
│                 │    │     LAYER       │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │  Dashboard  │ │    │ │ Outlook API │ │    │ │ PDF Storage │ │
│ │   Web UI    │ │◄──►│ │ (Graph API) │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Modals    │ │    │ │ Email SMTP  │ │    │ │ User Prefs  │ │
│ │ & Dialogs   │ │◄──►│ │   Server    │ │    │ │   & Config  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Toast       │ │    │ │ OAuth2      │ │    │ │ Event       │ │
│ │ Notifications│ │◄──►│ │ Auth Flow   │ │    │ │ History     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CORE ENGINE                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │    PDF      │  │     AI      │  │  Learning   │  │  Event  ││
│  │ Processing  │  │ Analysis    │  │   System    │  │ Manager ││
│  │   Engine    │  │   Engine    │  │             │  │         ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│         │                 │                 │             │    │
│         ▼                 ▼                 ▼             ▼    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              RECOMMENDATION ENGINE                          ││
│  │                                                             ││
│  │  • Content Analysis    • Pattern Recognition               ││
│  │  • Scoring Algorithm   • User Preference Learning          ││
│  │  • Context Awareness   • Feedback Integration              ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    UPLOAD   │───►│   ANALYZE   │───►│   ACTION    │───►│   TRACK     │
│             │    │             │    │             │    │             │
│ • PDF Files │    │ • AI Engine │    │ • Accept/   │    │ • History   │
│ • Config    │    │ • Learning  │    │   Reject    │    │ • Events    │
│ • Email     │    │ • Scoring   │    │ • Calendar  │    │ • Monitor   │
│   Setup     │    │             │    │ • Email     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW STATES                              │
│                                                                     │
│ PREPARATION ──► ANALYSIS ──► DECISION ──► IMPLEMENTATION ──► REVIEW │
│                                                                     │
│ • Upload PDFs   • Run AI     • Accept    • Create Events   • Track  │
│ • Setup Email   • Generate   • Reject    • Send Emails     • Report │
│ • Config Cal    • Score      • Modify    • Monitor         • Learn  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧩 Component Architecture

### Frontend Components
```
dashboard.html
├── Setup Section
│   ├── PDF Upload Area
│   ├── Email Configuration Modal
│   └── Calendar Connection Status
├── Analysis Section
│   ├── Recommendation Cards
│   ├── Accept/Reject Buttons
│   └── Progress Indicators
├── Action Section
│   ├── Event Selection Modal
│   ├── Email Distribution Panel
│   └── Calendar Integration
└── History Section
    ├── Recommendation Timeline
    ├── Attestation Events
    └── Activity Log
```

### Backend Components
```
dashboard.py (Flask App)
├── Core Routes
│   ├── /upload (PDF handling)
│   ├── /analyze (AI processing)
│   ├── /accept_recommendation (workflow)
│   └── /recommendations (history)
├── Integration Routes
│   ├── /auth/login (OAuth2)
│   ├── /create_calendar_events (Outlook)
│   ├── /send_emails (SMTP)
│   └── /configure_email (setup)
├── API Routes
│   ├── /events (event management)
│   ├── /attestation_history (tracking)
│   └── /system_status (health)
└── Support Modules
    ├── outlook_calendar_mcp.py
    ├── email_sender.py
    └── learning_system.py
```

## 🔌 Integration Architecture

### Microsoft Graph API Integration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │  OAuth2 Flow    │    │ Microsoft Graph │
│                 │    │                 │    │                 │
│ 1. User clicks  │───►│ 2. Redirect to  │───►│ 3. User auth    │
│   "Connect Cal" │    │    Azure AD     │    │    & consent    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 6. Calendar     │    │ 5. Store tokens │    │ 4. Return auth  │
│    events       │◄───│    & create     │◄───│    code         │
│    created      │    │    events       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Email Distribution System
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Email Config    │    │ Template Engine │    │ SMTP Server     │
│                 │    │                 │    │                 │
│ • Team Lists    │───►│ • HTML Template │───►│ • Send Email    │
│ • Custom Lists  │    │ • Personalize   │    │ • Track Status  │
│ • Recipients    │    │ • Format        │    │ • Handle Errors │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Database Schema (JSON Files)

### User Preferences
```json
{
  "user_id": "string",
  "email_config": {
    "predefined_teams": ["team1", "team2"],
    "custom_emails": ["email1@domain.com"],
    "smtp_settings": {...}
  },
  "calendar_config": {
    "connected": boolean,
    "default_duration": number,
    "reminder_minutes": number
  },
  "ui_preferences": {
    "compact_layout": boolean,
    "toast_notifications": boolean
  }
}
```

### Event History
```json
{
  "events": [
    {
      "id": "string",
      "type": "recommendation|attestation",
      "timestamp": "ISO_date",
      "data": {...},
      "status": "created|pending|completed"
    }
  ]
}
```

### Learning Data
```json
{
  "recommendations": [...],
  "user_feedback": [...],
  "patterns": {...},
  "scores": {...}
}
```

## 🔐 Security Architecture

### Authentication Flow
```
User ──► Dashboard ──► OAuth2 ──► Azure AD ──► Token ──► Graph API
  │                                   │
  └─── Session ──► Flask ──► Secure ──┘
```

### Data Protection
- Environment variables for secrets
- HTTPS for production
- Token encryption
- Session management
- Input validation
- File upload security

## 🚀 Deployment Architecture

### Development
```
Local Machine
├── Python Virtual Environment
├── Flask Development Server
├── Local File Storage
└── Environment Variables (.env)
```

### Production
```
Production Server
├── Gunicorn WSGI Server
├── Nginx Reverse Proxy
├── SSL/TLS Certificates
├── Secure File Storage
├── Environment Variables (System)
└── Monitoring & Logging
```

## 📈 Performance Considerations

### Optimization Points
- **PDF Processing**: Async processing for large files
- **AI Analysis**: Caching of results
- **Calendar API**: Rate limiting and batching
- **Email Sending**: Queue-based processing
- **File Storage**: Efficient cleanup and rotation

### Scalability
- **Horizontal**: Multiple Flask instances
- **Vertical**: Resource optimization
- **Caching**: Redis for session/data
- **Database**: Migration to proper DB
- **CDN**: Static asset delivery

## 🔍 Monitoring & Observability

### Health Checks
- Application status
- Integration connectivity
- File system health
- Memory/CPU usage
- Error rates

### Logging
- Application logs
- Integration logs
- Security events
- Performance metrics
- User activity

This architecture supports the v0.3 feature set while maintaining flexibility for future enhancements and scalability requirements.
