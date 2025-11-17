#!/usr/bin/env python3
"""
Commitment Intelligent Platform v0.3 - Enhanced Dashboard
Features: Compact layout, toast notifications, calendar integration, email distribution
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
    return render_template_string(DASHBOARD_HTML)

# Enhanced HTML template with all v0.3 features
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Commitment Intelligent Platform v0.3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f8f9fa; 
            color: #333; 
            line-height: 1.6;
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        
        /* Header */
        .header { 
            background: linear-gradient(135deg, #232F3E 0%, #131A22 100%); 
            color: white; 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 { 
            font-size: 2.2em; 
            margin-bottom: 5px; 
            font-weight: 300;
        }
        
        .header .version { 
            color: #FF9900; 
            font-weight: bold; 
            font-size: 0.9em;
        }
        
        /* Compact Layout Grid */
        .main-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        
        /* Setup Section - Moved to top */
        .setup-section { 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
        }
        
        .setup-section h2 { 
            color: #28a745; 
            margin-bottom: 15px; 
            display: flex; 
            align-items: center; 
        }
        
        .setup-section h2::before { 
            content: "⚙️"; 
            margin-right: 10px; 
        }
        
        /* PDF Upload Area - Enhanced */
        .upload-area { 
            border: 2px dashed #ddd; 
            border-radius: 8px; 
            padding: 30px; 
            text-align: center; 
            margin-bottom: 20px; 
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover { 
            border-color: #FF9900; 
            background: #fff8f0; 
        }
        
        .upload-area.dragover { 
            border-color: #28a745; 
            background: #f8fff9; 
        }
        
        /* Analysis Section */
        .analysis-section { 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Buttons - Enhanced */
        .btn { 
            background: #FF9900; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 14px; 
            font-weight: 500;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn:hover { 
            background: #e88900; 
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .btn:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
            transform: none;
            box-shadow: none;
        }
        
        .btn-secondary { 
            background: #6c757d; 
        }
        
        .btn-secondary:hover { 
            background: #545b62; 
        }
        
        .btn-success { 
            background: #28a745; 
        }
        
        .btn-success:hover { 
            background: #218838; 
        }
        
        /* Toast Notifications */
        .toast-container { 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            z-index: 1000; 
        }
        
        .toast { 
            background: white; 
            border-radius: 8px; 
            padding: 16px 20px; 
            margin-bottom: 10px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
            border-left: 4px solid #28a745; 
            min-width: 300px;
            animation: slideIn 0.3s ease;
        }
        
        .toast.error { border-left-color: #dc3545; }
        .toast.warning { border-left-color: #ffc107; }
        .toast.info { border-left-color: #17a2b8; }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Modal System */
        .modal { 
            display: none; 
            position: fixed; 
            z-index: 1000; 
            left: 0; 
            top: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.5); 
        }
        
        .modal-content { 
            background: white; 
            margin: 5% auto; 
            padding: 30px; 
            border-radius: 12px; 
            width: 90%; 
            max-width: 600px; 
            max-height: 80vh; 
            overflow-y: auto;
        }
        
        .modal-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 20px; 
            padding-bottom: 15px; 
            border-bottom: 1px solid #eee;
        }
        
        .close { 
            font-size: 28px; 
            font-weight: bold; 
            cursor: pointer; 
            color: #aaa;
        }
        
        .close:hover { color: #000; }
        
        /* Recommendation Cards */
        .recommendation-card { 
            background: white; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 15px 0; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            border-left: 4px solid #17a2b8;
            transition: transform 0.2s ease;
        }
        
        .recommendation-card:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .recommendation-card.high-priority { border-left-color: #dc3545; }
        .recommendation-card.medium-priority { border-left-color: #ffc107; }
        .recommendation-card.low-priority { border-left-color: #28a745; }
        
        /* Status Indicators */
        .status-indicator { 
            display: inline-block; 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            margin-right: 8px;
        }
        
        .status-connected { background: #28a745; }
        .status-disconnected { background: #dc3545; }
        .status-pending { background: #ffc107; }
        
        /* Loading Spinner */
        .spinner { 
            border: 3px solid #f3f3f3; 
            border-top: 3px solid #FF9900; 
            border-radius: 50%; 
            width: 20px; 
            height: 20px; 
            animation: spin 1s linear infinite; 
            display: inline-block;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Form Elements */
        .form-group { 
            margin-bottom: 20px; 
        }
        
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: 500; 
            color: #555;
        }
        
        .form-control { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 6px; 
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        
        .form-control:focus { 
            outline: none; 
            border-color: #FF9900; 
            box-shadow: 0 0 0 2px rgba(255, 153, 0, 0.2);
        }
        
        /* History Section */
        .history-section { 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-top: 20px;
        }
        
        .history-item { 
            padding: 15px; 
            border-bottom: 1px solid #eee; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
        }
        
        .history-item:last-child { border-bottom: none; }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .modal-content { margin: 10% auto; padding: 20px; }
            .btn { padding: 10px 16px; font-size: 13px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Commitment Intelligent Platform</h1>
            <div class="version">Version 0.3 - Enhanced Dashboard</div>
            <p>AI-powered document analysis with calendar and email integration</p>
        </div>
        
        <!-- Main Grid Layout -->
        <div class="main-grid">
            <!-- Setup Section (Left Column) -->
            <div class="setup-section">
                <h2>Setup & Preparation</h2>
                
                <!-- PDF Upload Area -->
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    <div style="font-size: 48px; margin-bottom: 10px;">📄</div>
                    <h3>Upload PDF Documents</h3>
                    <p>Drag & drop files here or click to browse</p>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">Supported: PDF files up to 16MB</p>
                    <input type="file" id="fileInput" multiple accept=".pdf" style="display: none;">
                </div>
                
                <!-- Integration Status -->
                <div style="margin-bottom: 20px;">
                    <h4>Integration Status</h4>
                    <div style="margin: 10px 0;">
                        <span class="status-indicator status-disconnected"></span>
                        <span>Calendar Integration</span>
                        <button class="btn btn-secondary" style="float: right; padding: 6px 12px; font-size: 12px;" onclick="connectCalendar()">Connect Outlook</button>
                    </div>
                    <div style="margin: 10px 0;">
                        <span class="status-indicator status-disconnected"></span>
                        <span>Email Configuration</span>
                        <button class="btn btn-secondary" style="float: right; padding: 6px 12px; font-size: 12px;" onclick="configureEmail()">Configure</button>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div>
                    <button class="btn" onclick="analyzeDocuments()" id="analyzeBtn">
                        <span>🔍</span> Analyze Documents
                    </button>
                </div>
            </div>
            
            <!-- Analysis Section (Right Column) -->
            <div class="analysis-section">
                <h2>📊 Analysis Results</h2>
                <div id="analysisResults">
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <div style="font-size: 48px; margin-bottom: 15px;">🤖</div>
                        <h3>Ready for Analysis</h3>
                        <p>Upload PDF documents and click "Analyze Documents" to get started</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- History Section -->
        <div class="history-section">
            <h2>📈 Activity History</h2>
            <div id="historyContent">
                <div style="text-align: center; padding: 20px; color: #666;">
                    <p>No activity yet. Start by uploading and analyzing documents.</p>
                </div>
            </div>
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
                <button class="btn btn-secondary" onclick="selectAllEvents()">Select All</button>
                <button class="btn btn-secondary" onclick="deselectAllEvents()">Deselect All</button>
            </div>
            <div id="eventList">
                <!-- Events will be populated here -->
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeModal('eventModal')">Cancel</button>
                <button class="btn" onclick="createSelectedEvents()">Create Events</button>
            </div>
        </div>
    </div>

    <script>
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
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 5000);
        }
        
        // Modal Management
        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }
        
        // File Upload Handling
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                showToast(`${files.length} file(s) selected for upload`, 'info');
                // Handle file upload here
            }
        });
        
        // Drag and Drop
        const uploadArea = document.querySelector('.upload-area');
        
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf');
            if (files.length > 0) {
                showToast(`${files.length} PDF file(s) ready for upload`, 'success');
                // Handle dropped files
            } else {
                showToast('Please drop PDF files only', 'error');
            }
        });
        
        // Analysis Function
        function analyzeDocuments() {
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Analyzing...';
            
            showToast('Starting document analysis...', 'info');
            
            // Simulate analysis
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = '<span>🔍</span> Analyze Documents';
                showToast('Analysis completed successfully!', 'success');
                displaySampleRecommendations();
            }, 3000);
        }
        
        // Display Sample Recommendations
        function displaySampleRecommendations() {
            const resultsDiv = document.getElementById('analysisResults');
            resultsDiv.innerHTML = `
                <div class="recommendation-card high-priority">
                    <h4>🔴 High Priority: Process Optimization</h4>
                    <p>Identified inefficiencies in document workflow that could save 25% processing time.</p>
                    <div style="margin-top: 15px;">
                        <button class="btn btn-success" onclick="acceptRecommendation('rec-1')">Accept</button>
                        <button class="btn btn-secondary" onclick="rejectRecommendation('rec-1')">Reject</button>
                    </div>
                </div>
                <div class="recommendation-card medium-priority">
                    <h4>🟡 Medium Priority: Cost Reduction</h4>
                    <p>Potential cost savings of $15,000 annually through vendor consolidation.</p>
                    <div style="margin-top: 15px;">
                        <button class="btn btn-success" onclick="acceptRecommendation('rec-2')">Accept</button>
                        <button class="btn btn-secondary" onclick="rejectRecommendation('rec-2')">Reject</button>
                    </div>
                </div>
            `;
        }
        
        // Recommendation Actions
        function acceptRecommendation(id) {
            showToast('Recommendation accepted! Opening event creation...', 'success');
            openModal('eventModal');
            populateEventModal(id);
        }
        
        function rejectRecommendation(id) {
            showToast('Recommendation rejected', 'info');
        }
        
        // Calendar Integration
        function connectCalendar() {
            showToast('Redirecting to Microsoft authentication...', 'info');
            // Simulate OAuth flow
            setTimeout(() => {
                showToast('Calendar connected successfully!', 'success');
                updateConnectionStatus('calendar', true);
            }, 2000);
        }
        
        // Email Configuration
        function configureEmail() {
            openModal('emailModal');
        }
        
        function saveEmailConfig() {
            showToast('Email configuration saved!', 'success');
            closeModal('emailModal');
            updateConnectionStatus('email', true);
        }
        
        // Event Management
        function populateEventModal(recommendationId) {
            const eventList = document.getElementById('eventList');
            eventList.innerHTML = `
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" checked> Implementation Planning Meeting
                        <div style="margin-left: 20px; font-size: 12px; color: #666;">
                            Tomorrow 2:00 PM - 3:00 PM
                        </div>
                    </label>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" checked> Team Review Session
                        <div style="margin-left: 20px; font-size: 12px; color: #666;">
                            Next Week Monday 10:00 AM - 11:00 AM
                        </div>
                    </label>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox"> Follow-up Assessment
                        <div style="margin-left: 20px; font-size: 12px; color: #666;">
                            In 2 weeks Friday 3:00 PM - 4:00 PM
                        </div>
                    </label>
                </div>
            `;
        }
        
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
                }, 1500);
            } else {
                showToast('Please select at least one event to create', 'warning');
            }
        }
        
        // Update Connection Status
        function updateConnectionStatus(type, connected) {
            const indicators = document.querySelectorAll('.status-indicator');
            // Update status indicators based on connection type
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            showToast('Welcome to Commitment Intelligent Platform v0.3!', 'info');
        });
    </script>
</body>
</html>
'''
"""
Flask Routes for Commitment Intelligent Platform v0.3
API endpoints for file upload, analysis, calendar, and email integration
"""

from flask import jsonify, request, redirect, session
import json
import os
from datetime import datetime

def render_template_string(template):
    """Simple template renderer"""
    return template

# API Routes
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file uploads"""
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

@app.route('/analyze', methods=['POST'])
def analyze_documents():
    """Analyze uploaded documents and generate recommendations"""
    try:
        data = request.get_json() or {}
        files = data.get('files', [])
        
        # Simulate AI analysis
        recommendations = [
            {
                'id': 'rec-1',
                'title': 'Process Optimization Opportunity',
                'description': 'Identified workflow inefficiencies that could reduce processing time by 25%',
                'priority': 'high',
                'category': 'process_improvement',
                'estimated_impact': 'significant',
                'implementation_effort': 'medium',
                'confidence_score': 0.85,
                'estimated_savings': '$50,000 annually'
            },
            {
                'id': 'rec-2',
                'title': 'Cost Reduction Initiative',
                'description': 'Vendor consolidation opportunity with potential annual savings',
                'priority': 'medium',
                'category': 'cost_optimization',
                'estimated_impact': 'moderate',
                'implementation_effort': 'low',
                'confidence_score': 0.72,
                'estimated_savings': '$15,000 annually'
            },
            {
                'id': 'rec-3',
                'title': 'Compliance Enhancement',
                'description': 'Strengthen compliance processes to reduce audit risks',
                'priority': 'high',
                'category': 'compliance',
                'estimated_impact': 'high',
                'implementation_effort': 'high',
                'confidence_score': 0.91,
                'estimated_savings': 'Risk mitigation'
            }
        ]
        
        return jsonify({
            'success': True,
            'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'recommendations': recommendations,
            'summary': f'Analyzed {len(files)} document(s) and generated {len(recommendations)} recommendations'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/accept_recommendation', methods=['POST'])
def accept_recommendation():
    """Accept a recommendation and trigger workflow"""
    try:
        data = request.get_json()
        recommendation_id = data.get('recommendation_id')
        user_notes = data.get('user_notes', '')
        create_calendar_event = data.get('create_calendar_event', False)
        send_notifications = data.get('send_notifications', False)
        email_recipients = data.get('email_recipients', [])
        
        # Process recommendation acceptance
        result = {
            'success': True,
            'message': 'Recommendation accepted successfully',
            'recommendation_id': recommendation_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Create calendar event if requested
        if create_calendar_event:
            if calendar_client.is_connected():
                event_data = {
                    'title': f'Implementation: {recommendation_id}',
                    'description': f'Implementation meeting for recommendation {recommendation_id}',
                    'start_time': (datetime.now() + timedelta(days=1)).isoformat(),
                    'end_time': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                    'attendees': email_recipients
                }
                calendar_result = calendar_client.create_calendar_event(event_data)
                result['calendar_event'] = calendar_result
            else:
                result['calendar_event'] = calendar_client.simulate_event_creation({
                    'title': f'Implementation: {recommendation_id}'
                })
        
        # Send email notifications if requested
        if send_notifications and email_recipients:
            email_data = {
                'title': f'Recommendation {recommendation_id}',
                'description': 'Implementation planning required',
                'priority': 'High',
                'user_notes': user_notes,
                'implementation_date': 'Tomorrow'
            }
            
            if email_client.username and email_client.password:
                email_result = email_client.send_recommendation_notification(email_data, email_recipients)
                result['email_sent'] = email_result
            else:
                result['email_sent'] = email_client.simulate_email_send(
                    email_recipients, 
                    f'Recommendation Accepted: {recommendation_id}',
                    email_data
                )
        
        # Store in history (simulate with session for demo)
        if 'recommendation_history' not in session:
            session['recommendation_history'] = []
        
        session['recommendation_history'].append({
            'id': recommendation_id,
            'status': 'accepted',
            'timestamp': datetime.now().isoformat(),
            'user_notes': user_notes
        })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get recommendation history"""
    try:
        history = session.get('recommendation_history', [])
        
        return jsonify({
            'success': True,
            'recommendations': history,
            'total': len(history)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/auth/login')
def auth_login():
    """Initiate Microsoft OAuth2 authentication"""
    try:
        auth_url = calendar_client.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth2 callback"""
    try:
        auth_code = request.args.get('code')
        if not auth_code:
            return jsonify({'success': False, 'error': 'No authorization code received'})
        
        token_result = calendar_client.exchange_code_for_token(auth_code)
        
        if token_result['success']:
            user_info = calendar_client.get_user_info()
            session['calendar_connected'] = True
            session['user_info'] = user_info.get('user', {})
            
            return '''
            <html>
            <body>
                <h2>Calendar Connected Successfully!</h2>
                <p>You can now close this window and return to the dashboard.</p>
                <script>
                    setTimeout(() => {
                        window.close();
                    }, 2000);
                </script>
            </body>
            </html>
            '''
        else:
            return jsonify({'success': False, 'error': token_result.get('error')})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create_calendar_events', methods=['POST'])
def create_calendar_events():
    """Create calendar events from recommendations"""
    try:
        data = request.get_json()
        events = data.get('events', [])
        
        created_events = []
        failed_events = []
        
        for event_data in events:
            if calendar_client.is_connected():
                result = calendar_client.create_calendar_event(event_data)
            else:
                result = calendar_client.simulate_event_creation(event_data)
            
            if result['success']:
                created_events.append({
                    'recommendation_id': event_data.get('recommendation_id'),
                    'event_id': result.get('event_id'),
                    'web_link': result.get('web_link'),
                    'status': 'created'
                })
            else:
                failed_events.append({
                    'recommendation_id': event_data.get('recommendation_id'),
                    'error': result.get('error')
                })
        
        return jsonify({
            'success': True,
            'created_events': created_events,
            'failed_events': failed_events
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/configure_email', methods=['POST'])
def configure_email():
    """Configure email settings"""
    try:
        data = request.get_json()
        predefined_teams = data.get('predefined_teams', [])
        custom_emails = data.get('custom_emails', [])
        
        # Store email configuration in session (in production, use database)
        session['email_config'] = {
            'predefined_teams': predefined_teams,
            'custom_emails': custom_emails,
            'configured_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Email configuration saved successfully',
            'config_id': f"email_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_emails', methods=['POST'])
def send_emails():
    """Send email notifications"""
    try:
        data = request.get_json()
        template = data.get('template', 'recommendation_accepted')
        recipients = data.get('recipients', [])
        email_data = data.get('data', {})
        
        if email_client.username and email_client.password:
            result = email_client.send_email(
                recipients=recipients,
                subject=f"Recommendation Update: {email_data.get('recommendation_title', 'Update')}",
                template_type=template,
                data=email_data
            )
        else:
            result = email_client.simulate_email_send(recipients, 'Recommendation Update', email_data)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/events', methods=['GET'])
def get_events():
    """Get event history"""
    try:
        # Simulate event history
        events = [
            {
                'id': 'event-1',
                'type': 'recommendation',
                'status': 'created',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'recommendation_id': 'rec-1',
                    'title': 'Process Optimization',
                    'action': 'accepted'
                }
            }
        ]
        
        return jsonify({
            'success': True,
            'events': events,
            'total': len(events)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/attestation_history', methods=['GET'])
def get_attestation_history():
    """Get attestation history"""
    try:
        # Simulate attestation history
        attestations = [
            {
                'id': 'att-1',
                'recommendation_id': 'rec-1',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'implementation_date': '2024-12-01',
                'assigned_team': 'operations',
                'progress': 25
            }
        ]
        
        return jsonify({
            'success': True,
            'attestations': attestations,
            'total': len(attestations)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '0.3.0',
        'integrations': {
            'microsoft_graph': 'connected' if calendar_client.is_connected() else 'disconnected',
            'email_smtp': 'configured' if email_client.username else 'not_configured'
        }
    })

@app.route('/system_status')
def system_status():
    """System status endpoint"""
    return jsonify({
        'success': True,
        'system': {
            'uptime': 'Running',
            'version': '0.3.0'
        },
        'integrations': {
            'microsoft_graph': {
                'status': 'connected' if calendar_client.is_connected() else 'disconnected'
            },
            'email_smtp': {
                'status': 'configured' if email_client.username else 'not_configured'
            }
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
