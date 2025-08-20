from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx

assistant_router = APIRouter()

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

@assistant_router.post("/assistant/ask", response_model=AskResponse)
async def ask_assistant(payload: AskRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured on server")

    # Compose chat request
    url = f"{OPENAI_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are SmartLinks Admin Assistant. Be concise and helpful."},
            {"role": "user", "content": payload.question},
        ],
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code >= 400:
                # Try to surface OpenAI error
                try:
                    err = resp.json()
                except Exception:
                    err = {"error": resp.text}
                raise HTTPException(status_code=502, detail={"message": "OpenAI error", "detail": err})
            data = resp.json()
            answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not answer:
                answer = "(No response received from AI)"
            return AskResponse(answer=answer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant failed: {e}")
