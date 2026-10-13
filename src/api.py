from pathlib import Path
import sys
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_service import health_status, query_rag, save_feedback

app = FastAPI(
    title="Customer Support RAG API",
    description="A small API for the customer-support RAG assistant.",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)


class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=5000)
    rating: Literal["positive", "negative"]
    comment: str = Field(default="", max_length=2000)


@app.get("/health")
def health():
    return health_status()


@app.post("/query")
def query(request: QueryRequest):
    try:
        return query_rag(request.question, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # The API returns a clear error while debugging locally. Avoid exposing
        # detailed exception messages in a public production deployment.
        raise HTTPException(status_code=500, detail=f"Query failed: {type(exc).__name__}") from exc


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    try:
        return save_feedback(
            question=request.question,
            answer=request.answer,
            rating=request.rating,
            comment=request.comment,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not save feedback.") from exc
