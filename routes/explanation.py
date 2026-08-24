from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_service import generate_explanation
import time

router = APIRouter()


class ExplanationRequest(BaseModel):
    original: str
    corrected: str
    native_language: str
    target_language: str


@router.post("")
async def explain(request: ExplanationRequest):
    start_time = time.time()
    try:
        result = await generate_explanation(
            original=request.original,
            corrected=request.corrected,
            native_language=request.native_language,
            target_language=request.target_language,
        )
        print(f"[TIMING] generate_explanation completed in {(time.time() - start_time) * 1000:.2f}ms")
        return result
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