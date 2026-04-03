document.addEventListener("DOMContentLoaded", () => {
    const alertsGrid = document.getElementById("alertsGrid");
    const filterBtns = document.querySelectorAll(".filter-btn");
    const searchInput = document.getElementById("searchInput");
    const searchClear = document.getElementById("searchClear");
    const sortBtns = document.querySelectorAll(".sort-btn");
    
    let allData = [];
    let currentFilter = "all";
    let currentSort = "newest";
    let searchQuery = "";

    // ─── Relative Time ─────────────────────────────────────
    const relativeTime = (dateString) => {
        const now = new Date();
        const d = new Date(dateString);
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        const diffHr = Math.floor(diffMs / 3600000);
        const diffDay = Math.floor(diffMs / 86400000);
        
        if (diffMin < 1) return "Just now";
        if (diffMin < 60) return `${diffMin}m ago`;
        if (diffHr < 24) return `${diffHr}h ago`;
        if (diffDay < 7) return `${diffDay}d ago`;
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const formatDate = (dateString) => {
        const d = new Date(dateString);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    // ─── Animated Counter ───────────────────────────────────
    const animateCounter = (el, target) => {
        const start = parseInt(el.textContent) || 0;
        if (start === target) return;
        const duration = 600;
        const startTime = performance.now();
        
        const tick = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(start + (target - start) * eased);
            if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    };

    // ─── Badge Logic ────────────────────────────────────────
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
        return "badge default";
    };

    // ─── Source Icon ────────────────────────────────────────
    const getSourceIcon = (alert) => {
        if (alert.status === "Competitor Update") {
            return (alert.severity.includes("AI") || alert.severity.includes("🤖")) ? "🤖" : "🏢";
        }
        if (alert.source.includes("Reddit")) return "🗣️";
        if (alert.source.includes("Hacker News")) return "💻";
        if (alert.source.includes("Roundtable") || alert.source.includes("Journal") || alert.source.includes("Land")) return "📰";
        if (alert.source.includes("Google Search Blog")) return "📢";
        if (alert.source.includes("Google")) return "📣";
        return "🌐";
    };

    // ─── Search Highlight ───────────────────────────────────
    const highlightText = (text, query) => {
        if (!query || query.length < 2) return text;
        const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escaped})`, 'gi');
        return text.replace(regex, '<mark class="search-hl">$1</mark>');
    };

    // ─── Render Cards ───────────────────────────────────────
    const renderCards = (data) => {
        alertsGrid.innerHTML = "";
        
        // Update results count
        const resultsBar = document.getElementById("resultsCount");
        if (searchQuery) {
            resultsBar.innerHTML = `Showing <span class="search-match">${data.length}</span> result${data.length !== 1 ? 's' : ''} for "<span class="search-match">${searchQuery}</span>"`;
        } else {
            resultsBar.textContent = `${data.length} signal${data.length !== 1 ? 's' : ''} found`;
        }

        if (data.length === 0) {
            alertsGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">${searchQuery ? '🔍' : '📭'}</div>
                    <h3>${searchQuery ? 'No matching alerts' : 'No alerts in this category'}</h3>
                    <p>${searchQuery ? `Try different keywords or clear the search` : 'Check back later for new intelligence signals'}</p>
                </div>
            `;
            return;
        }

        data.forEach((alert, index) => {
            const card = document.createElement("article");
            card.className = "alert-card card-reveal";
            card.style.animationDelay = `${index * 0.04}s`;

            const badgeClass = getBadgeClass(alert.status, alert.severity);
            const badgeText = alert.status === "Brand Mention" ? alert.severity : 
                              alert.status === "Competitor Update" ? alert.severity : alert.status;

            const sourceIcon = getSourceIcon(alert);
            const cleanText = alert.text.replace(/\n🔗.*/g, '').trim();
            const needsExpand = cleanText.length > 200;

            const displayTitle = highlightText(alert.title, searchQuery);
            const displayText = highlightText(cleanText, searchQuery);
            const displaySource = highlightText(alert.source, searchQuery);

            card.innerHTML = `
                <div class="card-header">
                    <span class="${badgeClass}">${badgeText}</span>
                    <span class="card-date" title="${formatDate(alert.date)}">${relativeTime(alert.date)}</span>
                </div>
                <h2 class="card-title">${displayTitle}</h2>
                <p class="card-text" id="text-${index}">${displayText}</p>
                ${needsExpand ? `<button class="card-expand-btn" data-index="${index}" data-expanded="false">Show more ▾</button>` : ''}
                <div class="card-footer">
                    <span class="source-tag"><span class="source-icon">${sourceIcon}</span> ${displaySource}</span>
                    <a href="${alert.url}" target="_blank" rel="noopener noreferrer" class="read-more">View Source <span>&rarr;</span></a>
                </div>
            `;
            alertsGrid.appendChild(card);
        });

        // Scroll-reveal with IntersectionObserver
        const cards = document.querySelectorAll('.card-reveal');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.05, rootMargin: '50px 0px 50px 0px' });

        cards.forEach(card => observer.observe(card));

        // Force-reveal cards already in viewport (fixes filter → invisible cards bug)
        requestAnimationFrame(() => {
            setTimeout(() => {
                cards.forEach(card => {
                    if (!card.classList.contains('revealed')) {
                        const rect = card.getBoundingClientRect();
                        if (rect.top < window.innerHeight + 100) {
                            card.classList.add('revealed');
                            observer.unobserve(card);
                        }
                    }
                });
            }, 100);
        });

        // Expand/collapse handlers
        document.querySelectorAll('.card-expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = e.target.dataset.index;
                const textEl = document.getElementById(`text-${idx}`);
                const isExpanded = e.target.dataset.expanded === 'true';
                textEl.classList.toggle('expanded');
                e.target.dataset.expanded = !isExpanded;
                e.target.textContent = isExpanded ? 'Show more ▾' : 'Show less ▴';
            });
        });
    };

    // ─── Stats ──────────────────────────────────────────────
    const updateStats = (data) => {
        animateCounter(document.getElementById("stat-total"), data.length);
        animateCounter(document.getElementById("stat-mentions"), data.filter(d => d.status === "Brand Mention").length);
        animateCounter(document.getElementById("stat-competitors"), data.filter(d => d.status === "Competitor Update").length);
    };

    // ─── Filter Counts ──────────────────────────────────────
    const ALGO_STATUSES = ["UGC Discussion", "Community Report", "SERP Feature Change", "Official Announcement", "SERVICE_INFORMATION", "AVAILABLE", "RESOLVED"];

    const updateFilterCounts = (data) => {
        document.getElementById("count-all").textContent = data.length;
        document.getElementById("count-brand").textContent = data.filter(d => d.status === "Brand Mention").length;
        document.getElementById("count-algo").textContent = data.filter(d => ALGO_STATUSES.includes(d.status)).length;
        document.getElementById("count-comp").textContent = data.filter(d => d.status === "Competitor Update").length;
        document.getElementById("count-serp").textContent = data.filter(d => d.status === "SERP Feature Change").length;
        document.getElementById("count-official").textContent = data.filter(d => d.source === "Google Status Dashboard").length;
    };

    // ─── Core Filter + Search + Sort Pipeline ───────────────
    const applyAll = () => {
        let data = [...allData];

        // 1. Category filter
        if (currentFilter !== "all") {
            if (currentFilter === "official") {
                data = data.filter(d => d.source === "Google Status Dashboard");
            } else if (currentFilter === "algo_chatter") {
                data = data.filter(d => ALGO_STATUSES.includes(d.status));
            } else if (currentFilter === "competitor") {
                data = data.filter(d => d.status === "Competitor Update");
            } else {
                data = data.filter(d => d.status === currentFilter);
            }
        }

        // 2. Search
        if (searchQuery && searchQuery.length >= 2) {
            const q = searchQuery.toLowerCase();
            data = data.filter(d => 
                d.title.toLowerCase().includes(q) ||
                d.text.toLowerCase().includes(q) ||
                d.source.toLowerCase().includes(q) ||
                (d.severity || '').toLowerCase().includes(q)
            );
        }

        // 3. Sort
        data.sort((a, b) => {
            const da = new Date(a.date), db = new Date(b.date);
            return currentSort === "newest" ? db - da : da - db;
        });

        renderCards(data);
    };

    // ─── Filter Buttons ─────────────────────────────────────
    filterBtns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            const clicked = e.currentTarget;
            filterBtns.forEach(b => b.classList.remove("active"));
            clicked.classList.add("active");
            currentFilter = clicked.dataset.filter;
            applyAll();
        });
    });

    // ─── Stat Card Click → Filter ───────────────────────────
    document.querySelectorAll('.stat-card[data-filter]').forEach(card => {
        card.addEventListener('click', () => {
            const f = card.dataset.filter;
            filterBtns.forEach(b => b.classList.remove("active"));
            const matchBtn = document.querySelector(`.filter-btn[data-filter="${f}"]`);
            if (matchBtn) matchBtn.classList.add("active");
            currentFilter = f;
            applyAll();
        });
    });

    // ─── Search ─────────────────────────────────────────────
    let searchTimeout;
    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = searchInput.value.trim();
            searchClear.classList.toggle("hidden", !searchQuery);
            applyAll();
        }, 200);
    });

    searchClear.addEventListener("click", () => {
        searchInput.value = "";
        searchQuery = "";
        searchClear.classList.add("hidden");
        applyAll();
        searchInput.focus();
    });

    // ESC clears search
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && searchQuery) {
            searchInput.value = "";
            searchQuery = "";
            searchClear.classList.add("hidden");
            applyAll();
        }
        // Ctrl/Cmd + K focuses search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
    });

    // ─── Sort ───────────────────────────────────────────────
    sortBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            sortBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentSort = btn.dataset.sort;
            applyAll();
        });
    });

    // ─── Monthly Summary ────────────────────────────────────
    const buildMonthlySummary = (data) => {
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        
        const monthData = data.filter(d => {
            const dd = new Date(d.date);
            return dd.getMonth() === currentMonth && dd.getFullYear() === currentYear;
        });
        
        document.getElementById('summaryMonthLabel').textContent = monthNames[currentMonth];
        
        // Category mapping with filter targets
        const categories = {
            'Competitor Intel': { count: 0, color: '#E67E22', filter: 'competitor', items: [] },
            'Community & Algo': { count: 0, color: '#1E90FF', filter: 'algo_chatter', items: [] },
            'Brand Mentions': { count: 0, color: '#36a64f', filter: 'Brand Mention', items: [] },
            'Official Updates': { count: 0, color: '#FF4500', filter: 'official', items: [] },
            'SERP Features': { count: 0, color: '#8A2BE2', filter: 'SERP Feature Change', items: [] }
        };
        
        monthData.forEach(d => {
            if (d.status === 'Competitor Update') { categories['Competitor Intel'].count++; categories['Competitor Intel'].items.push(d); }
            else if (d.status === 'Brand Mention') { categories['Brand Mentions'].count++; categories['Brand Mentions'].items.push(d); }
            else if (d.status === 'SERP Feature Change') { categories['SERP Features'].count++; categories['SERP Features'].items.push(d); }
            else if (['SERVICE_INFORMATION','AVAILABLE','RESOLVED'].some(s => (d.status || '').includes(s))) { categories['Official Updates'].count++; categories['Official Updates'].items.push(d); }
            else { categories['Community & Algo'].count++; categories['Community & Algo'].items.push(d); }
        });
        
        const maxCount = Math.max(...Object.values(categories).map(c => c.count), 1);
        
        // Render breakdown bars (clickable!)
        const breakdownEl = document.getElementById('categoryBreakdown');
        breakdownEl.innerHTML = Object.entries(categories)
            .sort((a, b) => b[1].count - a[1].count)
            .map(([name, {count, color, filter}]) => `
                <div class="breakdown-item" data-filter="${filter}" title="Click to filter: ${name}">
                    <span class="breakdown-label">${name}</span>
                    <div class="breakdown-bar-track">
                        <div class="breakdown-bar-fill" data-width="${(count/maxCount)*100}" style="background: ${color};"></div>
                    </div>
                    <span class="breakdown-count" style="color: ${color};">${count}</span>
                </div>
            `).join('');

        // Animate bars after render
        requestAnimationFrame(() => {
            setTimeout(() => {
                breakdownEl.querySelectorAll('.breakdown-bar-fill').forEach(bar => {
                    bar.style.width = bar.dataset.width + '%';
                });
            }, 150);
        });

        // Clickable bars → filter
        breakdownEl.querySelectorAll('.breakdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const f = item.dataset.filter;
                filterBtns.forEach(b => b.classList.remove("active"));
                const matchBtn = document.querySelector(`.filter-btn[data-filter="${f}"]`);
                if (matchBtn) matchBtn.classList.add("active");
                currentFilter = f;
                applyAll();
                // Smooth scroll to cards
                document.getElementById('alertsGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
        
        // AI/LLM tracker
        const aiCount = monthData.filter(d => {
            const sev = (d.severity || '').toLowerCase();
            return sev.includes('ai') || sev.includes('🤖') || sev.includes('llm');
        }).length;
        const aiPct = monthData.length > 0 ? Math.round((aiCount / monthData.length) * 100) : 0;
        
        animateCounter(document.getElementById('aiCount'), aiCount);
        document.getElementById('aiPctText').textContent = `${aiPct}% of all signals this month`;
        setTimeout(() => {
            document.getElementById('aiPctFill').style.width = `${aiPct}%`;
        }, 400);
        
        // Top sources (clickable!)
        const sourceCounts = {};
        monthData.forEach(d => {
            const src = d.source || 'Unknown';
            sourceCounts[src] = (sourceCounts[src] || 0) + 1;
        });
        const sortedSources = Object.entries(sourceCounts).sort((a,b) => b[1] - a[1]).slice(0, 6);
        const sourceColors = ['#BB86FC', '#64B5F6', '#4DB6AC', '#FFB74D', '#F06292', '#AED581'];
        
        document.getElementById('topSources').innerHTML = sortedSources
            .map(([name, count], i) => `
                <div class="source-row" data-source="${name}" title="Click to search: ${name}">
                    <span class="source-name">
                        <span class="source-dot" style="background: ${sourceColors[i % sourceColors.length]};"></span>
                        ${name}
                    </span>
                    <span class="source-count">${count}</span>
                </div>
            `).join('');

        // Clickable sources → search
        document.querySelectorAll('.source-row[data-source]').forEach(row => {
            row.addEventListener('click', () => {
                const src = row.dataset.source;
                searchInput.value = src;
                searchQuery = src;
                searchClear.classList.remove("hidden");
                currentFilter = "all";
                filterBtns.forEach(b => b.classList.remove("active"));
                document.querySelector('.filter-btn[data-filter="all"]').classList.add("active");
                applyAll();
                document.getElementById('alertsGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
        
        // Key highlights (clickable!)
        const highlights = [];
        
        const latestAI = monthData.find(d => d.status === 'Competitor Update' && ((d.severity||'').includes('AI') || (d.severity||'').includes('🤖')));
        if (latestAI) highlights.push({ emoji: '🤖', text: latestAI.title, url: latestAI.url, type: 'AI/LLM' });
        
        const latestBrand = monthData.find(d => d.status === 'Brand Mention');
        if (latestBrand) highlights.push({ emoji: '🎯', text: latestBrand.title, url: latestBrand.url, type: 'Brand' });
        
        const latestOfficial = monthData.find(d => ['SERVICE_INFORMATION','AVAILABLE','RESOLVED'].some(s => (d.status||'').includes(s)));
        if (latestOfficial) highlights.push({ emoji: '📢', text: latestOfficial.title, url: latestOfficial.url, type: 'Official' });
        
        const latestCommunity = monthData.find(d => ['Community Report','UGC Discussion','Official Announcement'].includes(d.status));
        if (latestCommunity) highlights.push({ emoji: '📰', text: latestCommunity.title, url: latestCommunity.url, type: 'Community' });
        
        const latestComp = monthData.find(d => d.status === 'Competitor Update' && !((d.severity||'').includes('AI') || (d.severity||'').includes('🤖')));
        if (latestComp) highlights.push({ emoji: '🏢', text: latestComp.title, url: latestComp.url, type: 'Competitor' });
        
        document.getElementById('keyHighlights').innerHTML = highlights.length > 0 
            ? highlights.map(h => `
                <div class="highlight-item" title="Open source" onclick="window.open('${h.url}', '_blank')">
                    ${h.emoji} <strong>${h.text}</strong>
                </div>
            `).join('')
            : '<div class="highlight-item">No highlights yet this month.</div>';
        
        // Subtitle
        document.getElementById('summarySubtitle').textContent = 
            `${monthData.length} signals tracked • ${aiCount} AI/LLM flagged • ${categories['Competitor Intel'].count} competitor updates`;
    };
    
    // ─── Summary Toggle ─────────────────────────────────────
    document.getElementById('summaryToggle').addEventListener('click', () => {
        const body = document.getElementById('summaryBody');
        const icon = document.getElementById('toggleIcon');
        body.classList.toggle('collapsed');
        icon.classList.toggle('collapsed');
    });

    // ─── Last Updated ───────────────────────────────────────
    const setLastUpdated = (data) => {
        if (data.length === 0) return;
        const latest = data.reduce((a, b) => new Date(a.date) > new Date(b.date) ? a : b);
        document.getElementById('lastUpdated').textContent = `Last updated: ${formatDate(latest.date)}`;
    };

    // ─── Fetch Data ─────────────────────────────────────────
    fetch('dashboard_data.json')
        .then(response => {
            if (!response.ok) throw new Error("Could not load data");
            return response.json();
        })
        .then(data => {
            allData = data;
            updateStats(data);
            updateFilterCounts(data);
            buildMonthlySummary(data);
            setLastUpdated(data);
            applyAll();
        })
        .catch(error => {
            alertsGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <h3>Error Loading Data</h3>
                    <p>Could not load dashboard_data.json. Make sure the Python script has run at least once.</p>
                </div>
            `;
            console.error(error);
        });
});
