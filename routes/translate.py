from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.ai_service import translate_word
from auth import get_current_user

router = APIRouter()


class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str


@router.post("")
async def translate(request: TranslationRequest, current_user=Depends(get_current_user),):
    try:
        return await translate_word(
            text=request.text,
            source_language=request.source_language,
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
            detail="The translation could not be completed.",
        ) from error