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

# Import the scraping function from your separate scraper file
from scraper import scrape_amazon_product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Amazon Bundle Analyzer")

# Client picks up GEMINI_API_KEY from environment variables automatically
client = genai.Client()

class ProductInput(BaseModel):
    urls: List[HttpUrl]

class ProductAnalysis(BaseModel):
    title: str
    original_price: float
    sale_price: float
    currency: str
    weather_suitability: str
    compatibility_analysis: str

class CartSummary(BaseModel):
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

@app.post("/api/analyze", response_model=CartSummary)
async def analyze_cart(payload: ProductInput):
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

    return CartSummary(
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
    <title>AI Amazon Bundle & Weather Compatibility Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center py-10 px-4">
    <div class="max-w-4xl w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500 mb-2">
            AI Amazon Bundle Analyzer
        </h1>
        <p class="text-slate-400 mb-6">
            Paste Amazon product URLs below to calculate combined totals (with and without sales), analyze weather impact, and discover compatibility requirements.
        </p>

        <div id="url-inputs" class="space-y-3 mb-4">
            <div class="flex gap-2">
                <input type="url" placeholder="https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
                <button onclick="removeInput(this)" class="px-3 py-2 bg-rose-950/50 border border-rose-800/50 text-rose-300 rounded-lg hover:bg-rose-900/50 transition-colors">Remove</button>
            </div>
        </div>

        <div class="flex gap-4 mb-8">
            <button onclick="addUrlInput()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg font-medium transition-colors text-sm">
                + Add Another URL
            </button>
            <button onclick="analyzeCart()" id="submit-btn" class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition-all">
                Analyze Bundle
            </button>
        </div>

        <div id="loading" class="hidden text-center py-12">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-4"></div>
            <p class="text-slate-400 animate-pulse">Scraping pages and running AI analysis...</p>
        </div>

        <div id="results" class="hidden space-y-6">
            <div class="bg-slate-950 border border-slate-800 p-6 rounded-xl flex flex-col sm:flex-row justify-between items-center gap-4">
                <div>
                    <h3 class="text-lg font-bold text-slate-200">Cart Summary</h3>
                    <p class="text-slate-400 text-sm">Combined pricing breakdown for all validated items.</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-slate-400 line-through" id="summary-orig">Original: $0.00</div>
                    <div class="text-2xl font-black text-emerald-400" id="summary-sale">Sale Total: $0.00</div>
                </div>
            </div>

            <div id="items-container" class="space-y-4"></div>
        </div>
    </div>

    <script>
        function addUrlInput() {
            const container = document.getElementById('url-inputs');
            const div = document.createElement('div');
            div.className = 'flex gap-2';
            div.innerHTML = `
                <input type="url" placeholder="https://www.amazon.com/dp/B0..." class="url-input flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors">
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

        async function analyzeCart() {
            const inputs = document.querySelectorAll('.url-input');
            const urls = Array.from(inputs).map(input => input.value.trim()).filter(val => val.length > 0);

            if (urls.length === 0) {
                alert("Please enter at least one valid Amazon URL.");
                return;
            }

            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');

            submitBtn.disabled = true;
            loading.classList.remove('hidden');
            results.classList.add('hidden');

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls })
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Failed to analyze bundle.");
                }

                const data = await response.json();
                
                document.getElementById('summary-orig').innerText = `Original Total: ${data.currency}${data.total_original_price.toFixed(2)}`;
                document.getElementById('summary-sale').innerText = `Sale Total: ${data.currency}${data.total_sale_price.toFixed(2)}`;

                const itemsContainer = document.getElementById('items-container');
                itemsContainer.innerHTML = '';

                data.items.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'bg-slate-950 border border-slate-800 p-6 rounded-xl space-y-4';
                    card.innerHTML = `
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                            <h4 class="font-bold text-lg text-slate-100 flex-1">${item.title}</h4>
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
