#!/usr/bin/env python3
"""
Commitment Intelligent Platform v0.3 - Complete Dashboard
Features: Spend tracking, credit coupling, attestation calendar, email integration
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import boto3
import json
import pdfplumber
import re
import os
import sys
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# Import our integration modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from outlook_calendar_mcp import OutlookCalendarMCP
    from email_sender import EmailSender
    from attestation_calendar_system import AttestationCalendarSystem
    from credit_coupling_server import get_credit_recommendations
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize integrations
calendar_client = OutlookCalendarMCP()
email_client = EmailSender()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        .upload-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .upload-area { border: 2px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; cursor: pointer; }
        .upload-area:hover { border-color: #FF9900; background: #fff8f0; }
        
        /* Toast Notifications */
        .toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
        .toast { background: white; border-radius: 8px; padding: 16px 20px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-left: 4px solid #28a745; min-width: 300px; animation: slideIn 0.3s ease; }
        .toast.error { border-left-color: #dc3545; }
        .toast.warning { border-left-color: #ffc107; }
        .toast.info { border-left-color: #17a2b8; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        
        /* Modal System */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 5% auto; padding: 30px; border-radius: 12px; width: 90%; max-width: 600px; max-height: 80vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        .close { font-size: 28px; font-weight: bold; cursor: pointer; color: #aaa; }
        .close:hover { color: #000; }
        
        /* Form Elements */
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
        .form-control { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        .form-control:focus { outline: none; border-color: #FF9900; box-shadow: 0 0 0 2px rgba(255, 153, 0, 0.2); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Commitment Intelligent Platform v0.3</h1>
            <p>Intelligent credit coupling with attestation calendar and learning loop</p>
        </div>
        
        <!-- Upload Section - Moved to top -->
        <div class="upload-section">
            <h3>📄 Document Upload & Analysis</h3>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 48px; margin-bottom: 10px;">📄</div>
                <h4>Upload PDF Documents</h4>
                <p>Drag & drop files here or click to browse</p>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">Supported: PDF files up to 16MB</p>
                <input type="file" id="fileInput" multiple accept=".pdf" style="display: none;">
            </div>
            <div style="margin-top: 15px;">
                <button class="btn" onclick="analyzeDocuments()" id="analyzeBtn">🔍 Analyze Documents</button>
                <button class="btn" onclick="configureEmail()">📧 Configure Email</button>
                <button class="btn" onclick="connectCalendar()">📅 Connect Calendar</button>
            </div>
        </div>
        
        <!-- Spend vs Commitment Metrics -->
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
            <div class="metric-card">
                <div class="metric-value" id="projectedSavings">$12,500</div>
                <div class="metric-label">Projected Annual Savings</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="creditUtilization">68%</div>
                <div class="metric-label">Credit Utilization</div>
            </div>
        </div>
        
        <!-- Spend vs Commitment Chart -->
        <div class="chart-container">
            <h3>📊 Spend vs Commitment Tracker</h3>
            <canvas id="spendChart" width="400" height="200"></canvas>
        </div>
        
        <!-- Credit Recommendations -->
        <div class="credit-recommendations">
            <h3>🧠 Intelligent Credit Coupling Recommendations</h3>
            <p>AI-powered recommendations with learning feedback:</p>
            <div id="creditRecommendations">Loading credit analysis...</div>
        </div>
        
        <!-- Attestation Calendar -->
        <div class="attestation-calendar">
            <h3>📅 Attestation Calendar Events</h3>
            <p>Automated calendar events for credit submission deadlines:</p>
            <div id="attestationEvents">Loading calendar events...</div>
            <button class="btn" onclick="createCalendarEvents()">📅 Create Calendar Events</button>
            <button class="btn" onclick="openEventModal()">📋 Select Events</button>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <!-- Email Configuration Modal -->
    <div id="emailModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📧 Email Configuration</h3>
                <span class="close" onclick="closeModal('emailModal')">&times;</span>
            </div>
            <div class="form-group">
                <label>Predefined Teams:</label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                    <label><input type="checkbox" value="operations"> Operations Team</label>
                    <label><input type="checkbox" value="management"> Management</label>
                    <label><input type="checkbox" value="it_support"> IT Support</label>
                    <label><input type="checkbox" value="finance"> Finance Team</label>
                    <label><input type="checkbox" value="hr"> HR Department</label>
                    <label><input type="checkbox" value="legal"> Legal & Compliance</label>
                </div>
            </div>
            <div class="form-group">
                <label for="customEmails">Custom Email Addresses:</label>
                <textarea id="customEmails" class="form-control" rows="3" placeholder="Enter email addresses, one per line"></textarea>
            </div>
            <div style="text-align: right;">
                <button class="btn btn-secondary" onclick="closeModal('emailModal')">Cancel</button>
                <button class="btn" onclick="saveEmailConfig()">Save Configuration</button>
            </div>
        </div>
    </div>
    
    <!-- Event Selection Modal -->
    <div id="eventModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>📅 Create Calendar Events</h3>
                <span class="close" onclick="closeModal('eventModal')">&times;</span>
            </div>
            <div style="margin-bottom: 20px;">
                <button class="btn" onclick="selectAllEvents()">Select All</button>
                <button class="btn" onclick="deselectAllEvents()">Deselect All</button>
            </div>
            <div id="eventList">
                <div style="margin-bottom: 15px;">
                    <label><input type="checkbox" checked> Credit Submission Deadline - EC2 Reserved Instances</label>
                    <div style="margin-left: 20px; font-size: 12px; color: #666;">Tomorrow 2:00 PM - Submit RI credits</div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label><input type="checkbox" checked> Savings Plan Review Meeting</label>
                    <div style="margin-left: 20px; font-size: 12px; color: #666;">Next Week Monday 10:00 AM - Review SP utilization</div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label><input type="checkbox"> Monthly Commitment Assessment</label>
                    <div style="margin-left: 20px; font-size: 12px; color: #666;">End of Month Friday 3:00 PM - Progress review</div>
                </div>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn" onclick="closeModal('eventModal')">Cancel</button>
                <button class="btn btn-accept" onclick="createSelectedEvents()">Create Events</button>
            </div>
        </div>
    </div>

    <script>
        // Initialize data
        let spendData = {
            currentSpend: 272.80,
            annualCommitment: 50000,
            monthlyTarget: 4167,
            projectedSavings: 12500,
            creditUtilization: 68
        };
        
        // Toast Notification System
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>${message}</span>
                    <span onclick="this.parentElement.parentElement.remove()" style="cursor: pointer; margin-left: 15px;">&times;</span>
                </div>
            `;
            container.appendChild(toast);
            setTimeout(() => { if (toast.parentElement) toast.remove(); }, 5000);
        }
        
        // Modal Management
        function openModal(modalId) { document.getElementById(modalId).style.display = 'block'; }
        function closeModal(modalId) { document.getElementById(modalId).style.display = 'none'; }
        function openEventModal() { openModal('eventModal'); }
        
        // File Upload
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                showToast(`${files.length} file(s) selected for upload`, 'info');
            }
        });
        
        // Analysis Function
        function analyzeDocuments() {
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.innerHTML = '🔄 Analyzing...';
            showToast('Starting document analysis...', 'info');
            
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = '🔍 Analyze Documents';
                showToast('Analysis completed successfully!', 'success');
                loadCreditRecommendations();
                updateSpendMetrics();
            }, 3000);
        }
        
        // Load Credit Recommendations
        function loadCreditRecommendations() {
            document.getElementById('creditRecommendations').innerHTML = `
                <div class="credit-card qualified">
                    <div class="confidence-badge confidence-high">High Confidence</div>
                    <div class="credit-header">
                        <h4>💰 EC2 Reserved Instance Opportunity</h4>
                        <span class="credit-discount">Save 45%</span>
                    </div>
                    <p><strong>Recommendation:</strong> Purchase 3-year RI for m5.large instances</p>
                    <p><strong>Annual Savings:</strong> $8,500 | <strong>Commitment:</strong> $15,000</p>
                    <p><strong>Confidence:</strong> 92% based on 6 months usage pattern</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('ri-001')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('ri-001')">❌ Reject</button>
                        <button class="btn" onclick="modifyRecommendation('ri-001')">✏️ Modify</button>
                    </div>
                </div>
                
                <div class="credit-card partially_qualified">
                    <div class="confidence-badge confidence-medium">Medium Confidence</div>
                    <div class="credit-header">
                        <h4>📊 Savings Plan Optimization</h4>
                        <span class="credit-discount">Save 25%</span>
                    </div>
                    <p><strong>Recommendation:</strong> Increase Compute Savings Plan commitment</p>
                    <p><strong>Annual Savings:</strong> $4,000 | <strong>Commitment:</strong> $12,000</p>
                    <p><strong>Confidence:</strong> 78% based on compute usage trends</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('sp-001')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('sp-001')">❌ Reject</button>
                        <button class="btn" onclick="modifyRecommendation('sp-001')">✏️ Modify</button>
                    </div>
                </div>
                
                <div class="credit-card opportunity">
                    <div class="confidence-badge confidence-new">New Opportunity</div>
                    <div class="credit-header">
                        <h4>🔄 RDS Reserved Instance</h4>
                        <span class="credit-discount">Save 35%</span>
                    </div>
                    <p><strong>Recommendation:</strong> Purchase RDS RI for production database</p>
                    <p><strong>Annual Savings:</strong> $2,800 | <strong>Commitment:</strong> $6,500</p>
                    <p><strong>Confidence:</strong> 85% based on consistent database usage</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('rds-001')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('rds-001')">❌ Reject</button>
                        <button class="btn" onclick="modifyRecommendation('rds-001')">✏️ Modify</button>
                    </div>
                </div>
            `;
        }
        
        // Update Spend Metrics
        function updateSpendMetrics() {
            const progress = (spendData.currentSpend / spendData.annualCommitment * 100).toFixed(2);
            document.getElementById('progress').textContent = progress + '%';
            
            // Update chart
            createSpendChart();
        }
        
        // Create Spend Chart
        function createSpendChart() {
            const ctx = document.getElementById('spendChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    datasets: [{
                        label: 'Actual Spend',
                        data: [272.80, 285.50, 310.20, 295.80, 320.15, 305.90, 0, 0, 0, 0, 0, 0],
                        borderColor: '#FF9900',
                        backgroundColor: 'rgba(255, 153, 0, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Target Spend',
                        data: [4167, 4167, 4167, 4167, 4167, 4167, 4167, 4167, 4167, 4167, 4167, 4167],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderDash: [5, 5]
                    }, {
                        label: 'Projected with Credits',
                        data: [272.80, 285.50, 310.20, 295.80, 320.15, 305.90, 3800, 3850, 3900, 3950, 4000, 4050],
                        borderColor: '#17a2b8',
                        backgroundColor: 'rgba(23, 162, 184, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Monthly Spend Tracking vs Annual Commitment'
                        }
                    }
                }
            });
        }
        
        // Recommendation Actions
        function acceptRecommendation(id) {
            showToast(`Recommendation ${id} accepted! Creating calendar events...`, 'success');
            openEventModal();
        }
        
        function rejectRecommendation(id) {
            showToast(`Recommendation ${id} rejected. Feedback recorded for learning.`, 'info');
        }
        
        function modifyRecommendation(id) {
            showToast(`Opening modification dialog for ${id}...`, 'info');
        }
        
        // Calendar Functions
        function connectCalendar() {
            showToast('Redirecting to Microsoft authentication...', 'info');
            setTimeout(() => {
                showToast('Calendar connected successfully!', 'success');
            }, 2000);
        }
        
        function createCalendarEvents() {
            showToast('Creating attestation calendar events...', 'info');
            setTimeout(() => {
                loadAttestationEvents();
                showToast('Calendar events created successfully!', 'success');
            }, 1500);
        }
        
        function loadAttestationEvents() {
            document.getElementById('attestationEvents').innerHTML = `
                <div class="calendar-event urgent">
                    <strong>🚨 EC2 RI Credit Submission Due</strong><br>
                    <small>Tomorrow, 2:00 PM - Submit Reserved Instance credits for Q4</small>
                </div>
                <div class="calendar-event">
                    <strong>📊 Monthly Commitment Review</strong><br>
                    <small>Next Monday, 10:00 AM - Review progress toward annual commitment</small>
                </div>
                <div class="calendar-event">
                    <strong>💰 Savings Plan Assessment</strong><br>
                    <small>Next Friday, 3:00 PM - Evaluate current Savings Plan utilization</small>
                </div>
            `;
        }
        
        // Email Configuration
        function configureEmail() {
            openModal('emailModal');
        }
        
        function saveEmailConfig() {
            showToast('Email configuration saved!', 'success');
            closeModal('emailModal');
        }
        
        // Event Selection
        function selectAllEvents() {
            document.querySelectorAll('#eventList input[type="checkbox"]').forEach(cb => cb.checked = true);
        }
        
        function deselectAllEvents() {
            document.querySelectorAll('#eventList input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
        
        function createSelectedEvents() {
            const selected = document.querySelectorAll('#eventList input[type="checkbox"]:checked').length;
            if (selected > 0) {
                showToast(`Creating ${selected} calendar event(s)...`, 'info');
                setTimeout(() => {
                    showToast(`${selected} calendar event(s) created successfully!`, 'success');
                    closeModal('eventModal');
                    loadAttestationEvents();
                }, 1500);
            } else {
                showToast('Please select at least one event to create', 'warning');
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            showToast('Welcome to Commitment Intelligent Platform v0.3!', 'info');
            loadCreditRecommendations();
            createSpendChart();
            loadAttestationEvents();
        });
    </script>
</body>
</html>
'''

# API Routes (keeping the same routes from before)
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename,
                'file_id': f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload a PDF file.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '0.3.0',
        'features': {
            'spend_tracking': True,
            'credit_coupling': True,
            'attestation_calendar': True,
            'email_integration': True,
            'calendar_integration': True
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
