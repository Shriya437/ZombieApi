document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fileInput = document.getElementById('csvFile');
    const fileNameDisplay = document.getElementById('fileName');
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dashboardContent = document.getElementById('dashboardContent');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const systemStatus = document.getElementById('systemStatus');
    const viewResultsBtn = document.getElementById('viewResultsBtn');

    // Metrics
    const metricTotalFlows = document.getElementById('metricTotalFlows');
    const metricAnomalies = document.getElementById('metricAnomalies');
    const metricHighRisk = document.getElementById('metricHighRisk');

    // API URL
    const API_BASE = 'http://localhost:8000';

    let selectedFile = null;

    // Handle File Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileNameDisplay.textContent = selectedFile.name;
            fileNameDisplay.style.color = 'var(--accent-primary)';
            runAnalysisBtn.disabled = false;
        } else {
            selectedFile = null;
            fileNameDisplay.textContent = 'No file selected';
            fileNameDisplay.style.color = 'var(--text-secondary)';
        }
    });

    // Handle Run Analysis
    runAnalysisBtn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select a CSV file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        // UI State: Loading
        systemStatus.textContent = 'Processing Data...';
        systemStatus.parentElement.style.color = 'var(--warning)';
        
        if (!welcomeScreen.classList.contains('hidden')) {
            welcomeScreen.classList.add('hidden');
        }
        dashboardContent.classList.remove('hidden');
        loadingOverlay.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/upload-data`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Server error');
            }

            const data = await response.json();
            
            // Simulate extra processing time for effect
            setTimeout(() => {
                renderDashboard(data);
                loadingOverlay.classList.add('hidden');
                systemStatus.textContent = 'Analysis Complete';
                systemStatus.parentElement.style.color = 'var(--success)';
            }, 800);

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during analysis.');
            loadingOverlay.classList.add('hidden');
            systemStatus.textContent = 'Error';
            systemStatus.parentElement.style.color = 'var(--danger)';
        }
    });

    // View Results directly (GET)
    viewResultsBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        
        systemStatus.textContent = 'Fetching Results...';
        
        if (!welcomeScreen.classList.contains('hidden')) {
            welcomeScreen.classList.add('hidden');
        }
        dashboardContent.classList.remove('hidden');
        loadingOverlay.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/results`);
            const data = await response.json();
            
            setTimeout(() => {
                if (data.summary.total_flows === 0) {
                    // Empty state
                    alert('No previous analysis found.');
                    dashboardContent.classList.add('hidden');
                    welcomeScreen.classList.remove('hidden');
                } else {
                    renderDashboard(data);
                }
                loadingOverlay.classList.add('hidden');
                systemStatus.textContent = 'System Ready';
            }, 500);

        } catch (error) {
            console.error('Error:', error);
            loadingOverlay.classList.add('hidden');
            systemStatus.textContent = 'System Ready';
        }
    });

    // Render logic
    function renderDashboard(data) {
        // 1. Update Metrics
        animateValue(metricTotalFlows, 0, data.summary.total_flows, 1000);
        animateValue(metricAnomalies, 0, data.summary.total_anomalies, 1000);
        animateValue(metricHighRisk, 0, data.summary.high_risk, 1000);

        // 2. Render Feature Importance
        const featureList = document.getElementById('featureImportanceList');
        featureList.innerHTML = '';
        data.feature_importance.forEach(item => {
            const pct = (item.importance * 100).toFixed(1);
            const html = `
                <div class="feature-item">
                    <span class="feature-name">${formatLabel(item.feature)}</span>
                    <div class="feature-bar-bg">
                        <div class="feature-bar-fill" style="width: ${pct}%"></div>
                    </div>
                    <span class="feature-value">${pct}%</span>
                </div>
            `;
            featureList.insertAdjacentHTML('beforeend', html);
        });

        // 3. Render Temporal Data (Simple Bars)
        const timelineBars = document.getElementById('timelineBars');
        timelineBars.innerHTML = '';
        const maxAnomalies = Math.max(...data.temporal_data.anomaly_count);
        
        data.temporal_data.time_bucket.forEach((time, index) => {
            const count = data.temporal_data.anomaly_count[index];
            const heightPct = maxAnomalies > 0 ? (count / maxAnomalies) * 100 : 0;
            
            const html = `
                <div class="timeline-bar-container">
                    <div class="t-bar" style="height: ${heightPct}%" title="${count} anomalies"></div>
                    <span class="t-label">${time}</span>
                </div>
            `;
            timelineBars.insertAdjacentHTML('beforeend', html);
        });

        // 4. Render Table Data
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        
        data.table_data.forEach(row => {
            const riskBadgeClass = row.risk_level.toLowerCase();
            const html = `
                <tr>
                    <td style="font-family: monospace; color: var(--accent-primary)">#${row.flow_id}</td>
                    <td>${row.attack_type}</td>
                    <td><span class="badge ${riskBadgeClass}">${row.risk_level}</span></td>
                    <td>${row.risk_score}</td>
                    <td>${row.anomaly_score}</td>
                    <td>${(row.confidence * 100).toFixed(1)}%</td>
                    <td>${row.behavior_tag}</td>
                    <td style="color: var(--text-secondary); max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${row.explanation}">
                        ${row.explanation}
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', html);
        });
    }

    // Helper: Number counter animation
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Helper: Format feature names (e.g., packet_length -> Packet Length)
    function formatLabel(str) {
        return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
});
