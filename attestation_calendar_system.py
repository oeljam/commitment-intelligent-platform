#!/usr/bin/env python3
"""
Attestation Calendar System with Learning Loop
Creates calendar events for credit submission deadlines and learns from user feedback
"""

import json
from datetime import datetime, timedelta
import uuid

class AttestationCalendarSystem:
    def __init__(self):
        self.credit_deadlines = {
            "gen_ai_credit": {
                "name": "Gen AI Credit Attestation",
                "deadline_days": [30, 14, 7, 3, 1],  # Days before deadline
                "submission_deadline": "2025-12-31",
                "template": "Gen AI workload attestation form",
                "requirements": ["SageMaker usage report", "Lambda function list", "Graviton instance verification"]
            },
            "graviton_optimization_credit": {
                "name": "Graviton Optimization Attestation", 
                "deadline_days": [30, 14, 7, 3, 1],
                "submission_deadline": "2025-12-31",
                "template": "Graviton optimization attestation form",
                "requirements": ["ARM instance usage report", "RDS Graviton verification", "Performance benchmarks"]
            },
            "data_analytics_credit": {
                "name": "Data Analytics Credit Attestation",
                "deadline_days": [30, 14, 7, 3, 1], 
                "submission_deadline": "2025-12-31",
                "template": "Data analytics workload attestation form",
                "requirements": ["Redshift usage report", "EMR job statistics", "S3 data volume metrics"]
            },
            "serverless_credit": {
                "name": "Serverless Optimization Attestation",
                "deadline_days": [30, 14, 7, 3, 1],
                "submission_deadline": "2025-12-31", 
                "template": "Serverless architecture attestation form",
                "requirements": ["Lambda invocation metrics", "API Gateway usage", "DynamoDB performance data"]
            }
        }
        
        self.learning_data = {
            "accepted_recommendations": [],
            "rejected_recommendations": [],
            "user_preferences": {}
        }
    
    def create_attestation_events(self, qualified_credits):
        """Create calendar events for qualified credit attestations"""
        events = []
        
        for credit in qualified_credits:
            if credit['status'] in ['qualified', 'partially_qualified']:
                credit_key = self._get_credit_key(credit['credit_name'])
                if credit_key in self.credit_deadlines:
                    credit_info = self.credit_deadlines[credit_key]
                    
                    # Create events for each reminder day
                    for days_before in credit_info['deadline_days']:
                        event = self._create_calendar_event(credit_info, days_before, credit)
                        events.append(event)
        
        return events
    
    def _create_calendar_event(self, credit_info, days_before, credit):
        """Create individual calendar event"""
        deadline = datetime.strptime(credit_info['submission_deadline'], '%Y-%m-%d')
        event_date = deadline - timedelta(days=days_before)
        
        return {
            "event_id": f"attestation-{uuid.uuid4()}",
            "title": f"URGENT: {credit_info['name']} - {days_before} days remaining",
            "description": f"""
Credit: {credit['credit_name']} ({credit['discount']} savings)
Deadline: {credit_info['submission_deadline']}
Current Status: {credit['status']}
Potential Savings: ${credit['potential_savings']:.2f}/month

Required Documents:
{chr(10).join(['• ' + req for req in credit_info['requirements']])}

Template: {credit_info['template']}
            """.strip(),
            "start_time": event_date.strftime('%Y-%m-%dT09:00:00'),
            "end_time": event_date.strftime('%Y-%m-%dT10:00:00'),
            "reminder_minutes": 15,
            "category": "attestation",
            "credit_type": credit['credit_name'],
            "days_before_deadline": days_before
        }
    
    def _get_credit_key(self, credit_name):
        """Map credit name to internal key"""
        mapping = {
            "Generative AI Credit": "gen_ai_credit",
            "Graviton Optimization Credit": "graviton_optimization_credit", 
            "Data Analytics Credit": "data_analytics_credit",
            "Serverless Optimization Credit": "serverless_credit"
        }
        return mapping.get(credit_name)
    
    def record_recommendation_feedback(self, recommendation_id, action, credit_type, reason=None):
        """Record user feedback on recommendations for learning"""
        feedback = {
            "recommendation_id": recommendation_id,
            "credit_type": credit_type,
            "action": action,  # 'accepted' or 'rejected'
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "user_context": self._get_user_context()
        }
        
        if action == 'accepted':
            self.learning_data['accepted_recommendations'].append(feedback)
        else:
            self.learning_data['rejected_recommendations'].append(feedback)
        
        # Update user preferences
        self._update_user_preferences(credit_type, action, reason)
        
        return feedback
    
    def _get_user_context(self):
        """Get current user context for learning"""
        return {
            "current_spend": 272.80,
            "commitment_progress": 0.55,
            "active_services": ["EC2", "S3", "Lambda", "DynamoDB"]
        }
    
    def _update_user_preferences(self, credit_type, action, reason):
        """Update user preferences based on feedback"""
        if credit_type not in self.user_preferences:
            self.user_preferences[credit_type] = {
                "acceptance_rate": 0,
                "common_rejection_reasons": [],
                "preferred_timing": "30_days_before"
            }
        
        # Update acceptance rate
        total_feedback = len([f for f in self.learning_data['accepted_recommendations'] + 
                            self.learning_data['rejected_recommendations'] 
                            if f['credit_type'] == credit_type])
        
        accepted_count = len([f for f in self.learning_data['accepted_recommendations'] 
                            if f['credit_type'] == credit_type])
        
        if total_feedback > 0:
            self.user_preferences[credit_type]['acceptance_rate'] = accepted_count / total_feedback
        
        # Track rejection reasons
        if action == 'rejected' and reason:
            if reason not in self.user_preferences[credit_type]['common_rejection_reasons']:
                self.user_preferences[credit_type]['common_rejection_reasons'].append(reason)
    
    def get_personalized_recommendations(self, credit_recommendations):
        """Apply learning to personalize recommendations"""
        personalized = []
        
        for credit in credit_recommendations:
            credit_type = credit['credit_name']
            
            # Apply learning-based adjustments
            if credit_type in self.user_preferences:
                prefs = self.user_preferences[credit_type]
                
                # Adjust recommendation based on acceptance rate
                if prefs['acceptance_rate'] < 0.3:
                    credit['confidence'] = 'low'
                    credit['learning_note'] = f"Previously rejected {len([r for r in self.learning_data['rejected_recommendations'] if r['credit_type'] == credit_type])} times"
                elif prefs['acceptance_rate'] > 0.7:
                    credit['confidence'] = 'high'
                    credit['learning_note'] = "High acceptance rate - recommended"
                else:
                    credit['confidence'] = 'medium'
            else:
                credit['confidence'] = 'new'
                credit['learning_note'] = "New recommendation - no learning data"
            
            personalized.append(credit)
        
        return personalized

def create_attestation_calendar_events(credit_recommendations):
    """Main function to create attestation events"""
    calendar_system = AttestationCalendarSystem()
    return calendar_system.create_attestation_events(credit_recommendations)

def process_recommendation_feedback(recommendation_id, action, credit_type, reason=None):
    """Process user feedback on recommendations"""
    calendar_system = AttestationCalendarSystem()
    return calendar_system.record_recommendation_feedback(recommendation_id, action, credit_type, reason)

if __name__ == "__main__":
    # Test with sample credit data
    sample_credits = [
        {
            "credit_name": "Serverless Optimization Credit",
            "discount": "18%",
            "status": "partially_qualified",
            "potential_savings": 49.10
        }
    ]
    
    events = create_attestation_calendar_events(sample_credits)
    print(json.dumps(events, indent=2))
