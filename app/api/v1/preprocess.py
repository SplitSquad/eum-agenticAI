# app/api/v1/preprocess.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from app.core.preprocess import translate_query

router = APIRouter(prefix="/preprocess", tags=["Preprocess"])

@router.get("/ping")
def ping():
    return {"message": "pong"}

class PreprocessRequest(BaseModel):
    uid: str
    query: str

@router.post("/translate")
async def preprocess_translate(payload: PreprocessRequest) -> Dict:
    translated = await translate_query(payload.query)
    return {
        "response": "translated",
        "data": translated
    }
# 추가적인 전처리 기능이 필요하다면 여기에 추가
