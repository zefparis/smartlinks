from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str

@router.get("/dg")
async def test_dg():
    return {"message": "DG AI is alive"}

@router.post("/dg")
async def ask_dg(request: ChatRequest):
    # For now, just echo the prompt
    return {
        "response": f"Received your message: {request.prompt}",
        "status": "success"
    }
