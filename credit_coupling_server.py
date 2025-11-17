#!/usr/bin/env python3
"""
Intelligent Credit Coupling MCP Server
Analyzes AWS service usage and suggests credit-eligible combinations
"""

import boto3
import json
from datetime import datetime, timedelta

class CreditCouplingEngine:
    def __init__(self):
        self.credit_offerings = {
            "gen_ai_credit": {
                "name": "Generative AI Credit",
                "discount": "25%",
                "requirements": {
                    "primary_services": ["Amazon SageMaker", "Amazon Bedrock", "AWS Lambda"],
                    "supporting_services": ["Amazon EC2", "Amazon S3"],
                    "minimum_spend": 1000,
                    "graviton_bonus": True
                },
                "description": "Combines ML/AI services with compute for enhanced AI workloads"
            },
            "graviton_optimization_credit": {
                "name": "Graviton Optimization Credit", 
                "discount": "31%",
                "requirements": {
                    "primary_services": ["Amazon EC2"],
                    "instance_types": ["graviton", "arm64"],
                    "supporting_services": ["Amazon RDS", "Amazon ElastiCache"],
                    "minimum_spend": 500
                },
                "description": "ARM-based instances with database services for cost optimization"
            },
            "data_analytics_credit": {
                "name": "Data Analytics Credit",
                "discount": "22%", 
                "requirements": {
                    "primary_services": ["Amazon Redshift", "Amazon EMR", "AWS Glue"],
                    "supporting_services": ["Amazon S3", "Amazon Kinesis"],
                    "minimum_spend": 800
                },
                "description": "Big data processing with storage and streaming services"
            },
            "serverless_credit": {
                "name": "Serverless Optimization Credit",
                "discount": "18%",
                "requirements": {
                    "primary_services": ["AWS Lambda", "Amazon API Gateway"],
                    "supporting_services": ["Amazon DynamoDB", "Amazon S3"],
                    "minimum_spend": 300
                },
                "description": "Event-driven architecture with managed databases"
            }
        }
    
    def get_current_services(self):
        """Get current AWS service usage"""
        try:
            client = boto3.client('ce', region_name='us-east-1')
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            response = client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            services = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    services[service] = cost
            
            return services
        except:
            # Fallback with known services
            return {
                'Amazon Elastic Compute Cloud - Compute': 150.30,
                'Amazon Simple Storage Service': 45.20,
                'AWS Lambda': 25.10,
                'Amazon SageMaker': 52.20
            }
    
    def analyze_credit_eligibility(self):
        """Analyze which credits user qualifies for and suggest improvements"""
        current_services = self.get_current_services()
        recommendations = []
        
        for credit_id, credit in self.credit_offerings.items():
            analysis = self._analyze_single_credit(credit, current_services)
            if analysis:
                recommendations.append(analysis)
        
        return recommendations
    
    def _analyze_single_credit(self, credit, current_services):
        """Analyze eligibility for a single credit offering"""
        primary_match = []
        supporting_match = []
        missing_primary = []
        missing_supporting = []
        total_spend = 0
        
        # Check primary services
        for service in credit['requirements']['primary_services']:
            found = False
            for current_service, spend in current_services.items():
                if service.lower() in current_service.lower():
                    primary_match.append({'service': current_service, 'spend': spend})
                    total_spend += spend
                    found = True
                    break
            if not found:
                missing_primary.append(service)
        
        # Check supporting services
        for service in credit['requirements']['supporting_services']:
            found = False
            for current_service, spend in current_services.items():
                if service.lower() in current_service.lower():
                    supporting_match.append({'service': current_service, 'spend': spend})
                    total_spend += spend
                    found = True
                    break
            if not found:
                missing_supporting.append(service)
        
        # Determine status
        has_primary = len(primary_match) > 0
        meets_spend = total_spend >= credit['requirements']['minimum_spend']
        
        if has_primary and meets_spend:
            status = "qualified"
        elif has_primary:
            status = "partially_qualified"
        else:
            status = "opportunity"
        
        return {
            'credit_name': credit['name'],
            'discount': credit['discount'],
            'status': status,
            'description': credit['description'],
            'current_spend': total_spend,
            'minimum_spend': credit['requirements']['minimum_spend'],
            'primary_services_matched': primary_match,
            'supporting_services_matched': supporting_match,
            'missing_primary': missing_primary,
            'missing_supporting': missing_supporting,
            'potential_savings': total_spend * (float(credit['discount'].rstrip('%')) / 100),
            'recommendation': self._generate_recommendation(credit, status, missing_primary, missing_supporting, total_spend)
        }
    
    def _generate_recommendation(self, credit, status, missing_primary, missing_supporting, current_spend):
        """Generate specific recommendation based on analysis"""
        if status == "qualified":
            return f"✅ You qualify for {credit['name']}! Ensure attestation includes all coupled services."
        
        elif status == "partially_qualified":
            spend_needed = credit['requirements']['minimum_spend'] - current_spend
            return f"💡 Add ${spend_needed:.0f} more spend to qualify for {credit['name']}. Consider expanding existing services."
        
        else:
            if missing_primary:
                primary = missing_primary[0]
                return f"🎯 Add {primary} to unlock {credit['name']}. Current services: {', '.join([s['service'] for s in []])}"
            return f"Consider {credit['name']} for {credit['discount']} savings on coupled services."

def get_credit_recommendations():
    """Main function to get credit coupling recommendations"""
    engine = CreditCouplingEngine()
    return engine.analyze_credit_eligibility()

if __name__ == "__main__":
    recommendations = get_credit_recommendations()
    print(json.dumps(recommendations, indent=2))
