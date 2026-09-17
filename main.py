from __future__ import annotations

import asyncio
import json
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from google import genai
from google.genai import types

from scraper import scrape_amazon_product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Christmas Wishlist & Setup Analyzer")

client = genai.Client()

class WishlistInput(BaseModel):
    wishlist_name: str
    color_theme: str
    urls: List[HttpUrl]

class ProductAnalysis(BaseModel):
    title: str
    original_price: float
    sale_price: float
    currency: str
    weather_suitability: str
    compatibility_analysis: str
    christmas_forecast_price: float
    christmas_forecast_reason: str

class WishlistSummary(BaseModel):
    wishlist_name: str
    color_theme: str
    items: List[ProductAnalysis]
    total_original_price: float
    total_sale_price: float
    total_christmas_price: float
    currency: str

async def analyze_product_with_ai(product_data: dict) -> dict:
    prompt = f"""
    Analyze the following product details extracted from an e-commerce page:
    Title: {product_data['title']}
    Current Price: {product_data['currency']}{product_data['sale_price']}

    Provide three specific assessments in valid JSON format:
    1. "weather_suitability": Evaluate how weather conditions (rain, winter cold, snow, extreme heat, indoor-only usage) affect this product's performance or durability during the winter holiday season.
    2. "compatibility_analysis": Analyze what other hardware, software, accessories, or specific connection standards this item physically or digitally requires to work properly. If standalone, write "Standalone item; no external dependencies."
    3. "christmas_forecast": Estimate the expected price of this item around Christmas time (factoring in Black Friday deals, Cyber Monday, holiday surges, or clearance), and provide a short numerical float for "forecast_price" and a string for "forecast_reason".

    Return strictly a JSON object with keys: 
    - "weather_suitability" (string)
    - "compatibility_analysis" (string)
    - "christmas_forecast_price" (float)
    - "christmas_forecast_reason" (string)
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        result_json = json.loads(response.text)
        return {
            "weather_suitability": result_json.get("weather_suitability", "Winter evaluation unavailable."),
            "compatibility_analysis": result_json.get("compatibility_analysis", "Compatibility check unavailable."),
            "christmas_forecast_price": float(result_json.get("christmas_forecast_price", product_data['sale_price'])),
            "christmas_forecast_reason": result_json.get("christmas_forecast_reason", "Expected to follow seasonal holiday pricing trends.")
        }
    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}")
        fallback_price = round(product_data['sale_price'] * 0.9, 2)
        return {
            "weather_suitability": "Cozy indoor holiday usage recommended.",
            "compatibility_analysis": "Standalone item or standard compatibility.",
            "christmas_forecast_price": fallback_price,
            "christmas_forecast_reason": "Estimated slight holiday discount approximation."
        }

@app.post("/api/analyze-wishlist", response_model=WishlistSummary)
async def analyze_wishlist(payload: WishlistInput):
    if not payload.urls:
        raise HTTPException(status_code=400, detail="At least one URL must be provided.")

    tasks = [scrape_amazon_product(str(url)) for url in payload.urls]
    scraped_results = await asyncio.gather(*tasks)

    analyzed_items = []
    total_orig = 0.0
    total_sale = 0.0
    total_xmas = 0.0
    currency = "$"

    for item in scraped_results:
        currency = item["currency"]
        ai_insights = await analyze_product_with_ai(item)
        
        analysis = ProductAnalysis(
            title=item["title"],
            original_price=item["original_price"],
            sale_price=item["sale_price"],
            currency=item["currency"],
            weather_suitability=ai_insights["weather_suitability"],
            compatibility_analysis=ai_insights["compatibility_analysis"],
            christmas_forecast_price=ai_insights["christmas_forecast_price"],
            christmas_forecast_reason=ai_insights["christmas_forecast_reason"]
        )
        analyzed_items.append(analysis)
        total_orig += item["original_price"]
        total_sale += item["sale_price"]
        total_xmas += ai_insights["christmas_forecast_price"]

    return WishlistSummary(
        wishlist_name=payload.wishlist_name || "Santa's Ultimate Wishlist",
        color_theme=payload.color_theme || "festive-red",
        items=analyzed_items,
        total_original_price=round(total_orig, 2),
        total_sale_price=round(total_sale, 2),
        total_christmas_price=round(total_xmas, 2),
        currency=currency
    )

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎄 Festive AI Christmas Wishlist & Price Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes snowfall {
            0% { transform: translateY(-10vh) translateX(0); opacity: 1; }
            100% { transform: translateY(105vh) translateX(20px); opacity: 0.2; }
        }
        .snowflake {
            position: fixed;
            top: -10vh;
            background: white;
            border-radius: 50%;
            pointer-events: none;
            animation: snowfall linear infinite;
        }
        .christ-glow {
            text-shadow: 0 0 15px rgba(239, 68, 68, 0.6), 0 0 25px rgba(34, 197, 94, 0.4);
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center py-10 px-4 relative overflow-x-hidden">

    <!-- Animated Snow Globe Background Effect -->
    <div id="snow-container" class="absolute inset-0 pointer-events-none z-0 overflow-hidden"></div>

    <!-- Top Right Christmas Countdown Counter with Santa Hat -->
    <div class="absolute top-4 right-4 z-20 bg-red-950/80 border-2 border-red-600/60 backdrop-blur-md px-4 py-2 rounded-2xl shadow-2xl flex items-center gap-3">
        <div class="relative">
            <span class="text-2xl">🎅</span>
            <!-- CSS Santa Hat perched on top right emoji -->
            <div class="absolute -top-3 -right-2 text-lg transform rotate-12">🎄</div>
        </div>
        <div>
            <div class="text-[10px] font-bold text-red-300 uppercase tracking-widest">Christmas Countdown</div>
            <div id="countdown-timer" class="text-sm font-black text-emerald-400">Calculative...</div>
        </div>
    </div>

    <div class="max-w-4xl w-full bg-slate-900/90 backdrop-blur-xl border border-red-900/40 rounded-3xl shadow-2xl p-8 relative z-10 mt-6">
        <div class="text-center mb-8">
            <span class="px-3 py-1 bg-red-900/50 border border-red-700/60 text-red-300 rounded-full text-xs font-bold uppercase tracking-widest">❄️ Holiday Season 2026 ❄️</span>
            <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-emerald-400 to-amber-300 mt-2 christ-glow">
                AI Christmas Wishlist & Price Predictor
            </h1>
            <p class="text-slate-400 text-sm mt-1">
                Build your customized festive wishlist, forecast Christmas holiday pricing changes, check weather endurance, and track gear compatibility!
            </p>
        </div>

        <!-- Wishlist Configuration Panel -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 bg-slate-950/80 p-5 rounded-2xl border border-red-900/30">
            <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-red-300 uppercase tracking-wider mb-1">Wishlist Menu Name</label>
                <input type="text" id="wishlist-name" value="✨ Ultimate Holiday Dream Gift Board ✨" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-red-500 transition-colors font-medium">
            </div>
            <div>
                <label class="block text-xs font-semibold text-red-300 uppercase tracking-wider mb-1">Festive Theme Color</label>
                <select id="color-theme" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-red-500 transition-colors">
                    <option value="festive-red">🎄 Classic Christmas Red</option>
                    <option value="pine-green">🌲 Evergreen Pine</option>
                    <option value="frozen-ice">❄️ Winter Frost Blue</option>
                    <option value="golden-bell">🔔 Golden Holiday Glow</option>
                </select>
            </div>
        </div>

        <div class="mb-2 flex justify-between items-center">
            <h3 class="text-sm font-bold text-emerald-400 uppercase tracking-wider">🎁 Amazon Gift & Gear URLs</h3>
            <span class="text-xs text-slate-500">Paste your gift links below</span>
        </div>

        <div id="url-inputs" class="space-y-3 mb-4">
            <div class="flex gap-2">
                <input type="url" placeholder="Gift Item URL #1: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-red-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-xl hover:bg-rose-900/50 transition-colors font-semibold text-sm">Remove</button>
            </div>
        </div>

        <div class="flex gap-4 mb-8">
            <button onclick="addUrlInput()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl font-medium transition-colors text-sm text-red-300">
                + Add Another Gift
            </button>
            <button onclick="analyzeWishlist()" id="submit-btn" class="flex-1 px-6 py-3 bg-gradient-to-r from-red-600 to-emerald-600 hover:from-red-500 hover:to-emerald-500 text-white font-black rounded-xl shadow-lg shadow-red-600/30 transition-all uppercase tracking-wider text-sm">
                🔮 Forecast Christmas Prices & Build Wishlist
            </button>
        </div>

        <div id="loading" class="hidden text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-red-500 border-t-emerald-400 mb-4"></div>
            <p class="text-red-300 font-semibold animate-pulse">Consulting Santa's AI Workshop & Forecasting Holiday Sales...</p>
        </div>

        <div id="results" class="hidden space-y-6">
            <!-- Wishlist Summary Header Card -->
            <div id="board-header" class="border p-6 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4 transition-all shadow-xl">
                <div>
                    <span id="board-badge" class="px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider">Wishlist Menu</span>
                    <h2 id="display-wishlist-name" class="text-2xl font-black text-slate-100 mt-1">Wishlist Name</h2>
                    <p class="text-slate-400 text-sm">Detailed comparison of current prices vs estimated Christmas holiday costs.</p>
                </div>
                <div class="text-right space-y-1">
                    <div class="text-xs text-slate-400 line-through" id="summary-orig">Original Total: $0.00</div>
                    <div class="text-sm text-slate-300" id="summary-sale">Current Sale Total: $0.00</div>
                    <div class="text-2xl font-black text-amber-300" id="summary-xmas">🎄 Christmas Forecast: $0.00</div>
                </div>
            </div>

            <div id="items-container" class="space-y-4"></div>
        </div>
    </div>

    <script>
        // Create animated snowfall effect
        function initSnow() {
            const container = document.getElementById('snow-container');
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
        initSnow();

        // Christmas Countdown Logic
        function updateCountdown() {
            const now = new Date();
            const currentYear = now.getFullYear();
            let xmas = new Date(currentYear, 11, 25); // December 25th
            if (now > xmas) {
                xmas = new Date(currentYear + 1, 11, 25);
            }
            const diffTime = xmas - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            document.getElementById('countdown-timer').innerText = `${diffDays} Days Left!`;
        }
        updateCountdown();

        const themeStyles = {
            'festive-red': { border: 'border-red-900/60', bg: 'bg-red-950/40', badge: 'bg-red-900 text-red-200 border border-red-700' },
            'pine-green': { border: 'border-emerald-900/60', bg: 'bg-emerald-950/40', badge: 'bg-emerald-900 text-emerald-200 border border-emerald-700' },
            'frozen-ice': { border: 'border-sky-900/60', bg: 'bg-sky-950/40', badge: 'bg-sky-900 text-sky-200 border border-sky-700' },
            'golden-bell': { border: 'border-amber-900/60', bg: 'bg-amber-950/40', badge: 'bg-amber-900 text-amber-200 border border-amber-700' }
        };

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

                        <!-- Christmas Price Forecast Insight Box -->
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
    </script>
</body>
</html>
    """
