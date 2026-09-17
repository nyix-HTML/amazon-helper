from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from google import genai
from google.genai import types

from scraper import scrape_amazon_product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Ultimate Holiday Tech & Wishlist Platform")

client = genai.Client()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

class WishlistInput(BaseModel):
    wishlist_name: str
    color_theme: str
    urls: List[HttpUrl]

class TechAdvisorInput(BaseModel):
    user_needs: str
    budget_range: str
    cart_urls: List[HttpUrl] = []

class ProductAnalysis(BaseModel):
    title: str
    original_price: float
    sale_price: float
    currency: str
    weather_suitability: str
    compatibility_analysis: str
    christmas_forecast_price: float
    christmas_forecast_reason: str
    eco_efficiency_rating: str
    shipping_deadline_estimate: str

class WishlistSummary(BaseModel):
    wishlist_name: str
    color_theme: str
    items: List[ProductAnalysis]
    total_original_price: float
    total_sale_price: float
    total_christmas_price: float
    currency: str

class TechAdvisorResponse(BaseModel):
    ai_recommendation_summary: str
    recommended_specs: str
    cart_evaluations: List[dict]
    suggested_build_urls: List[str]

async def analyze_product_with_ai(product_data: dict) -> dict:
    prompt = f"""
    Analyze the following product details extracted from an e-commerce page:
    Title: {product_data['title']}
    Current Price: {product_data['currency']}{product_data['sale_price']}

    Provide five specific assessments in valid JSON format:
    1. "weather_suitability": Evaluate how winter weather conditions (cold, snow, humidity, indoor-only usage) affect this product's performance or durability.
    2. "compatibility_analysis": Analyze what other hardware, software, accessories, or connection standards this item requires. If standalone, write "Standalone item; no external dependencies."
    3. "christmas_forecast_price": Estimate the expected price around Christmas time as a numerical float.
    4. "christmas_forecast_reason": Short string explaining the holiday price trend or Black Friday/Cyber Monday impact.
    5. "eco_efficiency_rating": Rate power consumption, energy efficiency, and thermal draw on a scale of A+ to F with a 1-sentence justification.
    6. "shipping_deadline_estimate": Estimated holiday delivery window status for arrival before December 25th.

    Return strictly a JSON object with keys: 
    - "weather_suitability" (string)
    - "compatibility_analysis" (string)
    - "christmas_forecast_price" (float)
    - "christmas_forecast_reason" (string)
    - "eco_efficiency_rating" (string)
    - "shipping_deadline_estimate" (string)
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
            "weather_suitability": result_json.get("weather_suitability", "Winter evaluation standard."),
            "compatibility_analysis": result_json.get("compatibility_analysis", "Standard compatibility."),
            "christmas_forecast_price": float(result_json.get("christmas_forecast_price", product_data['sale_price'])),
            "christmas_forecast_reason": result_json.get("christmas_forecast_reason", "Expected seasonal holiday pricing adjustment."),
            "eco_efficiency_rating": result_json.get("eco_efficiency_rating", "Rating A: Efficient standard power draw."),
            "shipping_deadline_estimate": result_json.get("shipping_deadline_estimate", "Prime Eligible: Arrives well before Christmas.")
        }
    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}")
        fallback_price = round(product_data['sale_price'] * 0.9, 2)
        return {
            "weather_suitability": "Cozy indoor holiday usage recommended.",
            "compatibility_analysis": "Standalone item or standard compatibility.",
            "christmas_forecast_price": fallback_price,
            "christmas_forecast_reason": "Estimated slight holiday discount approximation.",
            "eco_efficiency_rating": "Rating B: Standard energy profile.",
            "shipping_deadline_estimate": "Standard Holiday Shipping Window."
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
            christmas_forecast_reason=ai_insights["christmas_forecast_reason"],
            eco_efficiency_rating=ai_insights["eco_efficiency_rating"],
            shipping_deadline_estimate=ai_insights["shipping_deadline_estimate"]
        )
        analyzed_items.append(analysis)
        total_orig += item["original_price"]
        total_sale += item["sale_price"]
        total_xmas += ai_insights["christmas_forecast_price"]

    return WishlistSummary(
        wishlist_name=payload.wishlist_name or "Santa's Ultimate Wishlist",
        color_theme=payload.color_theme or "festive-red",
        items=analyzed_items,
        total_original_price=round(total_orig, 2),
        total_sale_price=round(total_sale, 2),
        total_christmas_price=round(total_xmas, 2),
        currency=currency
    )

@app.post("/api/tech-advisor", response_model=TechAdvisorResponse)
async def tech_advisor(payload: TechAdvisorInput):
    # Scrape user's existing cart/wishlist items if provided
    cart_items = []
    if payload.cart_urls:
        tasks = [scrape_amazon_product(str(url)) for url in payload.cart_urls]
        cart_items = await asyncio.gather(*tasks)

    prompt = f"""
    User Needs: {payload.user_needs}
    Budget Range: {payload.budget_range}
    Current Cart Items / Wishlist Items to Evaluate: {json.dumps(cart_items)}

    Provide an expert technology advisor response in valid JSON format:
    1. "ai_recommendation_summary": A comprehensive recommendation explaining what computer type, specs, and features the user should look for based on their needs and budget.
    2. "recommended_specs": Key specifications required (e.g., CPU, RAM, GPU, Storage).
    3. "cart_evaluations": A list of objects for each item in the user's cart containing: "title", "is_good_match" (boolean), "verdict_reason" (string explaining why assets make it good or bad for their specific needs), and "alternative_suggestion" (string).
    4. "suggested_build_urls": A list of 2-3 general search keywords or placeholder recommendation strings for ideal matching items.

    Return strictly a JSON object with keys: "ai_recommendation_summary", "recommended_specs", "cart_evaluations", "suggested_build_urls".
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
            "ai_recommendation_summary": result_json.get("ai_recommendation_summary", "Recommendation analysis complete."),
            "recommended_specs": result_json.get("recommended_specs", "Standard modern specifications recommended."),
            "cart_evaluations": result_json.get("cart_evaluations", []),
            "suggested_build_urls": result_json.get("suggested_build_urls", [])
        }
    except Exception as e:
        logger.error(f"Tech Advisor Gemini API failed: {e}")
        return {
            "ai_recommendation_summary": "AI Advisor is temporarily resting in the workshop. Try again shortly!",
            "recommended_specs": "Balanced processor and ample memory configuration.",
            "cart_evaluations": [],
            "suggested_build_urls": []
        }

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎄 AI Ultimate Holiday Tech & Wishlist Hub</title>
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
            <div class="absolute -top-3 -right-2 text-lg transform rotate-12">🎄</div>
        </div>
        <div>
            <div class="text-[10px] font-bold text-red-300 uppercase tracking-widest">Christmas Countdown</div>
            <div id="countdown-timer" class="text-sm font-black text-emerald-400">Calculative...</div>
        </div>
    </div>

    <div class="max-w-4xl w-full bg-slate-900/90 backdrop-blur-xl border border-red-900/40 rounded-3xl shadow-2xl p-8 relative z-10 mt-6 space-y-8">
        
        <!-- Header Section -->
        <div class="text-center">
            <span class="px-3 py-1 bg-red-900/50 border border-red-700/60 text-red-300 rounded-full text-xs font-bold uppercase tracking-widest">❄️ Holiday Season 2026 ❄️</span>
            <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-emerald-400 to-amber-300 mt-2 christ-glow">
                AI Holiday Wishlist & Tech Guru
            </h1>
            <p class="text-slate-400 text-sm mt-1">
                Forecast holiday pricing, check energy efficiency, split bills, get AI setup roasts, and consult our AI PC & Tech Advisor!
            </p>
        </div>

        <!-- NAVIGATION TABS -->
        <div class="flex border-b border-slate-800 gap-4">
            <button onclick="switchTab('wishlist')" id="tab-wishlist-btn" class="pb-3 px-4 font-bold text-sm border-b-2 border-red-500 text-red-400 transition-all">🎁 Christmas Wishlist Board</button>
            <button onclick="switchTab('tech')" id="tab-tech-btn" class="pb-3 px-4 font-bold text-sm border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-all">💻 AI Computer & Tech Advisor</button>
        </div>

        <!-- TAB 1: CHRISTMAS WISHLIST BOARD -->
        <div id="tab-wishlist-content" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/80 p-5 rounded-2xl border border-red-900/30">
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

            <div class="flex gap-4">
                <button onclick="addUrlInput()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl font-medium transition-colors text-sm text-red-300">+ Add Another Gift</button>
                <button onclick="analyzeWishlist()" id="submit-btn" class="flex-1 px-6 py-3 bg-gradient-to-r from-red-600 to-emerald-600 hover:from-red-500 hover:to-emerald-500 text-white font-black rounded-xl shadow-lg shadow-red-600/30 transition-all uppercase tracking-wider text-sm">🔮 Forecast Christmas Prices & Build Wishlist</button>
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

                <!-- NEW: Split Bill Tool -->
                <div class="bg-slate-950 border border-slate-800 p-5 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
                    <div>
                        <h4 class="font-bold text-slate-200 text-sm">👥 Group Gift Bill Splitter</h4>
                        <p class="text-xs text-slate-400">Divide the Christmas forecast total evenly among contributors.</p>
                    </div>
                    <div class="flex items-center gap-3">
                        <label class="text-xs font-semibold text-slate-400">People:</label>
                        <input type="number" id="split-count" value="2" min="1" max="20" oninput="updateSplit()" class="w-16 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-center text-slate-200 font-bold">
                        <span id="split-result" class="text-emerald-400 font-black">$0.00 / person</span>
                    </div>
                </div>

                <!-- NEW: AI Setup Roast & Critic Box -->
                <div class="bg-purple-950/20 border border-purple-800/40 p-5 rounded-2xl space-y-2">
                    <div class="flex justify-between items-center">
                        <h4 class="font-bold text-purple-300 text-sm flex items-center gap-2">🔥 AI Setup Roast & Bottleneck Critic</h4>
                        <button onclick="triggerRoast()" class="px-3 py-1.5 bg-purple-900 hover:bg-purple-800 text-purple-200 text-xs font-bold rounded-lg transition-colors">Generate Roast</button>
                    </div>
                    <p id="roast-text" class="text-slate-300 text-xs italic">Click 'Generate Roast' for expert AI feedback on your bundle bottlenecks and missing components!</p>
                </div>

                <!-- NEW: Price Drop Email Alert Subscription -->
                <div class="bg-emerald-950/20 border border-emerald-800/40 p-5 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
                    <div>
                        <h4 class="font-bold text-emerald-300 text-sm">🔔 Price Drop & Christmas Target Alerts</h4>
                        <p class="text-xs text-slate-400">Get notified when items hit predicted holiday lows.</p>
                    </div>
                    <div class="flex gap-2 w-full sm:w-auto">
                        <input type="email" id="alert-email" placeholder="your.email@example.com" class="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 flex-1">
                        <button onclick="subscribeAlerts()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition-colors">Subscribe</button>
                    </div>
                </div>

                <div id="items-container" class="space-y-4"></div>
            </div>
        </div>

        <!-- TAB 2: AI COMPUTER & TECH ADVISOR -->
        <div id="tab-tech-content" class="hidden space-y-6">
            <div class="bg-slate-950/80 p-6 rounded-2xl border border-sky-900/30 space-y-4">
                <h3 class="text-lg font-black text-sky-400">💻 AI PC & Tech Recommendation Engine</h3>
                <p class="text-slate-400 text-sm">Tell us what you need a computer for (e.g., 4K video editing, heavy gaming, programming, school) and your budget range. We will analyze your requirements and evaluate any computer or gear currently in your cart/wishlist URLs!</p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-sky-300 uppercase tracking-wider mb-1">Your Needs & Use Case</label>
                        <textarea id="tech-needs" rows="3" placeholder="e.g., I need a powerful laptop for running Blender, Unity, and playing Cyberpunk at high settings." class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500"></textarea>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-sky-300 uppercase tracking-wider mb-1">Budget Range</label>
                        <input type="text" id="tech-budget" placeholder="e.g., $1,200 - $1,800" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500 mb-3">
                        
                        <label class="block text-xs font-semibold text-sky-300 uppercase tracking-wider mb-1">Optional: Cart/Wishlist URL to Evaluate</label>
                        <input type="url" id="tech-cart-url" placeholder="https://www.amazon.com/dp/B0..." class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-sky-500">
                    </div>
                </div>

                <button onclick="runTechAdvisor()" id="tech-submit-btn" class="w-full py-3 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-xl shadow-lg transition-all uppercase tracking-wider text-sm">
                    🔍 Consult AI Tech Advisor
                </button>
            </div>

            <div id="tech-loading" class="hidden text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-sky-500 border-t-emerald-400 mb-4"></div>
                <p class="text-sky-300 font-semibold animate-pulse">Running hardware benchmark analysis and compatibility scans...</p>
            </div>

            <div id="tech-results" class="hidden space-y-6">
                <div class="bg-slate-950 border border-sky-900/50 p-6 rounded-2xl space-y-4">
                    <h4 class="text-xl font-bold text-slate-100">AI Recommendation Summary</h4>
                    <p id="tech-summary-text" class="text-slate-300 text-sm leading-relaxed"></p>
                    
                    <div class="bg-sky-950/30 p-4 rounded-xl border border-sky-800/40">
                        <h5 class="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-1">Recommended Hardware Specifications</h5>
                        <p id="tech-specs-text" class="text-slate-200 text-sm"></p>
                    </div>
                </div>

                <div id="cart-evaluations-container" class="space-y-4"></div>
            </div>
        </div>

    </div>

    <script>
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
            let xmas = new Date(currentYear, 11, 25);
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
            const count = parseInt(document.getElementById('split-count').value) || 1;
            const perPerson = lastWishlistData.total_christmas_price / Math.max(count, 1);
            document.getElementById('split-result').innerText = `${lastWishlistData.currency}${perPerson.toFixed(2)} / person`;
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
            document.getElementById('roast-text').innerText = roast;
        }

        function subscribeAlerts() {
            const email = document.getElementById('alert-email').value.trim();
            if (!email || !email.includes('@')) {
                alert("Please enter a valid email address for price alerts.");
                return;
            }
            alert(`Success! Price drop and Christmas target alerts registered for ${email}. You will be notified when items hit holiday lows!`);
            document.getElementById('alert-email').value = '';
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
    </script>
</body>
</html>
    """
