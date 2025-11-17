# MCP Server Requirements - Commitment Intelligent Platform

## Overview
The Commitment Intelligent Platform requires several MCP (Model Context Protocol) servers to provide full functionality. These servers handle external integrations and data sources.

## Required MCP Servers

### 1. AWS Billing MCP Server ✅ (EXISTING)
**Status**: Already operational on port 3010
**Purpose**: Real-time AWS cost and usage data
**Endpoints**:
- `/cost-explorer` - Get cost and usage data
- `/service-usage` - Analyze service consumption patterns
- `/account-info` - AWS account metadata

**Configuration**:
```json
{
  "name": "aws-billing",
  "port": 3010,
  "endpoints": {
    "cost_data": "/api/cost-explorer",
    "service_usage": "/api/service-usage"
  }
}
```

### 2. Outlook Calendar MCP Server ⚠️ (NEEDS ENHANCEMENT)
**Status**: Basic version exists, needs calendar creation capability
**Purpose**: Automated attestation calendar event management
**Required Endpoints**:
- `/create-event` - Create calendar events with reminders
- `/update-event` - Modify existing events
- `/delete-event` - Remove events
- `/get-availability` - Check calendar availability

**Enhancement Needed**:
```python
# Required calendar creation functionality
def create_attestation_event(event_data):
    """
    Create calendar event for attestation deadline
    Args:
        event_data: {
            "title": "URGENT: Gen AI Credit Attestation - 30 days remaining",
            "start_time": "2025-12-01T09:00:00",
            "end_time": "2025-12-01T10:00:00",
            "description": "Credit requirements and documentation",
            "reminder_minutes": 15,
            "attendees": ["user@company.com"]
        }
    """
    return calendar_api.create_event(event_data)
```

### 3. Document Processing MCP Server 🆕 (TO BE CREATED)
**Status**: NEEDS CREATION
**Purpose**: Advanced PDF processing and template extraction
**Required Endpoints**:
- `/extract-commitments` - Extract PPA commitment amounts
- `/extract-discounts` - Identify discount percentages
- `/extract-templates` - Get attestation templates
- `/extract-requirements` - Parse credit requirements

**Implementation**:
```python
# document_processing_server.py
class DocumentProcessingServer:
    def extract_credit_templates(self, pdf_path):
        """Extract attestation templates from PPA documents"""
        templates = {
            "gen_ai_credit": {
                "template_name": "Gen AI workload attestation form",
                "requirements": [
                    "SageMaker usage report",
                    "Lambda function list", 
                    "Graviton instance verification"
                ],
                "deadline": "2025-12-31"
            }
        }
        return templates
```

### 4. Learning Analytics MCP Server 🆕 (TO BE CREATED)
**Status**: NEEDS CREATION  
**Purpose**: User feedback analysis and recommendation improvement
**Required Endpoints**:
- `/record-feedback` - Store user acceptance/rejection data
- `/analyze-patterns` - Identify user preference patterns
- `/update-confidence` - Adjust recommendation confidence scores
- `/get-personalization` - Retrieve personalized recommendations

**Implementation**:
```python
# learning_analytics_server.py
class LearningAnalyticsServer:
    def record_user_feedback(self, feedback_data):
        """Record and analyze user feedback for learning"""
        feedback = {
            "user_id": feedback_data["user_id"],
            "recommendation_id": feedback_data["recommendation_id"],
            "action": feedback_data["action"],  # accepted/rejected
            "credit_type": feedback_data["credit_type"],
            "timestamp": datetime.now().isoformat()
        }
        # Store in database and update ML model
        return self.update_recommendation_model(feedback)
```

### 5. Notification MCP Server 🆕 (TO BE CREATED)
**Status**: NEEDS CREATION
**Purpose**: Multi-channel notifications for attestation deadlines
**Required Endpoints**:
- `/send-email` - Email notifications
- `/send-slack` - Slack channel notifications  
- `/send-teams` - Microsoft Teams notifications
- `/schedule-notification` - Schedule future notifications

**Implementation**:
```python
# notification_server.py
class NotificationServer:
    def send_attestation_reminder(self, notification_data):
        """Send multi-channel attestation reminders"""
        channels = ["email", "slack", "teams"]
        for channel in channels:
            self.send_notification(channel, {
                "title": f"Attestation Due: {notification_data['credit_type']}",
                "message": f"Deadline in {notification_data['days_remaining']} days",
                "urgency": "high" if notification_data['days_remaining'] <= 7 else "medium"
            })
```

## MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Commitment Platform                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│AWS Billing  │ │ Outlook     │ │ Document    │
│MCP Server   │ │ Calendar    │ │ Processing  │
│Port: 3010   │ │ MCP Server  │ │ MCP Server  │
│Status: ✅   │ │ Status: ⚠️  │ │ Status: 🆕  │
└─────────────┘ └─────────────┘ └─────────────┘

        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Learning    │ │Notification │ │   Future    │
│ Analytics   │ │ MCP Server  │ │ Extensions  │
│ MCP Server  │ │ Status: 🆕  │ │             │
│ Status: 🆕  │ └─────────────┘ └─────────────┘
└─────────────┘
```

## Implementation Priority

### Phase 1: Critical (Week 1)
1. **Enhance Outlook Calendar MCP** - Enable calendar event creation
2. **Create Document Processing MCP** - Advanced PDF template extraction

### Phase 2: Important (Week 2)
3. **Create Learning Analytics MCP** - User feedback and personalization
4. **Create Notification MCP** - Multi-channel alerting

### Phase 3: Enhancement (Week 3+)
5. **Additional integrations** based on customer needs

## MCP Server Configuration

### Environment Setup
```bash
# Start all required MCP servers
python3 aws_billing_server.py --port 3010 &
python3 outlook_calendar_server.py --port 3011 &
python3 document_processing_server.py --port 3012 &
python3 learning_analytics_server.py --port 3013 &
python3 notification_server.py --port 3014 &
```

### Platform Integration
```python
# In complete_intelligent_dashboard.py
MCP_SERVERS = {
    "aws_billing": "http://localhost:3010",
    "outlook_calendar": "http://localhost:3011", 
    "document_processing": "http://localhost:3012",
    "learning_analytics": "http://localhost:3013",
    "notification": "http://localhost:3014"
}

async def call_mcp_server(server_name, endpoint, data):
    """Call MCP server endpoint"""
    server_url = MCP_SERVERS[server_name]
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{server_url}{endpoint}", json=data) as response:
            return await response.json()
```

## Testing MCP Servers

### Health Check Script
```python
# test_mcp_servers.py
import requests

def test_all_mcp_servers():
    servers = {
        "AWS Billing": "http://localhost:3010/health",
        "Outlook Calendar": "http://localhost:3011/health",
        "Document Processing": "http://localhost:3012/health",
        "Learning Analytics": "http://localhost:3013/health",
        "Notification": "http://localhost:3014/health"
    }
    
    for name, url in servers.items():
        try:
            response = requests.get(url, timeout=5)
            status = "✅ HEALTHY" if response.status_code == 200 else "❌ ERROR"
            print(f"{name}: {status}")
        except:
            print(f"{name}: ❌ OFFLINE")

if __name__ == "__main__":
    test_all_mcp_servers()
```

## Security Considerations

### Authentication
- All MCP servers require API key authentication
- Use environment variables for sensitive credentials
- Implement rate limiting on all endpoints

### Data Privacy
- Document processing server handles sensitive PPA data
- Learning analytics stores user behavior data
- Implement data encryption at rest and in transit

## Deployment Notes

### Docker Compose for MCP Servers
```yaml
version: '3.8'
services:
  aws-billing-mcp:
    build: ./mcp-servers/aws-billing
    ports:
      - "3010:3010"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  
  outlook-calendar-mcp:
    build: ./mcp-servers/outlook-calendar
    ports:
      - "3011:3011"
    environment:
      - OUTLOOK_CLIENT_ID=${OUTLOOK_CLIENT_ID}
      - OUTLOOK_CLIENT_SECRET=${OUTLOOK_CLIENT_SECRET}
  
  document-processing-mcp:
    build: ./mcp-servers/document-processing
    ports:
      - "3012:3012"
    volumes:
      - ./uploads:/app/uploads
  
  learning-analytics-mcp:
    build: ./mcp-servers/learning-analytics
    ports:
      - "3013:3013"
    environment:
      - DATABASE_URL=${DATABASE_URL}
  
  notification-mcp:
    build: ./mcp-servers/notification
    ports:
      - "3014:3014"
    environment:
      - SMTP_SERVER=${SMTP_SERVER}
      - SLACK_TOKEN=${SLACK_TOKEN}
```

## Summary

**Existing**: 1 MCP server (AWS Billing)
**Needs Enhancement**: 1 MCP server (Outlook Calendar)  
**Needs Creation**: 3 MCP servers (Document Processing, Learning Analytics, Notification)

**Total MCP Infrastructure**: 5 servers for complete platform functionality
