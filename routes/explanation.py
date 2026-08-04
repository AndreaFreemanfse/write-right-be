from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_service import generate_explanation


router = APIRouter()


class ExplanationRequest(BaseModel):
    original: str
    corrected: str
    native_language: str
    target_language: str


@router.post("")
async def explain(request: ExplanationRequest):
    try:
        return await generate_explanation(
            original=request.original,
            corrected=request.corrected,
            native_language=request.native_language,
            target_language=request.target_language,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="The explanation generation could not be completed.",
        ) from error