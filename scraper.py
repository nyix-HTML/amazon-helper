from __future__ import annotations
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Replace or configure your environment variables for both APIs
SCRAPERAPI_KEY = "YOUR_SCRAPERAPI_KEY"
ZENROWS_API_KEY = "YOUR_ZENROWS_API_KEY"

async def scrape_amazon_product(url: str) -> dict:
    """
    Scrapes an Amazon product page, trying ScraperAPI first. 
    If a block or CAPTCHA is detected, it falls back to ZenRows.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    html_content = None
    
    # ----------------------------------------------------
    # ATTEMPT 1: ScraperAPI
    # ----------------------------------------------------
    try:
        scraperapi_url = "https://api.scraperapi.com"
        params = {
            "api_key": SCRAPERAPI_KEY,
            "url": str(url),
            "render": "true"
        }
        
        logger.info(f"Attempting to scrape via ScraperAPI: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(scraperapi_url, params=params, headers=headers)
            
            # Check for HTTP errors or common anti-bot CAPTCHA markers in text
            if response.status_code == 200:
                content = response.text
                if "captcha" not in content.lower() and "api-services-support@amazon.com" not in content.lower():
                    html_content = content
                    logger.info("ScraperAPI request successful.")
                else:
                    logger.warning("ScraperAPI hit an Amazon CAPTCHA block page. Triggering fallback...")
            else:
                logger.warning(f"ScraperAPI returned status code {response.status_code}. Triggering fallback...")
                
    except Exception as e:
        logger.error(f"ScraperAPI request failed with exception: {e}. Triggering fallback...")

    # ----------------------------------------------------
    # ATTEMPT 2: ZenRows Fallback (if ScraperAPI failed or blocked)
    # ----------------------------------------------------
    if not html_content:
        try:
            zenrows_url = "https://api.zenrows.com/v1/"
            params = {
                "apikey": ZENROWS_API_KEY,
                "url": str(url),
                "mode": "auto",           # Automatically handles JS rendering and stealth features
                "premium_proxy": "true"   # Uses high-grade ISP proxies for tough blocks
            }
            
            logger.info(f"Falling back to ZenRows for URL: {url}")
            async with httpx.AsyncClient(timeout=40.0) as client:
                response = await client.get(zenrows_url, params=params)
                
                if response.status_code == 200:
                    html_content = response.text
                    logger.info("ZenRows fallback request successful.")
                else:
                    logger.error(f"ZenRows fallback also failed with status code {response.status_code}.")
                    
        except Exception as e:
            logger.error(f"ZenRows fallback request failed with exception: {e}")

    # ----------------------------------------------------
    # FALLBACK DATA PARSING (BeautifulSoup)
    # ----------------------------------------------------
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract title safely
        title_elem = soup.select_one("#productTitle") or soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"
        
        # Extract price safely (checking various Amazon price element patterns)
        price_elem = (
            soup.select_one(".a-price-whole") or 
            soup.select_one("#priceblock_ourprice") or 
            soup.select_one("#corePrice_desktop .a-offscreen")
        )
        
        sale_price = 0.0  # Set default fallback to 0
        if price_elem:
            try:
                price_text = price_elem.get_text(strip=True).replace("$", "").replace(",", "").split(".")[0]
                sale_price = float(price_text)
            except ValueError:
                pass
                
        # If the sale price is 0, the original price stays 0. Otherwise, mock a 25% discount.
        original_price = round(sale_price * 1.25, 2) if sale_price > 0 else 0.0
        
        return {
            "title": title,
            "original_price": original_price,
            "sale_price": sale_price,
            "currency": "$"
        }

    # Ultimate fallback simulation data if both proxy providers fail completely
    logger.warning("Both scrapers failed to extract live content. Returning zeroed fallback data.")
    return {
        "title": "Product Data Unavailable (Scraping Failed)",
        "original_price": 0.0,
        "sale_price": 0.0,
        "currency": "$"
    }
