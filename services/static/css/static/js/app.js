// Tab Switcher
function switchTab(tab) {
    const wishlistTab = document.getElementById('tab-wishlist-btn');
    const techTab = document.getElementById('tab-tech-btn');
    const wishlistContent = document.getElementById('tab-wishlist-content');
    const techContent = document.getElementById('tab-tech-content');

    if (tab === 'wishlist') {
        wishlistTab.className = 'pb-3 px-4 font-bold text-sm border-b-2 border-red-500 text-red-400 transition-all';
        techTab.className = 'pb-3 px-4 font-bold text-sm border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-all';
        wishlistContent.classList.remove('hidden');
        techContent.classList.add('hidden');
    } else {
        techTab.className = 'pb-3 px-4 font-bold text-sm border-b-2 border-sky-500 text-sky-400 transition-all';
        wishlistTab.className = 'pb-3 px-4 font-bold text-sm border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-all';
        techContent.classList.remove('hidden');
        wishlistContent.classList.add('hidden');
    }
}

// Animated snowfall effect
function initSnow() {
    const container = document.getElementById('snow-container');
    if (!container) return;
    const particleCount = 35;
    for (let i = 0; i < particleCount; i++) {
        const flake = document.createElement('div');
        flake.className = 'snowflake';
        const size = Math.random() * 4 + 2 + 'px';
        flake.style.width = size;
        flake.style.height = size;
        flake.style.left = Math.random() * 100 + 'vw';
        flake.style.opacity = Math.random() * 0.7 + 0.3;
        flake.style.animationDuration = Math.random() * 8 + 5 + 's';
        flake.style.animationDelay = Math.random() * 5 + 's';
        container.appendChild(flake);
    }
}
document.addEventListener('DOMContentLoaded', initSnow);

// Christmas Countdown Logic
function updateCountdown() {
    const timerElem = document.getElementById('countdown-timer');
    if (!timerElem) return;
    const now = new Date();
    const currentYear = now.getFullYear();
    let xmas = new Date(currentYear, 11, 25);
    if (now > xmas) {
        xmas = new Date(currentYear + 1, 11, 25);
    }
    const diffTime = xmas - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    timerElem.innerText = `${diffDays} Days Left!`;
}
setInterval(updateCountdown, 1000);
updateCountdown();

const themeStyles = {
    'festive-red': { border: 'border-red-900/60', bg: 'bg-red-950/40', badge: 'bg-red-900 text-red-200 border border-red-700' },
    'pine-green': { border: 'border-emerald-900/60', bg: 'bg-emerald-950/40', badge: 'bg-emerald-900 text-emerald-200 border border-emerald-700' },
    'frozen-ice': { border: 'border-sky-900/60', bg: 'bg-sky-950/40', badge: 'bg-sky-900 text-sky-200 border border-sky-700' },
    'golden-bell': { border: 'border-amber-900/60', bg: 'bg-amber-950/40', badge: 'bg-amber-900 text-amber-200 border border-amber-700' }
};

let lastWishlistData = null;

function addUrlInput() {
    const container = document.getElementById('url-inputs');
    const count = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'flex gap-2';
    div.innerHTML = `
        <input type="url" placeholder="Gift Item URL #${count}: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-red-500 transition-colors">
        <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-xl hover:bg-rose-900/50 transition-colors font-semibold text-sm">Remove</button>
    `;
    container.appendChild(div);
}

function removeInput(button) {
    const container = document.getElementById('url-inputs');
    if (container.children.length > 1) {
        button.parentElement.remove();
    } else {
        alert("You must keep at least one wishlist URL field.");
    }
}

async function analyzeWishlist() {
    const wishlistName = document.getElementById('wishlist-name').value.trim() || "Santa's Wishlist";
    const colorTheme = document.getElementById('color-theme').value;
    const inputs = document.querySelectorAll('.url-input');
    const urls = Array.from(inputs).map(input => input.value.trim()).filter(val => val.length > 0);

    if (urls.length === 0) {
        alert("Please enter at least one Amazon gift URL.");
        return;
    }

    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    submitBtn.disabled = true;
    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/analyze-wishlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wishlist_name: wishlistName, color_theme: colorTheme, urls })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to analyze Christmas wishlist.");
        }

        const data = await response.json();
        lastWishlistData = data;
        
        const theme = themeStyles[data.color_theme] || themeStyles['festive-red'];
        const boardHeader = document.getElementById('board-header');
        boardHeader.className = `border ${theme.border} ${theme.bg} p-6 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4 transition-all shadow-xl`;
        
        const badge = document.getElementById('board-badge');
        badge.className = `px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${theme.badge}`;
        badge.innerText = `🎄 Christmas Wishlist Menu`;

        document.getElementById('display-wishlist-name').innerText = data.wishlist_name;
        document.getElementById('summary-orig').innerText = `Original Total: ${data.currency}${data.total_original_price.toFixed(2)}`;
        document.getElementById('summary-sale').innerText = `Current Sale Total: ${data.currency}${data.total_sale_price.toFixed(2)}`;
        document.getElementById('summary-xmas').innerText = `🎄 Christmas Forecast: ${data.currency}${data.total_christmas_price.toFixed(2)}`;

        updateSplit();

        const itemsContainer = document.getElementById('items-container');
        itemsContainer.innerHTML = '';

        data.items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'bg-slate-950 border border-red-900/30 p-6 rounded-2xl space-y-4 shadow-lg';
            card.innerHTML = `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                        <span class="text-xs font-mono text-red-300 bg-red-950/60 border border-red-800/50 px-2.5 py-1 rounded-lg mr-2 font-bold">🎁 Gift #${index + 1}</span>
                        <h4 class="font-bold text-lg text-slate-100 inline-block mt-1">${item.title}</h4>
                    </div>
                    <div class="text-right space-y-0.5">
                        <div class="text-xs text-slate-400 line-through">Reg: ${item.currency}${item.original_price.toFixed(2)}</div>
                        <div class="text-sm text-slate-300">Now: ${item.currency}${item.sale_price.toFixed(2)}</div>
                        <div class="text-lg font-black text-amber-300">🎄 Christmas Est: ${item.currency}${item.christmas_forecast_price.toFixed(2)}</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="bg-emerald-950/20 border border-emerald-800/40 p-3 rounded-xl">
                        <span class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block mb-0.5">⚡ Eco-Efficiency Rating</span>
                        <span class="text-xs text-slate-200">${item.eco_efficiency_rating}</span>
                    </div>
                    <div class="bg-sky-950/20 border border-sky-800/40 p-3 rounded-xl">
                        <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider block mb-0.5">📦 Holiday Shipping Deadline</span>
                        <span class="text-xs text-slate-200">${item.shipping_deadline_estimate}</span>
                    </div>
                </div>

                <div class="bg-amber-950/20 border border-amber-600/30 p-4 rounded-xl">
                    <h5 class="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">🎅 Christmas Price Forecast & Trend</h5>
                    <p class="text-slate-200 text-sm leading-relaxed">${item.christmas_forecast_reason}</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-900">
                    <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-800/60">
                        <h5 class="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1">❄️ Winter Weather Suitability</h5>
                        <p class="text-slate-300 text-sm leading-relaxed">${item.weather_suitability}</p>
                    </div>
                    <div class="bg-slate-900/50 p-4 rounded-xl border border-slate-800/60">
                        <h5 class="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">🔌 Compatibility & Requirements</h5>
                        <p class="text-slate-300 text-sm leading-relaxed">${item.compatibility_analysis}</p>
                    </div>
                </div>
            `;
            itemsContainer.appendChild(card);
        });

        results.classList.remove('hidden');
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        submitBtn.disabled = false;
        loading.classList.add('hidden');
    }
}

function updateSplit() {
    if (!lastWishlistData) return;
    const countInput = document.getElementById('split-count');
    const resultSpan = document.getElementById('split-result');
    if (!countInput || !resultSpan) return;
    const count = parseInt(countInput.value) || 1;
    const perPerson = lastWishlistData.total_christmas_price / Math.max(count, 1);
    resultSpan.innerText = `${lastWishlistData.currency}${perPerson.toFixed(2)} / person`;
}

function triggerRoast() {
    if (!lastWishlistData || !lastWishlistData.items) return;
    const count = lastWishlistData.items.length;
    let roast = `Your ${count}-item holiday board is decent, but let's be real: `;
    if (count < 3) {
        roast += "it's looking a bit sparse! You're missing essential power adapters, cables, or backup gear to make this setup fully operational.";
    } else {
        roast += "you've got a solid mix! Just make sure your power supplies and port connections match up so you don't run into bottleneck issues on Christmas day.";
    }
    const roastTextElem = document.getElementById('roast-text');
    if (roastTextElem) roastTextElem.innerText = roast;
}

function subscribeAlerts() {
    const emailElem = document.getElementById('alert-email');
    if (!emailElem) return;
    const email = emailElem.value.trim();
    if (!email || !email.includes('@')) {
        alert("Please enter a valid email address for price alerts.");
        return;
    }
    alert(`Success! Price drop and Christmas target alerts registered for ${email}. You will be notified when items hit holiday lows!`);
    emailElem.value = '';
}

async function runTechAdvisor() {
    const needs = document.getElementById('tech-needs').value.trim();
    const budget = document.getElementById('tech-budget').value.trim();
    const cartUrl = document.getElementById('tech-cart-url').value.trim();

    if (!needs || !budget) {
        alert("Please fill in both your needs and budget range.");
        return;
    }

    const submitBtn = document.getElementById('tech-submit-btn');
    const loading = document.getElementById('tech-loading');
    const results = document.getElementById('tech-results');

    submitBtn.disabled = true;
    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/tech-advisor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_needs: needs,
                budget_range: budget,
                cart_urls: cartUrl ? [cartUrl] : []
            })
        });

        if (!response.ok) throw new Error("Failed to generate tech recommendation.");
        const data = await response.json();

        document.getElementById('tech-summary-text').innerText = data.ai_recommendation_summary;
        document.getElementById('tech-specs-text').innerText = data.recommended_specs;

        const evalContainer = document.getElementById('cart-evaluations-container');
        evalContainer.innerHTML = '<h4 class="font-bold text-slate-100 text-lg mt-4">Cart / Wishlist Item Evaluations</h4>';

        if (data.cart_evaluations && data.cart_evaluations.length > 0) {
            data.cart_evaluations.forEach(item => {
                const statusColor = item.is_good_match ? 'text-emerald-400 border-emerald-900 bg-emerald-950/20' : 'text-rose-400 border-rose-900 bg-rose-950/20';
                const statusBadge = item.is_good_match ? '✅ Good Match' : '⚠️ Poor Match / Bottleneck';
                
                const div = document.createElement('div');
                div.className = `border p-5 rounded-2xl space-y-2 ${statusColor}`;
                div.innerHTML = `
                    <div class="flex justify-between items-center">
                        <h5 class="font-bold text-slate-100">${item.title}</h5>
                        <span class="px-2.5 py-1 text-xs font-black rounded-lg uppercase tracking-wider border">${statusBadge}</span>
                    </div>
                    <p class="text-slate-300 text-sm"><strong>Verdict:</strong> ${item.verdict_reason}</p>
                    <p class="text-slate-400 text-xs"><strong>Alternative Suggestion:</strong> ${item.alternative_suggestion}</p>
                `;
                evalContainer.appendChild(div);
            });
        } else {
            const div = document.createElement('div');
            div.className = 'text-slate-400 text-sm italic bg-slate-950 p-4 rounded-xl border border-slate-800';
            div.innerText = 'No cart URL was provided for individual hardware evaluation. Paste a product URL above to check if it fits your needs!';
            evalContainer.appendChild(div);
        }

        results.classList.remove('hidden');
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        submitBtn.disabled = false;
        loading.classList.add('hidden');
    }
}
