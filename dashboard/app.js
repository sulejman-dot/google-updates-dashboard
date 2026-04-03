document.addEventListener("DOMContentLoaded", () => {
    const alertsGrid = document.getElementById("alertsGrid");
    const filterBtns = document.querySelectorAll(".filter-btn");
    let allData = [];

    // Format Date Helper
    const formatDate = (dateString) => {
        const d = new Date(dateString);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    // Determine Badge Visuals
    const getBadgeClass = (status, severity) => {
        if (status === "Brand Mention") {
            if (severity.includes("Positive")) return "badge positive";
            if (severity.includes("Negative")) return "badge negative";
            return "badge neutral";
        }
        if (status === "Competitor Update") {
            if (severity.includes("AI") || severity.includes("🤖")) return "badge ai-llm";
            return "badge competitor";
        }
        if (status === "SERP Feature Change") return "badge feature";
        if (status === "UGC Discussion") return "badge neutral";
        return "badge default"; // Official/Other
    };

    // Render Cards
    const renderCards = (data) => {
        alertsGrid.innerHTML = "";
        
        if (data.length === 0) {
            alertsGrid.innerHTML = `<div class="loading">No alerts found for this category.</div>`;
            return;
        }

        data.forEach((alert, index) => {
            const card = document.createElement("article");
            card.className = "alert-card";
            card.style.animationDelay = `${index * 0.05}s`;

            const badgeClass = getBadgeClass(alert.status, alert.severity);
            const badgeText = alert.status === "Brand Mention" ? alert.severity : 
                              alert.status === "Competitor Update" ? alert.severity : alert.status;

            // Source icon
            let sourceIcon = "🌐";
            if (alert.status === "Competitor Update") {
                if (alert.severity.includes("AI") || alert.severity.includes("🤖")) sourceIcon = "🤖";
                else sourceIcon = "🏢";
            } else if (alert.source.includes("Reddit")) sourceIcon = "🗣️";
            else if (alert.source.includes("Hacker News")) sourceIcon = "💻";
            else if (alert.source.includes("Roundtable") || alert.source.includes("Journal") || alert.source.includes("Land")) sourceIcon = "📰";
            else if (alert.source.includes("Google Search Blog")) sourceIcon = "📢";
            else if (alert.source.includes("Google")) sourceIcon = "📣";

            card.innerHTML = `
                <div class="card-header">
                    <span class="${badgeClass}">${badgeText}</span>
                    <span class="card-date">${formatDate(alert.date)}</span>
                </div>
                <h2 class="card-title">${alert.title}</h2>
                <p class="card-text">${alert.text.replace(/\n🔗.*/g, '').trim()}</p>
                <div class="card-footer">
                    <span class="source-tag"><span class="source-icon">${sourceIcon}</span> ${alert.source}</span>
                    <a href="${alert.url}" target="_blank" rel="noopener noreferrer" class="read-more">View Source <span>&rarr;</span></a>
                </div>
            `;
            alertsGrid.appendChild(card);
        });
    };

    // Update Overview Stats
    const updateStats = (data) => {
        document.getElementById("stat-total").innerText = data.length;
        document.getElementById("stat-mentions").innerText = data.filter(d => d.status === "Brand Mention").length;
        document.getElementById("stat-competitors").innerText = data.filter(d => d.status === "Competitor Update").length;
    };

    // Filter Logic
    const applyFilter = (filterParam) => {
        let filteredData = allData;
        if (filterParam !== "all") {
            if (filterParam === "official") {
                // Only real Google Status Dashboard entries
                filteredData = allData.filter(d => d.source === "Google Status Dashboard");
            } else if (filterParam === "algo_chatter") {
                // Community news, UGC discussions, SERP feature changes, official blog posts
                filteredData = allData.filter(d => 
                    ["UGC Discussion", "Community Report", "SERP Feature Change", "Official Announcement"].includes(d.status)
                );
            } else if (filterParam === "competitor") {
                filteredData = allData.filter(d => d.status === "Competitor Update");
            } else {
                filteredData = allData.filter(d => d.status === filterParam);
            }
        }
        renderCards(filteredData);
    };

    filterBtns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            filterBtns.forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            applyFilter(e.target.dataset.filter);
        });
    });

    // --- Monthly Summary ---
    const buildMonthlySummary = (data) => {
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        
        // Filter to current month
        const monthData = data.filter(d => {
            const dd = new Date(d.date);
            return dd.getMonth() === currentMonth && dd.getFullYear() === currentYear;
        });
        
        // Month label
        document.getElementById('summaryMonthLabel').textContent = monthNames[currentMonth];
        
        // Category counts
        const categories = {
            'Competitor Intel': { count: 0, color: '#E67E22', items: [] },
            'Community & Algo': { count: 0, color: '#1E90FF', items: [] },
            'Brand Mentions': { count: 0, color: '#36a64f', items: [] },
            'Official Updates': { count: 0, color: '#FF4500', items: [] },
            'SERP Features': { count: 0, color: '#8A2BE2', items: [] }
        };
        
        monthData.forEach(d => {
            if (d.status === 'Competitor Update') { categories['Competitor Intel'].count++; categories['Competitor Intel'].items.push(d); }
            else if (d.status === 'Brand Mention') { categories['Brand Mentions'].count++; categories['Brand Mentions'].items.push(d); }
            else if (d.status === 'SERP Feature Change') { categories['SERP Features'].count++; categories['SERP Features'].items.push(d); }
            else if (['SERVICE_INFORMATION','AVAILABLE','RESOLVED'].some(s => (d.status || '').includes(s))) { categories['Official Updates'].count++; categories['Official Updates'].items.push(d); }
            else { categories['Community & Algo'].count++; categories['Community & Algo'].items.push(d); }
        });
        
        const maxCount = Math.max(...Object.values(categories).map(c => c.count), 1);
        
        // Render breakdown bars
        const breakdownEl = document.getElementById('categoryBreakdown');
        breakdownEl.innerHTML = Object.entries(categories)
            .sort((a, b) => b[1].count - a[1].count)
            .map(([name, {count, color}]) => `
                <div class="breakdown-item">
                    <span class="breakdown-label">${name}</span>
                    <div class="breakdown-bar-track">
                        <div class="breakdown-bar-fill" style="width: ${(count/maxCount)*100}%; background: ${color};"></div>
                    </div>
                    <span class="breakdown-count" style="color: ${color};">${count}</span>
                </div>
            `).join('');
        
        // AI/LLM tracker
        const aiCount = monthData.filter(d => {
            const sev = (d.severity || '').toLowerCase();
            return sev.includes('ai') || sev.includes('🤖') || sev.includes('llm');
        }).length;
        const aiPct = monthData.length > 0 ? Math.round((aiCount / monthData.length) * 100) : 0;
        
        document.getElementById('aiCount').textContent = aiCount;
        document.getElementById('aiPctText').textContent = `${aiPct}% of all signals this month`;
        setTimeout(() => {
            document.getElementById('aiPctFill').style.width = `${aiPct}%`;
        }, 300);
        
        // Top sources
        const sourceCounts = {};
        monthData.forEach(d => {
            const src = d.source || 'Unknown';
            sourceCounts[src] = (sourceCounts[src] || 0) + 1;
        });
        const sortedSources = Object.entries(sourceCounts).sort((a,b) => b[1] - a[1]).slice(0, 6);
        const sourceColors = ['#BB86FC', '#64B5F6', '#4DB6AC', '#FFB74D', '#F06292', '#AED581'];
        
        document.getElementById('topSources').innerHTML = sortedSources
            .map(([name, count], i) => `
                <div class="source-row">
                    <span class="source-name">
                        <span class="source-dot" style="background: ${sourceColors[i % sourceColors.length]};"></span>
                        ${name}
                    </span>
                    <span class="source-count">${count}</span>
                </div>
            `).join('');
        
        // Key highlights - pick best from each category
        const highlights = [];
        
        // Latest AI/LLM competitor update
        const latestAI = monthData.find(d => d.status === 'Competitor Update' && ((d.severity||'').includes('AI') || (d.severity||'').includes('🤖')));
        if (latestAI) highlights.push({ emoji: '🤖', text: latestAI.title, type: 'AI/LLM' });
        
        // Latest brand mention
        const latestBrand = monthData.find(d => d.status === 'Brand Mention');
        if (latestBrand) highlights.push({ emoji: '🎯', text: latestBrand.title, type: 'Brand' });
        
        // Latest official update
        const latestOfficial = monthData.find(d => ['SERVICE_INFORMATION','AVAILABLE','RESOLVED'].some(s => (d.status||'').includes(s)));
        if (latestOfficial) highlights.push({ emoji: '📢', text: latestOfficial.title, type: 'Official' });
        
        // Latest community report
        const latestCommunity = monthData.find(d => ['Community Report','UGC Discussion','Official Announcement'].includes(d.status));
        if (latestCommunity) highlights.push({ emoji: '📰', text: latestCommunity.title, type: 'Community' });
        
        // Latest competitor (non-AI)
        const latestComp = monthData.find(d => d.status === 'Competitor Update' && !((d.severity||'').includes('AI') || (d.severity||'').includes('🤖')));
        if (latestComp) highlights.push({ emoji: '🏢', text: latestComp.title, type: 'Competitor' });
        
        document.getElementById('keyHighlights').innerHTML = highlights.length > 0 
            ? highlights.map(h => `
                <div class="highlight-item">
                    ${h.emoji} <strong>${h.text}</strong>
                </div>
            `).join('')
            : '<div class="highlight-item">No highlights yet this month.</div>';
        
        // Subtitle
        document.getElementById('summarySubtitle').textContent = 
            `${monthData.length} signals tracked • ${aiCount} AI/LLM flagged • ${categories['Competitor Intel'].count} competitor updates`;
    };
    
    // Toggle summary collapse
    document.getElementById('summaryToggle').addEventListener('click', () => {
        const body = document.getElementById('summaryBody');
        const icon = document.getElementById('toggleIcon');
        body.classList.toggle('collapsed');
        icon.classList.toggle('collapsed');
    });

    // Fetch Data
    fetch('dashboard_data.json')
        .then(response => {
            if (!response.ok) throw new Error("Could not load data");
            return response.json();
        })
        .then(data => {
            allData = data;
            updateStats(data);
            buildMonthlySummary(data);
            renderCards(data);
        })
        .catch(error => {
            alertsGrid.innerHTML = `
                <div class="loading" style="color: var(--accent-red);">
                    Error loading dashboard_data.json.<br>
                    Make sure the Python script has run at least once to generate data.
                </div>
            `;
            console.error(error);
        });
});
