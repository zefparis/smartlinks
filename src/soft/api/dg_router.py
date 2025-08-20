from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import httpx

router = APIRouter()

SYSTEM_PROMPT = """
Tu es le Directeur Général (CEO) de SmartLinks Autopilot.
Ton rôle:
- Identifier les problèmes (API down, data absente, revenus en chute).
- Optimiser la monétisation (CTR, CR, revenu par pays/device).
- Être borderline: proposer des opportunités agressives de croissance.
- Réponds toujours avec 3 sections:
## Résumé exécutif
## Diagnostic
## Plan d'action (3 étapes max)
"""

class DGRequest(BaseModel):
    question: str
    insights: Dict[str, Any] = {}

class DGResponse(BaseModel):
    answer: str

async def get_ai_response(messages: List[Dict[str, str]]) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured on server"
        )

    url = f"{openai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }
    
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI response: {str(e)}"
        )

@router.post("/dg", response_model=DGResponse)
async def dg_analysis(request: DGRequest):
    try:
        context = f"""Contexte business actuel :\n{request.insights}"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\nQuestion: {request.question}"}
        ]
        
        answer = await get_ai_response(messages)
        return {"answer": answer}
        
    except Exception as e:
        error_msg = f"DG analysis failed: {str(e)}"
        return {
            "answer": (
                "## Erreur d'analyse\n\n"
                "Désolé, une erreur est survenue lors de l'analyse. "
                f"Veuillez réessayer.\n\nDétails: {str(e)}"
            )
        }
