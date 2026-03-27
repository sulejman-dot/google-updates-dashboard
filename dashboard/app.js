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
            const badgeText = alert.status === "Brand Mention" ? alert.severity : alert.status;

            // Source icon
            let sourceIcon = "🌐";
            if (alert.source.includes("Reddit")) sourceIcon = "🗣️";
            else if (alert.source.includes("Hacker News")) sourceIcon = "💻";
            else if (alert.source.includes("Roundtable")) sourceIcon = "📰";
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
    };

    // Filter Logic
    const applyFilter = (filterParam) => {
        let filteredData = allData;
        if (filterParam !== "all") {
            if (filterParam === "official") {
                filteredData = allData.filter(d => !["Brand Mention", "UGC Discussion", "SERP Feature Change"].includes(d.status));
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

    // Fetch Data
    fetch('dashboard_data.json')
        .then(response => {
            if (!response.ok) throw new Error("Could not load data");
            return response.json();
        })
        .then(data => {
            allData = data;
            updateStats(data);
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
