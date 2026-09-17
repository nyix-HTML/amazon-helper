from __future__ import annotations
import json
import logging
from google import genai
from google.genai import types
from config import client

logger = logging.getLogger(__name__)

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
            config=types.GenerateContentConfig(response_mime_type="application/json")
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

async def generate_tech_recommendations(user_needs: str, budget_range: str, cart_items: list) -> dict:
    prompt = f"""
    User Needs: {user_needs}
    Budget Range: {budget_range}
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
            config=types.GenerateContentConfig(response_mime_type="application/json")
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
