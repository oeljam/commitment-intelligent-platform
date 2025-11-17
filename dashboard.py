#!/usr/bin/env python3
"""
Commitment Intelligent Platform v0.3 - Fixed Dashboard
Focus: Workload qualification for credits, proper feedback, history tracking
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
        .history-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .credit-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; position: relative; }
        .credit-card.qualified { border-left: 4px solid #28a745; background: #f8fff9; }
        .credit-card.partially_qualified { border-left: 4px solid #ffc107; background: #fffdf0; }
        .credit-card.not_qualified { border-left: 4px solid #dc3545; background: #fff5f5; }
        .credit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .credit-discount { background: #FF9900; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .confidence-badge { position: absolute; top: 10px; right: 10px; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
        .confidence-high { background: #28a745; color: white; }
        .confidence-medium { background: #ffc107; color: black; }
        .confidence-low { background: #dc3545; color: white; }
        .feedback-buttons { margin-top: 15px; }
        .btn { background: #FF9900; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #e88900; }
        .btn-accept { background: #28a745; }
        .btn-reject { background: #dc3545; }
        .upload-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .upload-area { border: 2px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; cursor: pointer; }
        .upload-area:hover { border-color: #FF9900; background: #fff8f0; }
        .history-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .history-item:last-child { border-bottom: none; }
        .history-item.accepted { border-left: 4px solid #28a745; }
        .history-item.rejected { border-left: 4px solid #dc3545; }
        
        /* Toast Notifications */
        .toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
        .toast { background: white; border-radius: 8px; padding: 16px 20px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-left: 4px solid #28a745; min-width: 300px; animation: slideIn 0.3s ease; }
        .toast.error { border-left-color: #dc3545; }
        .toast.warning { border-left-color: #ffc107; }
        .toast.info { border-left-color: #17a2b8; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Commitment Intelligent Platform v0.3</h1>
            <p>Workload qualification for AWS credits and commitment tracking</p>
        </div>
        
        <!-- Upload Section -->
        <div class="upload-section">
            <h3>📄 Document Upload & Analysis</h3>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 48px; margin-bottom: 10px;">📄</div>
                <h4>Upload PDF Documents</h4>
                <p>Drag & drop files here or click to browse</p>
                <input type="file" id="fileInput" multiple accept=".pdf" style="display: none;">
            </div>
            <div style="margin-top: 15px;">
                <button class="btn" onclick="analyzeDocuments()" id="analyzeBtn">🔍 Analyze Documents</button>
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
                <div class="metric-value" id="qualifiedWorkloads">3</div>
                <div class="metric-label">Qualified Workloads</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="creditEligible">$15,200</div>
                <div class="metric-label">Credit Eligible Spend</div>
            </div>
        </div>
        
        <!-- Spend vs Commitment Chart (Fixed) -->
        <div class="chart-container">
            <h3>📊 Spend vs Commitment Tracker</h3>
            <canvas id="spendChart" width="400" height="200"></canvas>
        </div>
        
        <!-- Workload Credit Qualification (Fixed Focus) -->
        <div class="credit-recommendations">
            <h3>🎯 Workload Credit Qualification Analysis</h3>
            <p>AI analysis of workloads qualifying for AWS credits:</p>
            <div id="creditRecommendations">Loading workload analysis...</div>
        </div>
        
        <!-- History Section (Restored) -->
        
        <!-- Attestation Calendar Section -->
        <div class="attestation-calendar" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3>📅 Attestation Calendar & Reminders</h3>
            <p>Create calendar events with attestation forms for credit submissions:</p>
            <div id="attestationEvents">
                <div class="calendar-event urgent" style="border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 5px 0; background: #f9f9f9; border-left: 4px solid #dc3545;">
                    <strong>🚨 EC2 RI Credit Submission Due</strong><br>
                    <small>Tomorrow, 2:00 PM - Submit Reserved Instance credits for Q4</small>
                </div>
                <div class="calendar-event" style="border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 5px 0; background: #f9f9f9;">
                    <strong>📊 Monthly Commitment Review</strong><br>
                    <small>Next Monday, 10:00 AM - Review progress toward annual commitment</small>
                </div>
                <div class="calendar-event" style="border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 5px 0; background: #f9f9f9;">
                    <strong>💰 Savings Plan Assessment</strong><br>
                    <small>Next Friday, 3:00 PM - Evaluate current Savings Plan utilization</small>
                </div>
            </div>
            <button class="btn" onclick="openAttestationModal()">📋 Select & Create Calendar Reminders</button>
        </div>
        <div class="history-section">
            <h3>📈 Decision History</h3>
            <div id="historyContent">
                <div style="text-align: center; padding: 20px; color: #666;">
                    <p>No decisions recorded yet. Accept or reject recommendations to build history.</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    
    <!-- Attestation Calendar Modal -->
    <div id="attestationModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5);">
        <div class="modal-content" style="background: white; margin: 5% auto; padding: 30px; border-radius: 12px; width: 90%; max-width: 700px; max-height: 80vh; overflow-y: auto;">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                <h3>📅 Create Attestation Calendar Events</h3>
                <span class="close" onclick="closeModal('attestationModal')" style="font-size: 28px; font-weight: bold; cursor: pointer; color: #aaa;">&times;</span>
            </div>
            <div style="margin-bottom: 20px;">
                <button class="btn" onclick="selectAllAttestations()">✅ Select All</button>
                <button class="btn" onclick="deselectAllAttestations()" style="background: #6c757d;">❌ Deselect All</button>
            </div>
            <div id="attestationEventList">
                <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" checked style="margin-right: 10px;">
                        <div>
                            <strong>EC2 Reserved Instance Credit Submission</strong><br>
                            <small>📅 Tomorrow 2:00 PM - 3:00 PM</small><br>
                            <small>📎 Includes: RI utilization report, credit calculation form</small>
                        </div>
                    </label>
                </div>
                <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" checked style="margin-right: 10px;">
                        <div>
                            <strong>Monthly Commitment Progress Review</strong><br>
                            <small>📅 Next Monday 10:00 AM - 11:00 AM</small><br>
                            <small>📎 Includes: Spend tracking report, commitment attestation form</small>
                        </div>
                    </label>
                </div>
                <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" style="margin-right: 10px;">
                        <div>
                            <strong>Savings Plan Utilization Assessment</strong><br>
                            <small>📅 Next Friday 3:00 PM - 4:00 PM</small><br>
                            <small>📎 Includes: SP usage analysis, optimization attestation</small>
                        </div>
                    </label>
                </div>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn" onclick="closeModal('attestationModal')" style="background: #6c757d;">Cancel</button>
                <button class="btn btn-accept" onclick="createSelectedAttestations()">📅 Create Calendar Events</button>
            </div>
        </div>
    </div>
    <div class="toast-container" id="toastContainer"></div>

    <script>
        // History tracking
        let decisionHistory = [];
        
        // Initialize data
        let spendData = {
            currentSpend: 272.80, // Available from AWS APIs
            annualCommitment: null, // Requires PDF analysis
            monthlyTarget: null, // Calculated from commitment
            qualifiedWorkloads: null, // Requires PDF analysis
            creditEligible: null // Requires PDF analysis
        };
        
        let pdfAnalyzed = false;
        
        // Toast Notification System
        // Update metrics display based on analysis state
        function updateMetricsDisplay() {
            if (!pdfAnalyzed) {
                document.getElementById('currentSpend').textContent = '$' + spendData.currentSpend.toFixed(2);
                document.getElementById('annualCommitment').textContent = 'Upload PDF';
                document.getElementById('progress').textContent = 'Upload PDF';
                document.getElementById('monthlyTarget').textContent = 'Upload PDF';
                document.getElementById('qualifiedWorkloads').textContent = 'Upload PDF';
                document.getElementById('creditEligible').textContent = 'Upload PDF';
            } else {
                document.getElementById('currentSpend').textContent = '$' + spendData.currentSpend.toFixed(2);
                document.getElementById('annualCommitment').textContent = '$' + spendData.annualCommitment.toLocaleString();
                document.getElementById('progress').textContent = ((spendData.currentSpend / spendData.annualCommitment) * 100).toFixed(2) + '%';
                document.getElementById('monthlyTarget').textContent = '$' + spendData.monthlyTarget.toLocaleString();
                document.getElementById('qualifiedWorkloads').textContent = spendData.qualifiedWorkloads;
                document.getElementById('creditEligible').textContent = '$' + spendData.creditEligible.toLocaleString();
                createSpendChart();
            }
        }
        
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
        
        // Analysis Function
        function analyzeDocuments() {
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.innerHTML = '🔄 Analyzing PDF for commitment data...';
            showToast('Extracting commitment information from PDF...', 'info');
            
            setTimeout(() => {
                // Simulate extracting commitment data from PDF
                spendData.annualCommitment = 50000;
                spendData.monthlyTarget = 4167;
                spendData.qualifiedWorkloads = 3;
                spendData.creditEligible = 15200;
                pdfAnalyzed = true;
                
                btn.disabled = false;
                btn.innerHTML = '🔍 Analyze Documents';
                showToast('PDF analysis completed! Commitment data extracted.', 'success');
                
                updateMetricsDisplay();
                loadWorkloadQualifications();
            }, 3000);
        }
        }
        
        // Load Workload Qualifications (Fixed Focus)
        function loadWorkloadQualifications() {
            document.getElementById('creditRecommendations').innerHTML = `
                <div class="credit-card qualified">
                    <div class="confidence-badge confidence-high">Qualified</div>
                    <div class="credit-header">
                        <h4>✅ Production EC2 Workload</h4>
                        <span class="credit-discount">Credit Eligible</span>
                    </div>
                    <p><strong>Workload:</strong> m5.large instances running 24/7 production services</p>
                    <p><strong>Usage Pattern:</strong> Consistent 95%+ utilization for 6+ months</p>
                    <p><strong>Credit Qualification:</strong> Fully qualifies for Reserved Instance credits</p>
                    <p><strong>Potential Credit Value:</strong> $8,500 annually</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('prod-ec2-001', 'Production EC2 Workload')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('prod-ec2-001', 'Production EC2 Workload')">❌ Reject</button>
                    </div>
                </div>
                
                <div class="credit-card partially_qualified">
                    <div class="confidence-badge confidence-medium">Partial</div>
                    <div class="credit-header">
                        <h4>⚠️ Development RDS Database</h4>
                        <span class="credit-discount">Partial Credit</span>
                    </div>
                    <p><strong>Workload:</strong> db.t3.medium development database</p>
                    <p><strong>Usage Pattern:</strong> 60% utilization during business hours</p>
                    <p><strong>Credit Qualification:</strong> Partially qualifies - consider Savings Plan</p>
                    <p><strong>Potential Credit Value:</strong> $2,800 annually</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('dev-rds-001', 'Development RDS Database')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('dev-rds-001', 'Development RDS Database')">❌ Reject</button>
                    </div>
                </div>
                
                <div class="credit-card not_qualified">
                    <div class="confidence-badge confidence-low">Not Qualified</div>
                    <div class="credit-header">
                        <h4>❌ Test Environment Compute</h4>
                        <span class="credit-discount">No Credit</span>
                    </div>
                    <p><strong>Workload:</strong> Spot instances for testing and development</p>
                    <p><strong>Usage Pattern:</strong> Intermittent usage, <30% monthly utilization</p>
                    <p><strong>Credit Qualification:</strong> Does not qualify for commitment credits</p>
                    <p><strong>Recommendation:</strong> Keep on On-Demand or Spot pricing</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-accept" onclick="acceptRecommendation('test-spot-001', 'Test Environment Compute')">✅ Accept</button>
                        <button class="btn btn-reject" onclick="rejectRecommendation('test-spot-001', 'Test Environment Compute')">❌ Reject</button>
                    </div>
                </div>
            `;
        }
        
        // Fixed Chart (Removed projected with credits line)
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
                        legend: { position: 'top' },
                        title: {
                            display: true,
                            text: 'Monthly Spend vs Annual Commitment Target'
                        }
                    }
                }
            });
        }
        
        // Fixed Recommendation Actions with History
        function acceptRecommendation(id, name) {
            showToast(`Workload "${name}" accepted for credit qualification!`, 'success');
            addToHistory(id, name, 'accepted');
            updateHistoryDisplay();
        }
        
        function rejectRecommendation(id, name) {
            showToast(`Workload "${name}" rejected. Feedback recorded for learning.`, 'info');
            addToHistory(id, name, 'rejected');
            updateHistoryDisplay();
        }
        
        // History Management
        function addToHistory(id, name, action) {
            decisionHistory.unshift({
                id: id,
                name: name,
                action: action,
                timestamp: new Date().toLocaleString()
            });
        }
        
        function updateHistoryDisplay() {
            const historyDiv = document.getElementById('historyContent');
            if (decisionHistory.length === 0) {
                historyDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;"><p>No decisions recorded yet.</p></div>';
                return;
            }
            
            historyDiv.innerHTML = decisionHistory.map(item => `
                <div class="history-item ${item.action}">
                    <div>
                        <strong>${item.name}</strong><br>
                        <small>${item.timestamp}</small>
                    </div>
                    <div>
                        <span style="color: ${item.action === 'accepted' ? '#28a745' : '#dc3545'}; font-weight: bold;">
                            ${item.action.toUpperCase()}
                        </span>
                    </div>
                </div>
            `).join('');
        }
        
        // Update Spend Metrics
        function updateSpendMetrics() {
            const progress = (spendData.currentSpend / spendData.annualCommitment * 100).toFixed(2);
            document.getElementById('progress').textContent = progress + '%';
            createSpendChart();
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            showToast('Welcome! Current AWS spend loaded. Upload PDF for commitment analysis.', 'info');
            updateMetricsDisplay();
        
        // Modal Management
        function openModal(modalId) { document.getElementById(modalId).style.display = 'block'; }
        function closeModal(modalId) { document.getElementById(modalId).style.display = 'none'; }
        function openAttestationModal() { openModal('attestationModal'); }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }
        
        // Attestation Event Selection
        function selectAllAttestations() {
            document.querySelectorAll('#attestationEventList input[type="checkbox"]').forEach(cb => cb.checked = true);
            showToast('All attestation events selected', 'info');
        }
        
        function deselectAllAttestations() {
            document.querySelectorAll('#attestationEventList input[type="checkbox"]').forEach(cb => cb.checked = false);
            showToast('All attestation events deselected', 'info');
        }
        
        function createSelectedAttestations() {
            const selected = document.querySelectorAll('#attestationEventList input[type="checkbox"]:checked').length;
            if (selected > 0) {
                showToast(`Creating ${selected} calendar event(s) with attestation forms...`, 'info');
                setTimeout(() => {
                    showToast(`${selected} calendar event(s) created successfully with attached attestation forms!`, 'success');
                    closeModal('attestationModal');
                }, 1500);
            } else {
                showToast('Please select at least one attestation event to create', 'warning');
            }
        }
            loadWorkloadQualifications();
            createSpendChart();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
