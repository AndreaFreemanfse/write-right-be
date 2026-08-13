from datetime import datetime

from pydantic import BaseModel, Field


class JournalAnalysisRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    text: str
    native_language: str
    target_language: str


class MistakeResponse(BaseModel):
    original: str
    corrected: str
    original_full: str | None = None
    corrected_full: str | None = None
    loading: bool = False
    explanation: str | None = None
    category: str | None = None
    start: int | None = None
    end: int | None = None


class AccuracyCategories(BaseModel):
    grammar: int = Field(ge=0, le=100)
    vocabulary: int = Field(ge=0, le=100)
    spelling: int = Field(ge=0, le=100)
    sentenceStructure: int = Field(ge=0, le=100)


class AccuracyResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    categories: AccuracyCategories
    improvementNote: str


class BadgeResponse(BaseModel):
    id: int
    key: str
    name: str
    description: str
    icon: str

    model_config = {
        "from_attributes": True,
    }


class UserBadgeResponse(BaseModel):
    id: int
    earned_at: datetime
    badge: BadgeResponse

    model_config = {
        "from_attributes": True,
    }

class JournalAnalysisResponse(BaseModel):
    title: str
    text: str
    mistakes: list[MistakeResponse]
    accuracy: AccuracyResponse
    journal_entry_id: int
    new_badges: list[UserBadgeResponse] = Field(default_factory=list)


class JournalEntryResponse(BaseModel):
    title: str
    id: int
    original_text: str
    corrected_text: str
    mistakes: list[MistakeResponse]
    target_language: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

class JournalEntryUpdate(BaseModel):
    title: str
    original_text: str
    native_language: str
    target_language: str

class FlashcardCreate(BaseModel):
    set_id: int
    front: str
    back: str
    language: str = "German"


class FlashcardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    language: str | None = None
    mastered: bool | None = None


class FlashcardResponse(BaseModel):
    id: int
    set_id: int
    front: str
    back: str
    language: str
    mastered: bool

    model_config = {
        "from_attributes": True,
    }


class FlashcardSetCardCreate(BaseModel):
    front: str
    back: str
    language: str | None = None


class FlashcardSetCreate(BaseModel):
    name: str
    language: str = "German"
    source_type: str
    journal_entry_id: int | None = None
    flashcards: list[FlashcardSetCardCreate] = Field(default_factory=list)


class FlashcardSetUpdate(BaseModel):
    name: str | None = None
    language: str | None = None


class FlashcardSetResponse(BaseModel):
    id: int
    name: str
    language: str
    source_type: str
    journal_entry_id: int | None
    flashcards: list[FlashcardSetCardCreate] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }


class FlashcardSetSaveResponse(BaseModel):
    flashcard_set: FlashcardSetResponse
    created: bool
    added_count: int
    message: str
