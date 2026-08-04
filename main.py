from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from database import Base, engine

from routes import journal, flashcards, flashcard_sets, translate, explanation



# Initialize the FastAPI application instance
app = FastAPI()

Base.metadata.create_all(bind=engine)

# CORS - # Allows React frontend (running on a different URL/port) to safely communicate with this FastAPI backend.
frontend_url = os.getenv("FRONTEND_URL")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://write-right-fe-dad14.vercel.app/"
]

if frontend_url:
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CorrectionRequest(BaseModel):
    text: str


# Include the journal router for handling journal-related endpoints
# journal/analyze endpoint for journal corrections
app.include_router(
    journal.router,
    prefix="/journal",
    tags=["Journal"],
)

app.include_router(
    flashcards.router,
    prefix="/flashcards",
    tags=["Flashcards"],
)

app.include_router(
    flashcard_sets.router,
    prefix="/flashcard-sets",
    tags=["Flashcard Sets"],
)

app.include_router(
    translate.router,
    prefix="/translate",
    tags=["Translation"],
)

app.include_router(
    explanation.router,
    prefix="/explanation",
    tags=["Explanation"],
)


# Defines a root path GET endpoint
@app.get("/")
def read_root():
    return {"status": "success", "message": "FastAPI is initialized!"}

