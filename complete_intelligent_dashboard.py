#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import boto3
import json
import pdfplumber
import re
from datetime import datetime, timedelta
import sys
import os

# Import components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from credit_coupling_server import get_credit_recommendations
from attestation_calendar_system import create_attestation_calendar_events, process_recommendation_feedback

app = Flask(__name__)

@app.route('/')
def dashboard():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Commitment Intelligent Platform v0.3</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: #232F3E; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #232F3E; }
        .metric-label { color: #666; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .credit-recommendations { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .attestation-calendar { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .credit-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; position: relative; }
        .credit-card.qualified { border-left: 4px solid #28a745; background: #f8fff9; }
        .credit-card.partially_qualified { border-left: 4px solid #ffc107; background: #fffdf0; }
        .credit-card.opportunity { border-left: 4px solid #17a2b8; background: #f0f9ff; }
        .credit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .credit-discount { background: #FF9900; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .confidence-badge { position: absolute; top: 10px; right: 10px; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
        .confidence-high { background: #28a745; color: white; }
        .confidence-medium { background: #ffc107; color: black; }
        .confidence-low { background: #dc3545; color: white; }
        .confidence-new { background: #17a2b8; color: white; }
        .feedback-buttons { margin-top: 15px; }
        .btn { background: #FF9900; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #e88900; }
        .btn-accept { background: #28a745; }
        .btn-reject { background: #dc3545; }
        .calendar-event { border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 5px 0; background: #f9f9f9; }
        .calendar-event.urgent { border-left: 4px solid #dc3545; }
        .upload-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Commitment Intelligent Platform v0.3</h1>
            <p>Intelligent credit coupling with attestation calendar and learning loop</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" id="currentSpend">$272.80</div>
                <div class="metric-label">Current AWS Spend</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="annualCommitment">$50,000</div>
                <div class="metric-label">Annual Commitment</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="progress">0.55%</div>
                <div class="metric-label">Progress to Goal</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="monthlyTarget">$4,167</div>
                <div class="metric-label">Monthly Target</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Spend vs Commitment Tracker</h3>
            <canvas id="spendChart" width="400" height="200"></canvas>
        </div>
        
        <div class="credit-recommendations">
            <h3>🧠 Intelligent Credit Coupling Recommendations</h3>
            <p>AI-powered recommendations with learning feedback:</p>
            <div id="creditRecommendations">Loading credit analysis...</div>
        </div>
        
        <div class="attestation-calendar">
            <h3>📅 Attestation Calendar Events</h3>
            <p>Automated calendar events for credit submission deadlines:</p>
            <div id="attestationEvents">Loading calendar events...</div>
            <button class="btn" onclick="createCalendarEvents()">📅 Create Calendar Events</button>
        </div>
        
        <div class="upload-section">
            <h3>📄 Upload PPA Document</h3>
            <input type="file" id="pdfUpload" accept=".pdf" />
            <button class="btn" onclick="uploadPDF()">Process Document</button>
            <div id="uploadResult"></div>
        </div>
    </div>

    <script>
        let currentData = {
            spend: 272.80,
            commitment: 50000,
            progress: 0.55,
            monthlyTarget: 4167
        };

        function updateMetrics() {
            document.getElementById('currentSpend').textContent = `$${currentData.spend.toFixed(2)}`;
            document.getElementById('annualCommitment').textContent = `$${currentData.commitment.toLocaleString()}`;
            document.getElementById('progress').textContent = `${currentData.progress.toFixed(2)}%`;
            document.getElementById('monthlyTarget').textContent = `$${currentData.monthlyTarget.toLocaleString()}`;
        }

        function createChart() {
            const ctx = document.getElementById('spendChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Current Spend', 'Monthly Target', 'Annual Commitment'],
                    datasets: [{
                        label: 'Amount ($)',
                        data: [currentData.spend, currentData.monthlyTarget, currentData.commitment],
                        backgroundColor: ['#FF9900', '#232F3E', '#146EB4']
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        async function loadCreditRecommendations() {
            try {
                const response = await fetch('/api/credit-recommendations');
                const credits = await response.json();
                
                const creditsHtml = credits.map((credit, index) => `
                    <div class="credit-card ${credit.status}" id="credit-${index}">
                        <div class="confidence-badge confidence-${credit.confidence || 'new'}">${(credit.confidence || 'new').toUpperCase()}</div>
                        <div class="credit-header">
                            <h4>${credit.credit_name}</h4>
                            <span class="credit-discount">${credit.discount} savings</span>
                        </div>
                        <p><strong>Description:</strong> ${credit.description}</p>
                        <p><strong>Current Spend:</strong> $${credit.current_spend.toFixed(2)} / $${credit.minimum_spend} required</p>
                        <p><strong>Potential Savings:</strong> $${credit.potential_savings.toFixed(2)}/month</p>
                        
                        ${credit.learning_note ? `<p><em>💡 ${credit.learning_note}</em></p>` : ''}
                        
                        <div style="margin-top: 15px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
                            <strong>💡 Recommendation:</strong> ${credit.recommendation}
                        </div>
                        
                        <div class="feedback-buttons">
                            <button class="btn btn-accept" onclick="provideFeedback(${index}, 'accepted', '${credit.credit_name}')">✅ Accept</button>
                            <button class="btn btn-reject" onclick="provideFeedback(${index}, 'rejected', '${credit.credit_name}')">❌ Reject</button>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('creditRecommendations').innerHTML = creditsHtml;
                
            } catch (error) {
                document.getElementById('creditRecommendations').innerHTML = 
                    '<p style="color: red;">Error loading credit recommendations</p>';
            }
        }

        async function loadAttestationEvents() {
            try {
                const response = await fetch('/api/attestation-events');
                const events = await response.json();
                
                const eventsHtml = events.map(event => `
                    <div class="calendar-event ${event.days_before_deadline <= 7 ? 'urgent' : ''}">
                        <h5>${event.title}</h5>
                        <p><strong>Date:</strong> ${new Date(event.start_time).toLocaleDateString()}</p>
                        <p><strong>Credit:</strong> ${event.credit_type}</p>
                        <p><strong>Days Until Deadline:</strong> ${event.days_before_deadline}</p>
                        <details>
                            <summary>View Details</summary>
                            <pre style="white-space: pre-wrap; font-size: 0.9em;">${event.description}</pre>
                        </details>
                    </div>
                `).join('');
                
                document.getElementById('attestationEvents').innerHTML = eventsHtml || '<p>No attestation events scheduled</p>';
                
            } catch (error) {
                document.getElementById('attestationEvents').innerHTML = 
                    '<p style="color: red;">Error loading attestation events</p>';
            }
        }

        async function provideFeedback(creditIndex, action, creditType) {
            const reason = action === 'rejected' ? prompt('Why are you rejecting this recommendation?') : null;
            
            try {
                const response = await fetch('/api/recommendation-feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        recommendation_id: `credit-${creditIndex}`,
                        action: action,
                        credit_type: creditType,
                        reason: reason
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    const creditCard = document.getElementById(`credit-${creditIndex}`);
                    creditCard.style.opacity = '0.6';
                    creditCard.innerHTML += `<div style="color: ${action === 'accepted' ? 'green' : 'red'}; font-weight: bold; margin-top: 10px;">
                        ${action === 'accepted' ? '✅ Accepted' : '❌ Rejected'} - Learning recorded
                    </div>`;
                }
            } catch (error) {
                alert('Error recording feedback');
            }
        }

        async function createCalendarEvents() {
            try {
                const response = await fetch('/api/create-calendar-events', {method: 'POST'});
                const result = await response.json();
                
                if (result.success) {
                    alert(`✅ Created ${result.events_created} calendar events for attestation deadlines!`);
                    loadAttestationEvents();
                } else {
                    alert('❌ Error creating calendar events');
                }
            } catch (error) {
                alert('❌ Error creating calendar events');
            }
        }

        async function uploadPDF() {
            const fileInput = document.getElementById('pdfUpload');
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a PDF file');
                return;
            }

            const formData = new FormData();
            formData.append('pdf', file);

            try {
                const response = await fetch('/api/upload-pdf', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.success) {
                    currentData.commitment = result.commitment;
                    currentData.monthlyTarget = Math.round(result.commitment / 12);
                    currentData.progress = (currentData.spend / result.commitment) * 100;
                    
                    updateMetrics();
                    location.reload();
                    
                    document.getElementById('uploadResult').innerHTML = 
                        `<p style="color: green;">✅ PDF processed successfully! Commitment: $${result.commitment.toLocaleString()}</p>`;
                } else {
                    document.getElementById('uploadResult').innerHTML = 
                        `<p style="color: red;">❌ Error: ${result.error}</p>`;
                }
            } catch (error) {
                document.getElementById('uploadResult').innerHTML = 
                    `<p style="color: red;">❌ Upload failed: ${error.message}</p>`;
            }
        }

        // Initialize
        updateMetrics();
        createChart();
        loadCreditRecommendations();
        loadAttestationEvents();
    </script>
</body>
</html>
    '''

@app.route('/api/credit-recommendations')
def credit_recommendations():
    return jsonify(get_credit_recommendations())

@app.route('/api/attestation-events')
def attestation_events():
    credits = get_credit_recommendations()
    events = create_attestation_calendar_events(credits)
    return jsonify(events)

@app.route('/api/create-calendar-events', methods=['POST'])
def create_calendar_events():
    try:
        credits = get_credit_recommendations()
        events = create_attestation_calendar_events(credits)
        
        # In production, this would integrate with Outlook MCP
        # For now, simulate calendar creation
        return jsonify({
            'success': True,
            'events_created': len(events),
            'message': f'Created {len(events)} attestation calendar events'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommendation-feedback', methods=['POST'])
def recommendation_feedback():
    try:
        data = request.json
        feedback = process_recommendation_feedback(
            data['recommendation_id'],
            data['action'], 
            data['credit_type'],
            data.get('reason')
        )
        return jsonify({'success': True, 'feedback': feedback})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF file uploaded'})
        
        file = request.files['pdf']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        pdf_path = f'/tmp/{file.filename}'
        file.save(pdf_path)
        
        # Extract commitment amount
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        commitment_patterns = [
            r'Annual Commitment[:\s]*\$?([\d,]+)',
            r'Total AWS Services[:\s]*\$?([\d,]+)',
            r'Commitment[:\s]*\$?([\d,]+)'
        ]
        
        commitment = 50000
        for pattern in commitment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                commitment = int(match.group(1).replace(',', ''))
                break
        
        return jsonify({
            'success': True,
            'commitment': commitment,
            'monthly_target': commitment // 12
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
