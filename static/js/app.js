// --- Global State Management ---
let currentSeason = 'winter';
let isBoringNerdMode = false;
let lastWishlistData = {
    wishlist_name: "Ultimate Seasonal Tech Hub",
    currency: "$",
    total_christmas_price: 262.48,
    items: [
        { title: "Wireless Noise-Canceling Headphones", christmas_forecast_price: 199.99 },
        { title: "Smart Weather Station Hub", christmas_forecast_price: 62.49 }
    ]
};

// --- Season Engine Handler ---
function changeSeason(season) {
    currentSeason = season;
    const badge = document.getElementById('footer-item-subtitle');
    if (badge) {
        badge.innerText = `Season: ${season.toUpperCase()} | Mode: ${isBoringNerdMode ? 'Boring Nerd Mode' : 'Fun & Cute'}`;
    }
}

// --- Boring Nerd Mode Toggle ---
function toggleBoringMode() {
    isBoringNerdMode = !isBoringNerdMode;
    const btn = document.getElementById('boring-mode-btn');
    
    if (isBoringNerdMode) {
        btn.innerText = "📊 Nerd Mode: Active";
        btn.classList.add('border-emerald-500', 'text-emerald-400');
        document.body.classList.add('nerd-analytics-active');
    } else {
        btn.innerText = "📊 Nerd Mode: Off";
        btn.classList.remove('border-emerald-500', 'text-emerald-400');
        document.body.classList.remove('nerd-analytics-active');
    }
    
    // Refresh matrix and budget calculations in nerd style if needed
    updatePriceMatrix();
}

// --- Feature 1: Smart Budget Allocator Logic ---
function runSmartBudget() {
    const budgetInput = document.getElementById('user-budget-input').value;
    const budget = parseFloat(budgetInput) || 250;
    const resultsContainer = document.getElementById('budget-allocation-results');

    const items = [
        { title: "Seasonal Holiday Gift Box", price: 79.99 },
        { title: "Smart LED Ambient Light", price: 45.50 },
        { title: "Premium Winter Tech Gloves", price: 34.00 },
        { title: "Gourmet Coffee Sampler Pack", price: 28.99 },
        { title: "Compact Bluetooth Speaker", price: 89.00 }
    ];

    let totalCost = items.reduce((sum, item) => sum + item.price, 0);
    
    if (isBoringNerdMode) {
        // Nerd mode extra granular statistics
        let variance = (totalCost - budget).toFixed(2);
        resultsContainer.innerHTML = `
            <div class="space-y-1 font-mono text-[11px]">
                <div class="text-sky-400 font-bold">[NERD METRICS] Variance Analysis: ${variance > 0 ? '+' + variance : variance} USD</div>
                <div>Total Sum: $${totalCost.toFixed(2)} | Target Cap: $${budget.toFixed(2)}</div>
                <div class="${totalCost <= budget ? 'text-emerald-400' : 'text-rose-400'} font-bold">
                    Status: ${totalCost <= budget ? 'OPTIMAL (Within Threshold)' : 'CRITICAL (Exceeds Limit)'}
                </div>
            </div>
        `;
    } else {
        if (totalCost <= budget) {
            resultsContainer.innerHTML = `<span class="text-emerald-400 font-bold">✅ Within Budget!</span> Total estimated items cost is $${totalCost.toFixed(2)}, which is well within your $${budget.toFixed(2)} limit.`;
        } else {
            let diff = (totalCost - budget).toFixed(2);
            resultsContainer.innerHTML = `<span class="text-rose-400 font-bold">⚠️ Budget Exceeded by $${diff}!</span> Total items value: $${totalCost.toFixed(2)}.`;
        }
    }
}

// --- Feature 2: Multi-Store Price Comparison Matrix ---
function updatePriceMatrix() {
    const matrixBody = document.getElementById('price-matrix-body');
    if (!matrixBody) return;

    const matrixData = [
        { name: "Wireless Noise-Canceling Headphones", amazon: "$199.99", walmart: "$210.00", target: "$205.00", best: "Amazon ($199.99)" },
        { name: "Smart Weather Station Hub", amazon: "$84.50", walmart: "$79.99", target: "$89.00", best: "Walmart ($79.99)" },
        { name: "Seasonal LED Projector", amazon: "$49.99", walmart: "$52.00", target: "$49.99", best: "Amazon / Target ($49.99)" }
    ];

    matrixBody.innerHTML = matrixData.map(row => `
        <tr class="hover:bg-white/5 transition-all">
            <td class="p-3 font-medium text-white">${row.name} ${isBoringNerdMode ? '<span class="text-[10px] text-sky-400 font-mono">[SKU-ID: 9942]</span>' : ''}</td>
            <td class="p-3 text-slate-400">${row.amazon}</td>
            <td class="p-3 text-slate-400">${row.walmart}</td>
            <td class="p-3 text-slate-400">${row.target}</td>
            <td class="p-3 text-emerald-400 font-bold">${row.best}</td>
        </tr>
    `).join('');
}

// --- Feature 3: Interactive Price Predictor Sparkline Generator ---
function generatePriceChartSVG() {
    const points = [65, 70, 85, 90, 80, 75, 60, 55, 65, 85, 95, 70];
    const max = Math.max(...points);
    const min = Math.min(...points);
    const height = 40;
    const width = 180;
    
    let pathD = "";
    points.forEach((val, index) => {
        const x = (index / (points.length - 1)) * width;
        const y = height - ((val - min) / (max - min || 1)) * height;
        pathD += (index === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });

    return `
        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800 space-y-1">
            <div class="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>12-Month Price Trajectory</span>
                <span class="text-amber-400">Peak: Nov/Dec</span>
            </div>
            <svg class="w-full h-10 overflow-visible" viewBox="0 0 ${width} ${height}">
                <path d="${pathD}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    `;
}

// --- Feature 4: Printable PDF / Checklist Export ---
function exportWishlistPrint() {
    if (!lastWishlistData) {
        alert("Please generate a wishlist first before exporting.");
        return;
    }
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
        <head>
            <title>${lastWishlistData.wishlist_name} - Printable Checklist</title>
            <style>
                body { font-family: sans-serif; padding: 20px; color: #000; }
                h1 { font-size: 24px; margin-bottom: 5px; }
                .item { border-bottom: 1px solid #ccc; padding: 10px 0; display: flex; justify-content: space-between; }
                .total { font-weight: bold; margin-top: 20px; font-size: 18px; }
            </style>
        </head>
        <body>
            <h1>📋 ${lastWishlistData.wishlist_name}</h1>
            <p>Generated via Apple Music Style Seasonal Tech & Wishlist Hub</p>
            <hr/>
            <div>
                ${lastWishlistData.items.map((item, i) => `
                    <div class="item">
                        <div>[ ] <strong>#${i+1}:${item.title}</strong></div>
                        <div>Est: ${lastWishlistData.currency}${item.christmas_forecast_price.toFixed(2)}</div>
                    </div>
                `).join('')}
            </div>
            <div class="total">
                Total Forecast: ${lastWishlistData.currency}${lastWishlistData.total_christmas_price.toFixed(2)}
            </div>
            <script>
                window.print();
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

// --- App Initialization on DOM Load ---
document.addEventListener('DOMContentLoaded', () => {
    updatePriceMatrix();
    console.log("Apple Music UI & Nerd Mode framework initialized.");
});

function togglePlaybackState() {
    const btn = document.getElementById('play-pause-btn');
    if (btn.innerText === "▶") {
        btn.innerText = "⏸";
    } else {
        btn.innerText = "▶";
    }
}
