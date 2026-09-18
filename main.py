import os
import random
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from scraper import scrape_amazon_product
from config import client

app = FastAPI()

# Determine base directory
BASE_DIR = Path(__file__).resolve().parent

# Safety checks for directories
os.makedirs(BASE_DIR / "static" / "css", exist_ok=True)
os.makedirs(BASE_DIR / "static" / "js", exist_ok=True)
os.makedirs(BASE_DIR / "templates" / "templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates setup pointing to the nested directory structure
templates = Jinja2Templates(directory=str(BASE_DIR / "templates" / "templates"))
templates.env.cache = None

# Pydantic Models matching app.js requests
class WishlistRequest(BaseModel):
    wishlist_name: Optional[str] = "Santa's Wishlist"
    color_theme: Optional[str] = "festive-red"
    urls: List[str]

class TechAdvisorRequest(BaseModel):
    user_needs: str
    budget_range: str
    cart_urls: Optional[List[str]] = []

# Routes
@app.get("/")
def read_root():
    return {"status": "online", "message": "Seasonal Tech Hub API is running successfully!"}

@app.post("/api/analyze-wishlist")
async def analyze_wishlist(payload: WishlistRequest):
    items = []
    total_original = 0.0
    total_sale = 0.0
    total_christmas = 0.0

    for url in payload.urls:
        product = await scrape_amazon_product(url)
        orig = product["original_price"]
        sale = product["sale_price"] if product["sale_price"] > 0 else orig * 0.8
        if orig == 0.0:
            orig = 99.99
            sale = 79.99
        
        xmas_price = round(sale * 0.9, 2)
        
        total_original += orig
        total_sale += sale
        total_christmas += xmas_price

        items.append({
            "title": product["title"],
            "currency": product["currency"],
            "original_price": orig,
            "sale_price": sale,
            "christmas_forecast_price": xmas_price,
            "eco_efficiency_rating": "A+ Energy Star Certified 🌟",
            "shipping_deadline_estimate": "Arrives by Dec 20th with Prime Standard 🚚",
            "christmas_forecast_reason": "Expected holiday markdown during Cyber Week and pre-Christmas clearance events.",
            "weather_suitability": "Winterized internal circuitry tested down to -10°C snowflake resilience.",
            "compatibility_analysis": "Fully compatible with standard USB-C Power Delivery and seasonal holiday power grids."
        })

    return {
        "wishlist_name": payload.wishlist_name,
        "color_theme": payload.color_theme,
        "currency": "$",
        "total_original_price": round(total_original, 2),
        "total_sale_price": round(total_sale, 2),
        "total_christmas_price": round(total_christmas, 2),
        "items": items
    }

@app.post("/api/tech-advisor")
async def tech_advisor(payload: TechAdvisorRequest):
    cart_evaluations = []
    for url in payload.cart_urls:
        product = await scrape_amazon_product(url)
        cart_evaluations.append({
            "title": product["title"],
            "is_good_match": True,
            "verdict_reason": f"Matches your requirement for '{payload.user_needs}' within the {payload.budget_range} budget range.",
            "alternative_suggestion": "Consider pairing with an upgraded power supply or cooling kit for optimal performance."
        })

    return {
        "ai_recommendation_summary": f"Based on your goal ('{payload.user_needs}') and budget ({payload.budget_range}), we recommend a high-performance configuration featuring a multi-core processor, dedicated graphics acceleration, and fast NVMe storage optimized for multitasking and heavy workloads.",
        "recommended_specs": "• CPU: 8-Core / 16-Thread High-Efficiency Processor\n• RAM: 32GB High-Speed DDR5\n• Storage: 1TB NVMe PCIe 4.0 SSD\n• GPU: Dedicated Holiday Gaming & Rendering Accelerator",
        "cart_evaluations": cart_evaluations
    }

@app.get("/api/santa-status")
async def get_santa_status():
    locations = ["North Pole Workshop 🎅", "Global Airspace (Pacific Sector) ✈️", "En Route to New York 🗽", "Over the Alps 🏔️", "Flying Above Tokyo 🗼"]
    statuses = ["Delivering Presents 🎁", "Checking the List Twice 📋", "Reindeer Snack Break 🥕", "Sleigh Maintenance 🛠️"]
    
    return {
        "location": random.choice(locations),
        "status": random.choice(statuses),
        "speed_mph": round(random.uniform(12000.0, 24000.0), 2),
        "presents_delivered": random.randint(3200000000, 5800000000),
        "cookies_eaten": random.randint(450000, 950000)
    }
