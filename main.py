from __future__ import annotations
import os
import random
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import your resilient scraper module
from scraper import scrape_amazon_product

app = FastAPI(title="Holiday E-Commerce & Santa Tracker Hub")

# Safety check: Automatically create directories if missing to prevent Render deployment crashes
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static directory for CSS and JavaScript assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup template engine for rendering your frontend
templates = Jinja2Templates(directory="templates")

class ProductRequest(BaseModel):
    url: str

@app.get("/")
async def read_root(request: Request):
    """
    Renders the main e-commerce and tracker dashboard UI.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/scrape")
async def scrape_product(payload: ProductRequest):
    """
    API endpoint that triggers your modular scraper 
    (ScraperAPI with automatic ZenRows fallback).
    """
    result = await scrape_amazon_product(payload.url)
    return result

@app.get("/api/santa-location")
async def get_santa_location():
    """
    Santa Tracker backend endpoint that streams live-simulated location data.
    """
    lat = round(random.uniform(-75.0, 75.0), 4)
    lon = round(random.uniform(-170.0, 170.0), 4)
    speed_mph = round(random.uniform(8500.0, 24000.0), 2)
    presents_delivered = random.randint(1500000000, 5500000000)
    
    return {
        "latitude": lat,
        "longitude": lon,
        "speed_mph": speed_mph,
        "presents_delivered": presents_delivered,
        "status": "In Flight 🎅"
    }
