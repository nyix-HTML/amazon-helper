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

app = FastAPI(title="AI Amazon Bundle & Setup Analyzer")

# Client picks up GEMINI_API_KEY from environment variables automatically
client = genai.Client()

class SetupInput(BaseModel):
    setup_name: str
    color_theme: str
    urls: List[HttpUrl]

class ProductAnalysis(BaseModel):
    title: str
    original_price: float
    sale_price: float
    currency: str
    weather_suitability: str
    compatibility_analysis: str

class SetupSummary(BaseModel):
    setup_name: str
    color_theme: str
    items: List[ProductAnalysis]
    total_original_price: float
    total_sale_price: float
    currency: str

async def analyze_product_with_ai(product_data: dict) -> dict:
    prompt = f"""
    Analyze the following product details extracted from an e-commerce page:
    Title: {product_data['title']}
    Price: {product_data['currency']}{product_data['sale_price']}

    Provide two specific assessments in valid JSON format:
    1. "weather_suitability": Evaluate how weather conditions (e.g., rain, extreme heat, cold, humidity, indoor-only usage) affect this product's performance, durability, or usability. 
    2. "compatibility_analysis": Analyze what other hardware, software, accessories, or specific connection standards this item physically or digitally requires to work properly (e.g., specific cables, platforms, companion devices, sockets). If the item is entirely standalone and requires no supplementary connections, tools, or companion elements, explicitly state "Standalone item; no external dependencies or compatibility requirements."

    Return strictly a JSON object with keys: "weather_suitability" and "compatibility_analysis".
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
            "weather_suitability": result_json.get("weather_suitability", "Analysis unavailable."),
            "compatibility_analysis": result_json.get("compatibility_analysis", "Analysis unavailable.")
        }
    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}")
        return {
            "weather_suitability": "AI evaluation temporarily unavailable.",
            "compatibility_analysis": "AI evaluation temporarily unavailable."
        }

@app.post("/api/analyze-setup", response_model=SetupSummary)
async def analyze_setup(payload: SetupInput):
    if not payload.urls:
        raise HTTPException(status_code=400, detail="At least one URL must be provided.")

    tasks = [scrape_amazon_product(str(url)) for url in payload.urls]
    scraped_results = await asyncio.gather(*tasks)

    analyzed_items = []
    total_orig = 0.0
    total_sale = 0.0
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
            compatibility_analysis=ai_insights["compatibility_analysis"]
        )
        analyzed_items.append(analysis)
        total_orig += item["original_price"]
        total_sale += item["sale_price"]

    return SetupSummary(
        setup_name=payload.setup_name or "My Custom Setup",
        color_theme=payload.color_theme or "blue",
        items=analyzed_items,
        total_original_price=round(total_orig, 2),
        total_sale_price=round(total_sale, 2),
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
    <title>AI Setup & Gear Board Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center py-10 px-4">
    <div class="max-w-4xl w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500 mb-2">
            AI Setup & Gear Board Builder
        </h1>
        <p class="text-slate-400 mb-6">
            Name your setup, pick a theme color, and add your core gear and accessories (Camera, Cage, Mic, Light, Monitor, etc.) to analyze compatibility, weather impact, and total bundle pricing.
        </p>

        <!-- Setup Configuration Panel -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Setup Name</label>
                <input type="text" id="setup-name" placeholder="e.g., Pro Filmmaking Rig" value="Pro Filmmaking Rig" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Board Color Theme</label>
                <select id="color-theme" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                    <option value="blue">Blue Tech</option>
                    <option value="emerald">Emerald Studio</option>
                    <option value="purple">Purple Creative</option>
                    <option value="amber">Amber Warm</option>
                </select>
            </div>
        </div>

        <div class="mb-2 flex justify-between items-center">
            <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider">Gear & Accessory URLs</h3>
            <span class="text-xs text-slate-500">Paste starting item first, followed by accessories</span>
        </div>

        <div id="url-inputs" class="space-y-3 mb-4">
            <div class="flex gap-2">
                <input type="url" placeholder="Camera URL: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-lg hover:bg-rose-900/50 transition-colors">Remove</button>
            </div>
            <div class="flex gap-2">
                <input type="url" placeholder="Cage / Rig URL: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-lg hover:bg-rose-900/50 transition-colors">Remove</button>
            </div>
            <div class="flex gap-2">
                <input type="url" placeholder="Microphone URL: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-lg hover:bg-rose-900/50 transition-colors">Remove</button>
            </div>
        </div>

        <div class="flex gap-4 mb-8">
            <button onclick="addUrlInput()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg font-medium transition-colors text-sm">
                + Add Accessory URL
            </button>
            <button onclick="analyzeSetup()" id="submit-btn" class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition-all">
                Build & Analyze Board
            </button>
        </div>

        <div id="loading" class="hidden text-center py-12">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-4"></div>
            <p class="text-slate-400 animate-pulse">Assembling gear board and running AI insights...</p>
        </div>

        <div id="results" class="hidden space-y-6">
            <!-- Dynamic Setup Board Header -->
            <div id="board-header" class="border p-6 rounded-xl flex flex-col sm:flex-row justify-between items-center gap-4 transition-all">
                <div>
                    <span id="board-badge" class="px-2.5 py-1 text-xs font-bold rounded-full uppercase tracking-wider">Setup Board</span>
                    <h2 id="display-setup-name" class="text-2xl font-black text-slate-100 mt-1">Setup Name</h2>
                    <p class="text-slate-400 text-sm">Combined board pricing breakdown and dependency map.</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-slate-400 line-through" id="summary-orig">Original: $0.00</div>
                    <div class="text-2xl font-black text-emerald-400" id="summary-sale">Setup Total: $0.00</div>
                </div>
            </div>

            <div id="items-container" class="space-y-4"></div>
        </div>
    </div>

    <script>
        const themeStyles = {
            blue: { border: 'border-blue-900/60', bg: 'bg-blue-950/30', badge: 'bg-blue-900 text-blue-200 border border-blue-700' },
            emerald: { border: 'border-emerald-900/60', bg: 'bg-emerald-950/30', badge: 'bg-emerald-900 text-emerald-200 border border-emerald-700' },
            purple: { border: 'border-purple-900/60', bg: 'bg-purple-950/30', badge: 'bg-purple-900 text-purple-200 border border-purple-700' },
            amber: { border: 'border-amber-900/60', bg: 'bg-amber-950/30', badge: 'bg-amber-900 text-amber-200 border border-amber-700' }
        };

        function addUrlInput() {
            const container = document.getElementById('url-inputs');
            const count = container.children.length + 1;
            const div = document.createElement('div');
            div.className = 'flex gap-2';
            div.innerHTML = `
                <input type="url" placeholder="Accessory #${count} URL: https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-lg hover:bg-rose-900/50 transition-colors">Remove</button>
            `;
            container.appendChild(div);
        }

        function removeInput(button) {
            const container = document.getElementById('url-inputs');
            if (container.children.length > 1) {
                button.parentElement.remove();
            } else {
                alert("You must keep at least one URL field.");
            }
        }

        async function analyzeSetup() {
            const setupName = document.getElementById('setup-name').value.trim() || "My Setup Board";
            const colorTheme = document.getElementById('color-theme').value;
            const inputs = document.querySelectorAll('.url-input');
            const urls = Array.from(inputs).map(input => input.value.trim()).filter(val => val.length > 0);

            if (urls.length === 0) {
                alert("Please enter at least one product URL.");
                return;
            }

            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');

            submitBtn.disabled = true;
            loading.classList.remove('hidden');
            results.classList.add('hidden');

            try {
                const response = await fetch('/api/analyze-setup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ setup_name: setupName, color_theme: colorTheme, urls })
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Failed to analyze setup board.");
                }

                const data = await response.json();
                
                // Apply theme styling to board header
                const theme = themeStyles[data.color_theme] || themeStyles.blue;
                const boardHeader = document.getElementById('board-header');
                boardHeader.className = `border ${theme.border} ${theme.bg} p-6 rounded-xl flex flex-col sm:flex-row justify-between items-center gap-4 transition-all`;
                
                const badge = document.getElementById('board-badge');
                badge.className = `px-2.5 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${theme.badge}`;
                badge.innerText = `Setup Board (${data.color_theme.toUpperCase()})`;

                document.getElementById('display-setup-name').innerText = data.setup_name;
                document.getElementById('summary-orig').innerText = `Original Total: ${data.currency}${data.total_original_price.toFixed(2)}`;
                document.getElementById('summary-sale').innerText = `Setup Total: ${data.currency}${data.total_sale_price.toFixed(2)}`;

                const itemsContainer = document.getElementById('items-container');
                itemsContainer.innerHTML = '';

                data.items.forEach((item, index) => {
                    const label = index === 0 ? 'Core Starting Item' : `Accessory #${index}`;
                    const card = document.createElement('div');
                    card.className = 'bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-4';
                    card.innerHTML = `
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                            <div>
                                <span class="text-xs font-mono text-blue-400 bg-blue-950/60 border border-blue-900/50 px-2 py-0.5 rounded mr-2">${label}</span>
                                <h4 class="font-bold text-lg text-slate-100 inline-block mt-1">${item.title}</h4>
                            </div>
                            <div class="text-right">
                                <span class="text-sm text-slate-400 line-through mr-2">${item.currency}${item.original_price.toFixed(2)}</span>
                                <span class="text-xl font-extrabold text-blue-400">${item.currency}${item.sale_price.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-900">
                            <div class="bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                                <h5 class="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Weather Suitability & Impact</h5>
                                <p class="text-slate-300 text-sm leading-relaxed">${item.weather_suitability}</p>
                            </div>
                            <div class="bg-slate-900/50 p-4 rounded-lg border border-slate-800/60">
                                <h5 class="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">Hardware & System Compatibility</h5>
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
