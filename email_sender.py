#!/usr/bin/env python3
"""
Email Distribution System
Handles SMTP email sending with HTML templates and team management
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from datetime import datetime

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('EMAIL_FROM', self.username)
        
        # Predefined team email lists
        self.predefined_teams = {
            'operations': ['ops-team@company.com', 'operations-manager@company.com'],
            'management': ['ceo@company.com', 'cto@company.com', 'cfo@company.com'],
            'it_support': ['it-support@company.com', 'sysadmin@company.com'],
            'finance': ['finance-team@company.com', 'accounting@company.com'],
            'hr': ['hr@company.com', 'people-ops@company.com'],
            'legal': ['legal@company.com', 'compliance@company.com']
        }
    
    def get_team_emails(self, team_names):
        """Get email addresses for predefined teams"""
        emails = []
        for team in team_names:
            if team in self.predefined_teams:
                emails.extend(self.predefined_teams[team])
        return list(set(emails))  # Remove duplicates
    
    def create_html_template(self, template_type, data):
        """Create HTML email template"""
        if template_type == 'recommendation_accepted':
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #232F3E; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                        <h1 style="margin: 0;">Recommendation Accepted</h1>
                        <p style="margin: 10px 0 0 0;">Commitment Intelligent Platform</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border: 1px solid #ddd; border-top: none;">
                        <h2 style="color: #232F3E; margin-top: 0;">New Recommendation Implementation</h2>
                        
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #28a745;">📋 {data.get('title', 'Recommendation')}</h3>
                            <p><strong>Priority:</strong> <span style="color: #dc3545;">{data.get('priority', 'Medium')}</span></p>
                            <p><strong>Implementation Date:</strong> {data.get('implementation_date', 'TBD')}</p>
                            <p><strong>Assigned Team:</strong> {data.get('assigned_team', 'TBD')}</p>
                        </div>
                        
                        <div style="margin: 20px 0;">
                            <h4>Description:</h4>
                            <p>{data.get('description', 'No description provided')}</p>
                        </div>
                        
                        {f'<div style="margin: 20px 0;"><h4>Implementation Notes:</h4><p>{data.get("user_notes")}</p></div>' if data.get('user_notes') else ''}
                        
                        <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="margin-top: 0; color: #0066cc;">📅 Next Steps</h4>
                            <ul>
                                <li>Review the recommendation details</li>
                                <li>Check your calendar for implementation meeting</li>
                                <li>Prepare necessary resources and team members</li>
                                <li>Track progress in the platform dashboard</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:5000" style="background: #FF9900; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                View in Dashboard
                            </a>
                        </div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px; color: #666;">
                        <p>This email was sent by the Commitment Intelligent Platform</p>
                        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return "<html><body><h1>Notification</h1><p>Default email template</p></body></html>"
    
    def send_email(self, recipients, subject, template_type, data, attachments=None):
        """Send email with HTML template"""
        if not self.username or not self.password:
            return {
                'success': False,
                'error': 'SMTP credentials not configured'
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Create HTML content
            html_content = self.create_html_template(template_type, data)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return {
                'success': True,
                'message': f'Email sent successfully to {len(recipients)} recipients',
                'recipients': recipients
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }
    
    def send_recommendation_notification(self, recommendation_data, recipients):
        """Send notification for accepted recommendation"""
        subject = f"New Recommendation Accepted: {recommendation_data.get('title', 'Implementation Required')}"
        
        return self.send_email(
            recipients=recipients,
            subject=subject,
            template_type='recommendation_accepted',
            data=recommendation_data
        )
    
    def test_connection(self):
        """Test SMTP connection"""
        if not self.username or not self.password:
            return {
                'success': False,
                'error': 'SMTP credentials not configured'
            }
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
            
            return {
                'success': True,
                'message': 'SMTP connection successful'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'SMTP connection failed: {str(e)}'
            }
    
    def get_available_teams(self):
        """Get list of available predefined teams"""
        return list(self.predefined_teams.keys())
    
    def simulate_email_send(self, recipients, subject, data):
        """Simulate email sending when SMTP is not configured"""
        return {
            'success': True,
            'simulated': True,
            'message': f'Email simulation: Would send "{subject}" to {len(recipients)} recipients',
            'recipients': recipients,
            'data': data
        }
