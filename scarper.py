from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse, quote_plus

import aiohttp
from bs4 import BeautifulSoup
from fastapi import HTTPException

logger = logging.getLogger(__name__)
SCRAPING_API_KEY = os.getenv("SCRAPING_API_KEY")

async def scrape_amazon_product(url: str) -> dict:
    target_url = str(url)
    
    if SCRAPING_API_KEY:
        fetch_url = f"https://api.zenrows.com/v1/?apikey={SCRAPING_API_KEY}&url={quote_plus(target_url)}&js_render=true"
    else:
        fetch_url = target_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US, en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(fetch_url, timeout=30) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=502, 
                        detail=f"Failed to fetch page (Status {response.status}). Set SCRAPING_API_KEY in Render environment variables."
                    )
                html = await response.text()
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=f"Timeout while fetching URL: {target_url}")
        except Exception as e:
            logger.error(f"Network error scraping {target_url}: {e}")
            raise HTTPException(status_code=500, detail=f"Network error while fetching URL: {target_url}")

    soup = BeautifulSoup(html, "html.parser")

    title_elem = soup.select_one("#productTitle")
    title = title_elem.get_text(strip=True) if title_elem else None
    
    if not title:
        meta_title = soup.select_one("meta[name='title']")
        if meta_title:
            title = meta_title.get("content", "").strip()
        else:
            title = "Amazon Product (Anti-bot protected)"

    price_str = None
    original_price_str = None

    price_whole = soup.select_one(".priceToPay .a-price-whole")
    price_fraction = soup.select_one(".priceToPay .a-price-fraction")
    if price_whole and price_fraction:
        price_str = f"{price_whole.get_text(strip=True)}{price_fraction.get_text(strip=True)}"

    if not price_str:
        alt_price = soup.select_one(".a-price .a-offscreen")
        if alt_price:
            price_str = alt_price.get_text(strip=True)

    list_price_elem = soup.select_one(".basisPrice .a-offscreen") or soup.select_one("span.priceBlockStrikePriceString")
    if list_price_elem:
        original_price_str = list_price_elem.get_text(strip=True)

    def clean_price(p: Optional[str]) -> float:
        if not p:
            return 0.0
        cleaned = re.sub(r"[^\d.]", "", p)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    sale_val = clean_price(price_str)
    orig_val = clean_price(original_price_str)

    if orig_val == 0.0 or orig_val < sale_val:
        orig_val = sale_val if sale_val > 0.0 else 0.0

    if sale_val == 0.0 and orig_val > 0.0:
        sale_val = orig_val

    currency = "$"
    if price_str and "€" in price_str:
        currency = "€"
    elif price_str and "£" in price_str:
        currency = "£"

    return {
        "title": title,
        "original_price": orig_val,
        "sale_price": sale_val,
        "currency": currency
    }
