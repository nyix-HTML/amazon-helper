import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

# Allow your GitHub Pages site (or all origins for easy testing) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your exact GitHub Pages URL e.g. ["https://yourusername.github.io"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Google GenAI client using the environment variable configured in Railway
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class AssistantRequest(BaseModel):
    message: str

@app.post("/api/ai-assistant")
async def ai_assistant(req: AssistantRequest):
    try:
        # Generate content using Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"You are a helpful, cute, and knowledgeable shopping assistant for an e-commerce hub. Answer this user's query: {req.message}"
        )
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "Railway AI Backend is running!"}
