#!/usr/bin/env python3
"""
Microsoft Outlook Calendar Integration via Graph API
Handles OAuth2 authentication and calendar event management
"""

import requests
import json
from datetime import datetime, timedelta
import os
from urllib.parse import urlencode

class OutlookCalendarMCP:
    def __init__(self):
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        self.access_token = None
        self.refresh_token = None
        
    def get_auth_url(self):
        """Generate Microsoft OAuth2 authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'https://graph.microsoft.com/Calendars.ReadWrite https://graph.microsoft.com/User.Read offline_access',
            'response_mode': 'query'
        }
        
        base_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize'
        return f"{base_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            return {
                'success': True,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': token_data.get('expires_in')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_calendar_event(self, event_data):
        """Create a calendar event in Outlook"""
        if not self.access_token:
            return {'success': False, 'error': 'Not authenticated'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Format event for Microsoft Graph API
        graph_event = {
            'subject': event_data.get('title', 'Recommendation Implementation'),
            'body': {
                'contentType': 'HTML',
                'content': event_data.get('description', '')
            },
            'start': {
                'dateTime': event_data.get('start_time'),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data.get('end_time'),
                'timeZone': 'UTC'
            },
            'location': {
                'displayName': event_data.get('location', '')
            },
            'attendees': [
                {
                    'emailAddress': {
                        'address': email,
                        'name': email
                    },
                    'type': 'required'
                } for email in event_data.get('attendees', [])
            ],
            'reminderMinutesBeforeStart': event_data.get('reminder_minutes', 15)
        }
        
        try:
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/events',
                headers=headers,
                json=graph_event
            )
            response.raise_for_status()
            
            event_result = response.json()
            return {
                'success': True,
                'event_id': event_result.get('id'),
                'web_link': event_result.get('webLink'),
                'event_data': event_result
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_info(self):
        """Get current user information"""
        if not self.access_token:
            return {'success': False, 'error': 'Not authenticated'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            response.raise_for_status()
            
            user_data = response.json()
            return {
                'success': True,
                'user': {
                    'name': user_data.get('displayName'),
                    'email': user_data.get('mail') or user_data.get('userPrincipalName')
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def is_connected(self):
        """Check if calendar is connected and authenticated"""
        return self.access_token is not None
    
    def simulate_event_creation(self, event_data):
        """Simulate calendar event creation when API is not available"""
        return {
            'success': True,
            'simulated': True,
            'event_id': f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'message': 'Calendar event simulated (Microsoft Graph API not configured)',
            'event_data': event_data
        }
