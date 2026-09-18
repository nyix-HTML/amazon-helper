from __future__ import annotations
import os
import random
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from scraper import scrape_amazon_product

app = FastAPI(title="Holiday E-Commerce & Santa Tracker Hub")

BASE_DIR = Path(__file__).resolve().parent

# Safety checks for directories
os.makedirs(BASE_DIR / "static", exist_ok=True)
os.makedirs(BASE_DIR / "templates", exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# Workaround for the Jinja2/Starlette caching bug on Render
templates.env.cache = None

class ProductRequest(BaseModel):
    url: str

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
    
@app.post("/api/scrape")
async def scrape_product(payload: ProductRequest):
    result = await scrape_amazon_product(payload.url)
    return result

@app.get("/api/santa-location")
async def get_santa_location():
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
