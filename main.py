import os
import random
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

# Determine base directory
BASE_DIR = Path(__file__).resolve().parent

# Safety checks for directories
os.makedirs(BASE_DIR / "static", exist_ok=True)
os.makedirs(BASE_DIR / "templates" / "templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates setup pointing to the nested directory structure
templates = Jinja2Templates(directory=str(BASE_DIR / "templates" / "templates"))

# Workaround for the Jinja2/Starlette caching bug on Render
templates.env.cache = None

# Models
class ProductRequest(BaseModel):
    url: str

class TechAdvisorRequest(BaseModel):
    needs: Optional[str] = None
    budget: Optional[str] = None
    url: Optional[str] = None
    prompt: Optional[str] = None

# Routes
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/tech-advisor")
async def tech_advisor(payload: TechAdvisorRequest):
    user_query = payload.needs or payload.prompt or "General setup"
    user_budget = payload.budget or "Flexible"
    
    return {
        "success": True,
        "recommendation": f"For your needs ('{user_query}') within a budget of {user_budget}, we recommend prioritizing a balanced CPU, 16GB+ RAM, and a reliable SSD storage configuration!"
    }

@app.get("/api/santa-status")
async def get_santa_status():
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
