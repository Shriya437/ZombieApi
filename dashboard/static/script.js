document.addEventListener('DOMContentLoaded', () => {

    const fileInput = document.getElementById('csvFile');
    const fileNameDisplay = document.getElementById('fileName');
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dashboardContent = document.getElementById('dashboardContent');
    const visualsContent = document.getElementById('visualsContent');
    const statsContent = document.getElementById('statsContent');
    const insightsContent = document.getElementById('insightsContent');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const systemStatus = document.getElementById('systemStatus');
    const viewResultsBtn = document.getElementById('viewResultsBtn');
    const navDashboard = document.getElementById('navDashboard');
    const navVisuals = document.getElementById('navVisuals');
    const navStats = document.getElementById('navStats');
    const navInsights = document.getElementById('navInsights');

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

        setActiveNav('navDashboard');
        welcomeScreen.classList.add('hidden');
        visualsContent.classList.add('hidden');
        statsContent.classList.add('hidden');
        insightsContent.classList.add('hidden');
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

        setActiveNav('viewResultsBtn');
        welcomeScreen.classList.add('hidden');
        visualsContent.classList.add('hidden');
        statsContent.classList.add('hidden');
        insightsContent.classList.add('hidden');
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

    // ---------------- NAVIGATION TABS ----------------
    function setActiveNav(activeId) {
        document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
        if (activeId) {
            const el = document.getElementById(activeId);
            if (el && el.parentElement) el.parentElement.classList.add('active');
        }
    }

    navDashboard.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveNav('navDashboard');
        welcomeScreen.classList.add('hidden');
        visualsContent.classList.add('hidden');
        statsContent.classList.add('hidden');
        insightsContent.classList.add('hidden');
        dashboardContent.classList.remove('hidden');
    });

    navVisuals.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveNav('navVisuals');
        welcomeScreen.classList.add('hidden');
        dashboardContent.classList.add('hidden');
        statsContent.classList.add('hidden');
        insightsContent.classList.add('hidden');
        visualsContent.classList.remove('hidden');
    });

    navStats.addEventListener('click', async (e) => {
        e.preventDefault();
        setActiveNav('navStats');
        welcomeScreen.classList.add('hidden');
        dashboardContent.classList.add('hidden');
        visualsContent.classList.add('hidden');
        insightsContent.classList.add('hidden');
        statsContent.classList.remove('hidden');

        await fetchStatsIfNeeded();
    });

    navInsights.addEventListener('click', async (e) => {
        e.preventDefault();
        setActiveNav('navInsights');
        welcomeScreen.classList.add('hidden');
        dashboardContent.classList.add('hidden');
        visualsContent.classList.add('hidden');
        statsContent.classList.add('hidden');
        insightsContent.classList.remove('hidden');

        await fetchStatsIfNeeded();
    });

    async function fetchStatsIfNeeded() {
        const statsGrid = document.getElementById('statsGrid');
        if (statsGrid && statsGrid.children.length === 0) {
            try {
                systemStatus.textContent = 'Fetching Stats...';
                loadingOverlay.classList.remove('hidden');
                
                const res = await fetch('data/eda_stats.json');
                const statsData = await res.json();
                renderStats(statsData);
                
                loadingOverlay.classList.add('hidden');
                systemStatus.textContent = 'System Ready';
            } catch (err) {
                console.error(err);
                loadingOverlay.classList.add('hidden');
                systemStatus.textContent = 'Failed to Load Stats';
            }
        }
    }

    // ---------------- STATS RENDER ----------------
    function renderStats(data) {
        const grid = document.getElementById('statsGrid');
        grid.innerHTML = '';
        
        function createStatCard(title, content) {
            return `
                <div class="stat-card glass-panel">
                    <h4>${title}</h4>
                    <div class="stat-content">${content}</div>
                </div>
            `;
        }
        
        // Data Overview
        grid.insertAdjacentHTML('beforeend', createStatCard("Data Overview", `<p><b>Shape:</b> ${data.data_overview.shape.join(" rows x ")} columns</p>`));
        
        // Class Distribution
        let classHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.class_distribution)) {
            classHtml += `<li><b>${k}:</b> ${v.toLocaleString()} (${(data.class_percentage[k] || 0).toFixed(2)}%)</li>`;
        }
        classHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Class Distribution", classHtml));
        
        // Top Suspicious Ports
        let suspiciousPortsHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.top_suspicious_ports || {})) {
            suspiciousPortsHtml += `<li><b>Port ${k}:</b> ${(v * 100).toFixed(2)}% Attack Ratio</li>`;
        }
        suspiciousPortsHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Top Suspicious Ports", suspiciousPortsHtml));

        // Top Ports
        let topPortsHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.top_ports || {})) {
            topPortsHtml += `<li><b>Port ${k}:</b> ${v.toLocaleString()} flows</li>`;
        }
        topPortsHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Most Used Ports", topPortsHtml));

        // Attack Types
        let attackHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.attack_type || {})) {
            attackHtml += `<li><b>${k}:</b> ${v.toLocaleString()} flows</li>`;
        }
        attackHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Attack Types Breakdown", attackHtml));

        // Traffic Intensity
        let trafficHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.traffic_intensity || {})) {
            trafficHtml += `<li><b>${k}:</b> ${(v["Flow Bytes/s"] || 0).toLocaleString(undefined, {maximumFractionDigits:0})} B/s | ${(v["Flow Packets/s"] || 0).toLocaleString(undefined, {maximumFractionDigits:0})} Pkts/s</li>`;
        }
        trafficHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Traffic Intensity", trafficHtml));

        // Packet Imbalance
        let pktHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.packet_imbalance || {})) {
            pktHtml += `<li><b>${k}:</b> ${(v * 100).toFixed(2)}%</li>`;
        }
        pktHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Packet Imbalance (Fwd/Bwd)", pktHtml));

        // Timing Behavior (IAT Mean & Variability)
        let timingHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.timing_behavior || {})) {
            timingHtml += `<li style="display:block;margin-bottom:8px;"><b>${k}:</b><br>IAT Mean: ${(v["Flow IAT Mean"] || 0).toLocaleString(undefined, {maximumFractionDigits:0})} &micro;s<br>Variability: ${(v["iat_variability"] || 0).toFixed(2)}</li>`;
        }
        timingHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Timing Behavior", timingHtml));

        // Burstiness
        let burstHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.burstiness || {})) {
            burstHtml += `<li><b>${k}:</b> ${v.toLocaleString(undefined, {maximumFractionDigits:0})}</li>`;
        }
        burstHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Burstiness", burstHtml));

        // Flag Analysis
        let flagHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.flag_analysis || {})) {
            flagHtml += `<li><b>${k} (SYN/ACK ratio):</b> ${(v.flag_ratio || 0).toFixed(4)}</li>`;
        }
        flagHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("TCP Flag Analysis", flagHtml));

        // Repeat Call Behavior
        let repeatHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.repeat_call_behavior || {})) {
            repeatHtml += `<li><b>${k}:</b> ${(v * 100).toFixed(2)}%</li>`;
        }
        repeatHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Repeat Call Ratio", repeatHtml));

        // Endpoint Diversity
        let diversityHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.endpoint_diversity || {})) {
            diversityHtml += `<li><b>${k}:</b> ${v.toLocaleString(undefined, {maximumFractionDigits:0})} endpoints</li>`;
        }
        diversityHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Endpoint Diversity", diversityHtml));

        // Day-Wise Analysis
        let dayHtml = "<ul class='stat-list'>";
        for (const [k, v] of Object.entries(data.day_wise_analysis || {})) {
            let dayTotal = Object.values(v).reduce((a, b) => a + b, 0);
            dayHtml += `<li><b>${k}:</b> ${dayTotal.toLocaleString()} flows</li>`;
        }
        dayHtml += "</ul>";
        grid.insertAdjacentHTML('beforeend', createStatCard("Day-Wise Traffic", dayHtml));

        // Key Insights

        const insightsList = document.getElementById('insightsList');
        let insightsHtml = '';
        data.insights.forEach(insight => {
            insightsHtml += `<li style="margin-bottom: 0.5rem;">${insight}</li>`;
        });
        insightsList.innerHTML = insightsHtml;
    }

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