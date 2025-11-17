# API Documentation - v0.3

## 🌐 Overview
The Commitment Intelligent Platform v0.3 provides a comprehensive REST API for document analysis, recommendation management, calendar integration, and email distribution.

## 🔗 Base URL
```
Development: http://localhost:5000
Production: https://yourdomain.com
```

## 🔐 Authentication
Most endpoints require session-based authentication. Calendar integration uses OAuth2 with Microsoft Graph API.

## 📋 Core Endpoints

### Document Management

#### Upload PDF Document
```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): PDF document to upload

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "document.pdf",
  "file_id": "uuid-string"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid file type. Please upload a PDF file."
}
```

#### Analyze Documents
```http
POST /analyze
Content-Type: application/json
```

**Request Body:**
```json
{
  "files": ["file1.pdf", "file2.pdf"],
  "analysis_type": "comprehensive",
  "options": {
    "include_summary": true,
    "generate_recommendations": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "uuid-string",
  "recommendations": [
    {
      "id": "rec-1",
      "title": "Recommendation Title",
      "description": "Detailed description",
      "priority": "high",
      "category": "process_improvement",
      "estimated_impact": "significant",
      "implementation_effort": "medium",
      "confidence_score": 0.85
    }
  ],
  "summary": "Analysis summary text"
}
```

### Recommendation Management

#### Accept Recommendation
```http
POST /accept_recommendation
Content-Type: application/json
```

**Request Body:**
```json
{
  "recommendation_id": "rec-1",
  "user_notes": "Additional implementation notes",
  "priority_override": "high",
  "implementation_date": "2024-12-01",
  "assigned_team": "operations",
  "create_calendar_event": true,
  "send_notifications": true,
  "email_recipients": ["team@company.com"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Recommendation accepted successfully",
  "recommendation_id": "rec-1",
  "calendar_event_id": "event-123",
  "email_sent": true,
  "attestation_id": "att-456"
}
```

#### Get Recommendation History
```http
GET /recommendations
```

**Query Parameters:**
- `limit` (integer, optional): Number of recommendations to return (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)
- `status` (string, optional): Filter by status (accepted, rejected, pending)
- `category` (string, optional): Filter by category
- `date_from` (string, optional): ISO date string
- `date_to` (string, optional): ISO date string

**Response:**
```json
{
  "success": true,
  "recommendations": [
    {
      "id": "rec-1",
      "title": "Recommendation Title",
      "status": "accepted",
      "created_at": "2024-11-17T10:00:00Z",
      "accepted_at": "2024-11-17T11:30:00Z",
      "category": "process_improvement",
      "priority": "high",
      "implementation_status": "in_progress"
    }
  ],
  "total": 25,
  "has_more": false
}
```

### Calendar Integration

#### Authenticate with Microsoft
```http
GET /auth/login
```

**Response:**
Redirects to Microsoft OAuth2 authorization URL

#### OAuth Callback
```http
GET /auth/callback?code=auth_code&state=state_value
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "user_info": {
    "name": "John Doe",
    "email": "john.doe@company.com"
  }
}
```

#### Create Calendar Events
```http
POST /create_calendar_events
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [
    {
      "recommendation_id": "rec-1",
      "title": "Implement Process Improvement",
      "description": "Implementation of recommendation rec-1",
      "start_time": "2024-12-01T09:00:00Z",
      "end_time": "2024-12-01T10:00:00Z",
      "attendees": ["team@company.com"],
      "location": "Conference Room A",
      "reminder_minutes": 15
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created_events": [
    {
      "recommendation_id": "rec-1",
      "calendar_event_id": "event-123",
      "web_link": "https://outlook.office365.com/calendar/...",
      "status": "created"
    }
  ],
  "failed_events": []
}
```

### Email Management

#### Configure Email Settings
```http
POST /configure_email
Content-Type: application/json
```

**Request Body:**
```json
{
  "predefined_teams": ["operations", "management", "it_support"],
  "custom_emails": ["stakeholder@company.com", "external@partner.com"],
  "smtp_settings": {
    "server": "smtp.company.com",
    "port": 587,
    "username": "notifications@company.com",
    "use_tls": true
  },
  "email_templates": {
    "recommendation_accepted": {
      "subject": "New Recommendation Accepted: {{title}}",
      "template": "custom_template_html"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email configuration updated successfully",
  "config_id": "email-config-123"
}
```

#### Send Email Notifications
```http
POST /send_emails
Content-Type: application/json
```

**Request Body:**
```json
{
  "template": "recommendation_accepted",
  "recipients": ["team@company.com"],
  "data": {
    "recommendation_title": "Process Improvement",
    "implementation_date": "2024-12-01",
    "assigned_team": "Operations",
    "priority": "High"
  },
  "attachments": [
    {
      "filename": "implementation_plan.pdf",
      "content_type": "application/pdf",
      "data": "base64_encoded_content"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Emails sent successfully",
  "sent_count": 3,
  "failed_count": 0,
  "message_ids": ["msg-123", "msg-124", "msg-125"]
}
```

### Event Management

#### Get Events
```http
GET /events
```

**Query Parameters:**
- `type` (string, optional): Event type (recommendation, attestation, calendar)
- `status` (string, optional): Event status (created, pending, completed)
- `limit` (integer, optional): Number of events to return
- `date_from` (string, optional): ISO date string
- `date_to` (string, optional): ISO date string

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "event-123",
      "type": "recommendation",
      "status": "created",
      "timestamp": "2024-11-17T10:00:00Z",
      "data": {
        "recommendation_id": "rec-1",
        "title": "Process Improvement",
        "action": "accepted"
      },
      "metadata": {
        "user": "john.doe",
        "source": "dashboard"
      }
    }
  ],
  "total": 15
}
```

#### Get Attestation History
```http
GET /attestation_history
```

**Query Parameters:**
- `recommendation_id` (string, optional): Filter by recommendation
- `status` (string, optional): Filter by status
- `limit` (integer, optional): Number of records to return

**Response:**
```json
{
  "success": true,
  "attestations": [
    {
      "id": "att-456",
      "recommendation_id": "rec-1",
      "status": "pending",
      "created_at": "2024-11-17T11:30:00Z",
      "implementation_date": "2024-12-01",
      "assigned_team": "operations",
      "progress": 25,
      "notes": "Implementation in progress",
      "calendar_event_id": "event-123"
    }
  ],
  "total": 8
}
```

## 🔧 System Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-17T12:00:00Z",
  "version": "0.3.0",
  "integrations": {
    "microsoft_graph": "connected",
    "email_smtp": "configured",
    "file_storage": "available"
  }
}
```

### System Status
```http
GET /system_status
```

**Response:**
```json
{
  "success": true,
  "system": {
    "uptime": "2 days, 14 hours",
    "memory_usage": "45%",
    "disk_usage": "23%",
    "active_sessions": 12
  },
  "integrations": {
    "microsoft_graph": {
      "status": "connected",
      "last_check": "2024-11-17T11:55:00Z",
      "token_expires": "2024-11-17T13:00:00Z"
    },
    "email_smtp": {
      "status": "configured",
      "last_test": "2024-11-17T10:00:00Z"
    }
  },
  "statistics": {
    "total_documents": 156,
    "total_recommendations": 89,
    "accepted_recommendations": 34,
    "calendar_events_created": 28,
    "emails_sent": 142
  }
}
```

## 📊 WebSocket Endpoints (Real-time Updates)

### Connect to Real-time Updates
```javascript
const socket = io('/updates');

socket.on('recommendation_accepted', (data) => {
  console.log('New recommendation accepted:', data);
});

socket.on('calendar_event_created', (data) => {
  console.log('Calendar event created:', data);
});

socket.on('analysis_complete', (data) => {
  console.log('Analysis completed:', data);
});
```

## 🚨 Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "email",
    "message": "Invalid email format"
  },
  "timestamp": "2024-11-17T12:00:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Codes
- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_ERROR` - Authentication required or failed
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `INTEGRATION_ERROR` - External service integration failed
- `FILE_ERROR` - File upload or processing error
- `RATE_LIMIT_ERROR` - Too many requests
- `SYSTEM_ERROR` - Internal system error

## 🔄 Rate Limiting

### Limits
- **File Upload**: 10 files per minute per user
- **Analysis**: 5 requests per minute per user
- **Email Sending**: 50 emails per hour per user
- **Calendar Events**: 20 events per minute per user
- **General API**: 100 requests per minute per user

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700230800
```

## 📝 Request/Response Examples

### Complete Workflow Example

#### 1. Upload Document
```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:5000/upload
```

#### 2. Analyze Document
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"files": ["document.pdf"]}' \
  http://localhost:5000/analyze
```

#### 3. Accept Recommendation
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_id": "rec-1",
    "create_calendar_event": true,
    "send_notifications": true,
    "email_recipients": ["team@company.com"]
  }' \
  http://localhost:5000/accept_recommendation
```

#### 4. Create Calendar Event
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "events": [{
      "recommendation_id": "rec-1",
      "title": "Implement Recommendation",
      "start_time": "2024-12-01T09:00:00Z",
      "end_time": "2024-12-01T10:00:00Z"
    }]
  }' \
  http://localhost:5000/create_calendar_events
```

## 🧪 Testing

### API Testing with Postman
Import the provided Postman collection for comprehensive API testing.

### Automated Testing
```bash
# Run API tests
python -m pytest tests/api/

# Run integration tests
python -m pytest tests/integration/
```

## 📚 SDK and Libraries

### Python SDK Example
```python
from commitment_platform import CommitmentPlatformAPI

client = CommitmentPlatformAPI(base_url="http://localhost:5000")

# Upload and analyze document
result = client.upload_and_analyze("document.pdf")

# Accept recommendation
client.accept_recommendation(
    recommendation_id="rec-1",
    create_calendar_event=True,
    send_notifications=True
)
```

### JavaScript SDK Example
```javascript
import { CommitmentPlatformClient } from 'commitment-platform-js';

const client = new CommitmentPlatformClient({
  baseUrl: 'http://localhost:5000'
});

// Upload document
const uploadResult = await client.uploadDocument(file);

// Get recommendations
const recommendations = await client.getRecommendations();
```

This API documentation provides comprehensive coverage of all v0.3 endpoints and functionality for developers integrating with the Commitment Intelligent Platform.
