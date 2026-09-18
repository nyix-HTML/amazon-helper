// Tab Switcher
function switchTab(tab) {
    const wishlistTab = document.getElementById('tab-wishlist-btn');
    const techTab = document.getElementById('tab-tech-btn');
    const wishlistContent = document.getElementById('tab-wishlist-content');
    const techContent = document.getElementById('tab-tech-content');

    if (tab === 'wishlist') {
        wishlistTab.className = 'pb-3 px-4 font-bold text-sm border-b-2 border-pink-500 text-pink-400 transition-all';
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

// Seasonal Particle & Clicker Mini-game Engine
let seasonPoints = 0;
const seasonData = {
    winter: { emoji: '❄️', title: 'Winter Wonderland & Christmas Hub', mascot: '🎅', particleClass: 'snowflake' },
    spring: { emoji: '🌸', title: 'Spring Fling & Blossom Wishlist Hub', mascot: '🐰', particleClass: 'petal' },
    summer: { emoji: '☀️', title: 'Summer Sizzle & Sunshine Tech Hub', mascot: '😎', particleClass: 'sunbeam' },
    autumn: { emoji: '🍂', title: 'Autumn Harvest & Cozy Tech Hub', mascot: '🦊', particleClass: 'leaf' }
};

function changeSeason(seasonKey) {
    const data = seasonData[seasonKey] || seasonData.winter;
    document.getElementById('main-title').innerText = data.title;
    document.getElementById('mascot-avatar').innerText = data.mascot;
    document.getElementById('tracker-icon').innerText = data.emoji;
    
    // Re-initialize particles for active season
    initParticles(data.particleClass);
}

function initParticles(particleType = 'snowflake') {
    const container = document.getElementById('particle-container');
    if (!container) return;
    container.innerHTML = '';
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const flake = document.createElement('div');
        flake.className = `particle ${particleType}`;
        const size = Math.random() * 6 + 4 + 'px';
        flake.style.width = size;
        flake.style.height = size;
        flake.style.left = Math.random() * 100 + 'vw';
        flake.style.opacity = Math.random() * 0.7 + 0.3;
        flake.style.animationDuration = Math.random() * 8 + 5 + 's';
        flake.style.animationDelay = Math.random() * 5 + 's';
        
        // Clicker mini-game listener
        flake.addEventListener('click', () => {
            seasonPoints += 10;
            document.getElementById('clicker-score').innerText = `✨ ${seasonPoints} Points`;
            flake.remove();
        });
        
        container.appendChild(flake);
    }
}

function pokeMascot() {
    seasonPoints += 5;
    document.getElementById('clicker-score').innerText = `✨ ${seasonPoints} Points`;
    const speeches = [
        "Your wishlist is looking magical!",
        "Did you remember to check the power supply?",
        "Prices look great for this season!",
        "Click falling particles for bonus points!"
    ];
    const randomSpeech = speeches[Math.floor(Math.random() * speeches.length)];
    document.getElementById('mascot-speech').innerText = randomSpeech;
}

// Countdown Logic
function updateCountdown() {
    const countdownEl = document.getElementById('christmas-countdown');
    const now = new Date();
    let targetDate = new Date(now.getFullYear(), 11, 25); // Dec 25
    if (now > targetDate) targetDate.setFullYear(targetDate.getFullYear() + 1);
    
    const diff = targetDate - now;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((diff / 1000 / 60) % 60);
    const seconds = Math.floor((diff / 1000) % 60);
    
    if (countdownEl) countdownEl.innerText = `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

let lastWishlistData = null;

function addUrlInput() {
    const container = document.getElementById('url-inputs');
    const count = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'flex gap-2';
    div.innerHTML = `
        <input type="url" placeholder="Gift Item URL #${count}: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-pink-500 transition-colors">
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
    const wishlistName = document.getElementById('wishlist-name').value.trim() || "Seasonal Wishlist";
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

        if (!response.ok) throw new Error("Failed to analyze wishlist.");

        const data = await response.json();
        lastWishlistData = data;
        
        document.getElementById('display-wishlist-name').innerText = data.wishlist_name;
        document.getElementById('summary-orig').innerText = `Original Total: ${data.currency}${data.total_original_price.toFixed(2)}`;
        document.getElementById('summary-sale').innerText = `Current Sale Total: ${data.currency}${data.total_sale_price.toFixed(2)}`;
        document.getElementById('summary-xmas').innerText = `✨ Seasonal Forecast: ${data.currency}${data.total_christmas_price.toFixed(2)}`;

        updateSplit();

        const itemsContainer = document.getElementById('items-container');
        itemsContainer.innerHTML = '';

        data.items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'bg-slate-950 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-lg';
            card.innerHTML = `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                        <span class="text-xs font-mono text-pink-300 bg-pink-950/60 border border-pink-800/50 px-2.5 py-1 rounded-lg mr-2 font-bold">🎁 Gift #${index + 1}</span>
                        <h4 class="font-bold text-lg text-slate-100 inline-block mt-1">${item.title}</h4>
                    </div>
                    <div class="text-right space-y-0.5">
                        <div class="text-xs text-slate-400 line-through">Reg: ${item.currency}${item.original_price.toFixed(2)}</div>
                        <div class="text-sm text-slate-300">Now: ${item.currency}${item.sale_price.toFixed(2)}</div>
                        <div class="text-lg font-black text-amber-300">✨ Seasonal Est: ${item.currency}${item.christmas_forecast_price.toFixed(2)}</div>
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
    const roastTextElem = document.getElementById('roast-text');
    if (roastTextElem) roastTextElem.innerText = "Your cart is looking solid, but make sure your power supply can handle the load!";
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
            body: JSON.stringify({ user_needs: needs, budget_range: budget, cart_urls: cartUrl ? [cartUrl] : [] })
        });

        if (!response.ok) throw new Error("Failed to generate tech recommendation.");
        const data = await response.json();

        document.getElementById('tech-summary-text').innerText = data.ai_recommendation_summary;
        document.getElementById('tech-specs-text').innerText = data.recommended_specs;
        results.classList.remove('hidden');
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        submitBtn.disabled = false;
        loading.classList.add('hidden');
    }
}

async function updateSantaTracker() {
    try {
        const response = await fetch('/api/santa-status');
        const data = await response.json();
        document.getElementById('tracker-location').innerText = data.location;
        document.getElementById('tracker-status').innerText = data.status;
        document.getElementById('tracker-speed').innerText = data.speed_mph.toLocaleString() + ' mph';
        document.getElementById('tracker-presents').innerText = data.presents_delivered.toLocaleString();
    } catch (error) {
        console.error('Error fetching tracker status:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initParticles('snowflake');
    updateSantaTracker();
    updateCountdown();
    setInterval(updateSantaTracker, 6000);
    setInterval(updateCountdown, 1000);
});
