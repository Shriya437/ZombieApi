document.addEventListener('DOMContentLoaded', () => {

    const fileInput = document.getElementById('csvFile');
    const fileNameDisplay = document.getElementById('fileName');
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dashboardContent = document.getElementById('dashboardContent');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const systemStatus = document.getElementById('systemStatus');
    const viewResultsBtn = document.getElementById('viewResultsBtn');

    const metricTotalFlows = document.getElementById('metricTotalFlows');
    const metricAnomalies = document.getElementById('metricAnomalies');
    const metricHighRisk = document.getElementById('metricHighRisk');

    const API_BASE = 'http://localhost:8000';

    let selectedFile = null;

    // ---------------- FILE SELECT ----------------
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileNameDisplay.textContent = selectedFile.name;
            fileNameDisplay.style.color = 'var(--accent-primary)';
            runAnalysisBtn.disabled = false;
        } else {
            selectedFile = null;
            fileNameDisplay.textContent = 'No file selected';
        }
    });

    // ---------------- RUN ANALYSIS ----------------
    runAnalysisBtn.addEventListener('click', async () => {

        if (!selectedFile) {
            alert('Please select a CSV file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        systemStatus.textContent = 'Processing Data...';

        welcomeScreen.classList.add('hidden');
        dashboardContent.classList.remove('hidden');
        loadingOverlay.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/upload-data`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data || data.error) {
                console.error("Backend error:", data);
                alert(data?.error || "Server error");
                loadingOverlay.classList.add('hidden');
                return;
            }

            setTimeout(() => {
                console.log("RAW API RESPONSE:", data);
                renderDashboard(data);
                loadingOverlay.classList.add('hidden');
                systemStatus.textContent = 'Analysis Complete';
            }, 500);

        } catch (err) {
            console.error(err);
            alert("Request failed");
            loadingOverlay.classList.add('hidden');
        }
    });

    // ---------------- VIEW RESULTS ----------------
    viewResultsBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        systemStatus.textContent = 'Fetching Results...';

        welcomeScreen.classList.add('hidden');
        dashboardContent.classList.remove('hidden');
        loadingOverlay.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/results`);
            const data = await response.json();
            console.log("API RESPONSE:", data);
            setTimeout(() => {

                if (!data || !data.summary || data.summary.total_flows === 0) {
                    alert('No previous analysis found.');
                    dashboardContent.classList.add('hidden');
                    welcomeScreen.classList.remove('hidden');
                } else {
                    console.log("RAW API RESPONSE:", data);
                    renderDashboard(data);
                }

                loadingOverlay.classList.add('hidden');

            }, 500);

        } catch (err) {
            console.error(err);
            loadingOverlay.classList.add('hidden');
        }
    });

    // ---------------- DASHBOARD RENDER ----------------
    function renderDashboard(data) {
        console.log("INSIDE DASHBOARD:", data);

        // 🔥 SAFETY CHECK (MOST IMPORTANT)
        if (!data || !data.summary) {
            console.error("Invalid data:", data);
            alert("Invalid response from server");
            return;
        }

        const summary = data.summary || {};
        const features = data.feature_importance || [];
        const temporal = data.temporal_data || {};
        const table = data.table_data || [];

        animateValue(metricTotalFlows, 0, summary.total_flows || 0, 800);
        animateValue(metricAnomalies, 0, summary.total_anomalies || 0, 800);
        animateValue(metricHighRisk, 0, summary.high_risk || 0, 800);

        // ---------------- FEATURE IMPORTANCE ----------------
        const featureList = document.getElementById('featureImportanceList');
        featureList.innerHTML = '';

        features.forEach(item => {
            const pct = ((item?.importance || 0) * 100).toFixed(1);

            featureList.insertAdjacentHTML('beforeend', `
                <div class="feature-item">
                    <span class="feature-name">${formatLabel(item?.feature || "")}</span>
                    <div class="feature-bar-bg">
                        <div class="feature-bar-fill" style="width:${pct}%"></div>
                    </div>
                    <span class="feature-value">${pct}%</span>
                </div>
            `);
        });

        // ---------------- TEMPORAL DATA ----------------
        const timelineBars = document.getElementById('timelineBars');
        timelineBars.innerHTML = '';

        const times = temporal.time_bucket || [];
        const counts = temporal.anomaly_count || [];
        const max = Math.max(...counts, 0);

        times.forEach((t, i) => {
            const count = counts[i] || 0;
            const h = max ? (count / max) * 100 : 0;

            timelineBars.insertAdjacentHTML('beforeend', `
                <div class="timeline-bar-container">
                    <div class="t-bar" style="height:${h}%"></div>
                    <span class="t-label">${t}</span>
                </div>
            `);
        });

        // ---------------- TABLE ----------------
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';

        table.forEach(row => {
            tbody.insertAdjacentHTML('beforeend', `
                <tr>
                    <td>#${row.flow_id || 0}</td>
                    <td>${row.attack_type || ""}</td>
                    <td><span class="badge">${row.risk_level || "Low"}</span></td>
                    <td>${row.risk_score || 0}</td>
                    <td>${row.anomaly_score || 0}</td>
                    <td>${((row.confidence || 0) * 100).toFixed(1)}%</td>
                    <td>${row.behavior_tag || ""}</td>
                    <td title="${row.explanation || ""}">
                        ${row.explanation || ""}
                    </td>
                </tr>
            `);
        });
    }

    // ---------------- UTIL ----------------
    function animateValue(obj, start, end, duration) {
        let startTime = null;

        function step(t) {
            if (!startTime) startTime = t;
            const progress = Math.min((t - startTime) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    function formatLabel(str) {
        return (str || "")
            .split('_')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');
    }

});