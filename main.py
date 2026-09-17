from __future__ import annotations

import asyncio
import logging
import random
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from scraper import scrape_amazon_product
from services.ai_service import analyze_product_with_ai, generate_tech_recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Ultimate Holiday Tech & Wishlist Platform")

# Mount static directory for CSS and JS assets
app.mount("/static", StaticFiles(directory="static"), name="static")

class WishlistInput(BaseModel):
    wishlist_name: str
    color_theme: str
    urls: List[HttpUrl]

class TechAdvisorInput(BaseModel):
    user_needs: str
    budget_range: str
    cart_urls: List[HttpUrl] = []

@app.post("/api/analyze-wishlist")
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
        
        analysis = {
            "title": item["title"],
            "original_price": item["original_price"],
            "sale_price": item["sale_price"],
            "currency": item["currency"],
            "weather_suitability": ai_insights["weather_suitability"],
            "compatibility_analysis": ai_insights["compatibility_analysis"],
            "christmas_forecast_price": ai_insights["christmas_forecast_price"],
            "christmas_forecast_reason": ai_insights["christmas_forecast_reason"],
            "eco_efficiency_rating": ai_insights["eco_efficiency_rating"],
            "shipping_deadline_estimate": ai_insights["shipping_deadline_estimate"]
        }
        analyzed_items.append(analysis)
        total_orig += item["original_price"]
        total_sale += item["sale_price"]
        total_xmas += ai_insights["christmas_forecast_price"]

    return {
        "wishlist_name": payload.wishlist_name or "Santa's Ultimate Wishlist",
        "color_theme": payload.color_theme or "festive-red",
        "items": analyzed_items,
        "total_original_price": round(total_orig, 2),
        "total_sale_price": round(total_sale, 2),
        "total_christmas_price": round(total_xmas, 2),
        "currency": currency
    }

@app.post("/api/tech-advisor")
async def tech_advisor(payload: TechAdvisorInput):
    cart_items = []
    if payload.cart_urls:
        tasks = [scrape_amazon_product(str(url)) for url in payload.cart_urls]
        cart_items = await asyncio.gather(*tasks)

    result = await generate_tech_recommendations(payload.user_needs, payload.budget_range, cart_items)
    return result

@app.get("/api/santa-status")
async def get_santa_status():
    # List of global cities for Santa to journey through
    cities = [
        {"city": "North Pole", "lat": 90.0, "lon": 0.0, "status": "Preparing sleigh & checking the list"},
        {"city": "Reykjavik, Iceland", "lat": 64.1466, "lon": -21.9426, "status": "Testing reindeer jetpacks"},
        {"city": "London, UK", "lat": 51.5074, "lon": -0.1278, "status": "Dropping off gifts for good kids"},
        {"city": "Cairo, Egypt", "lat": 30.0444, "lon": 31.2357, "status": "Flying over the pyramids"},
        {"city": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503, "status": "Enjoying some local sushi and tea"},
        {"city": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093, "status": "Surfing a quick wave before midnight"},
        {"city": "New York, USA", "lat": 40.7128, "lon": -74.0060, "status": "Navigating skyscrapers"}
    ]
    
    current_stop = random.choice(cities)
    
    return {
        "location": current_stop["city"],
        "coordinates": {"lat": current_stop["lat"], "lon": current_stop["lon"]},
        "status": current_stop["status"],
        "speed_mph": random.randint(1500000, 3000000), # Reindeer speed!
        "presents_delivered": random.randint(2104500000, 2500000000),
        "cookies_eaten": random.randint(840100, 950000)
    }

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()
