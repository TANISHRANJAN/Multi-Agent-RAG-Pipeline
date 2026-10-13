from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "knowledge_base_chunks.jsonl"
FAISS_PATH = PROJECT_ROOT / "data" / "vector_store" / "customer_support.faiss"
FEEDBACK_PATH = PROJECT_ROOT / "reports" / "customer_feedback.jsonl"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "google/flan-t5-small"

_chunks: list[dict[str, Any]] | None = None
_embedding_model = None
_faiss_index = None
_bm25_index = None
_tokenizer = None
_generation_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _load_resources() -> None:
    global _chunks, _embedding_model, _faiss_index, _bm25_index
    global _tokenizer, _generation_model

    if _chunks is not None:
        return

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Knowledge-base chunks not found: {CHUNKS_PATH}")
    if not FAISS_PATH.exists():
        raise FileNotFoundError(f"FAISS index not found: {FAISS_PATH}")

    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        _chunks = [json.loads(line) for line in f if line.strip()]

    if not _chunks:
        raise ValueError("Knowledge base contains no chunks.")

    _faiss_index = faiss.read_index(str(FAISS_PATH))
    if _faiss_index.ntotal != len(_chunks):
        raise ValueError(
            f"FAISS index has {_faiss_index.ntotal} vectors but there are {len(_chunks)} chunks."
        )

    _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [str(chunk.get("text", "")) for chunk in _chunks]
    _bm25_index = BM25Okapi([_tokenize(text) for text in texts])

    _tokenizer = AutoTokenizer.from_pretrained(GENERATION_MODEL_NAME)
    _generation_model = AutoModelForSeq2SeqLM.from_pretrained(GENERATION_MODEL_NAME)
    _generation_model = _generation_model.to(_device)
    _generation_model.eval()


def health_status() -> dict[str, Any]:
    return {
        "status": "ok",
        "project": "customer-support-agentic-rag",
        "chunks_file_exists": CHUNKS_PATH.exists(),
        "faiss_index_exists": FAISS_PATH.exists(),
        "models_loaded": _chunks is not None,
    }


def _hybrid_search(query: str, top_k: int = 4, candidate_k: int = 10) -> list[dict[str, Any]]:
    _load_resources()
    assert _chunks is not None and _embedding_model is not None
    assert _faiss_index is not None and _bm25_index is not None

    n = len(_chunks)
    candidate_k = min(max(top_k, candidate_k), n)
    query_vector = _embedding_model.encode(
        [query], convert_to_numpy=True, normalize_embeddings=True
    ).astype("float32")
    semantic_scores, semantic_ids = _faiss_index.search(query_vector, candidate_k)

    token_scores = _bm25_index.get_scores(_tokenize(query))
    keyword_ids = np.argsort(token_scores)[::-1][:candidate_k]

    # Reciprocal Rank Fusion: combine rank positions instead of incomparable raw scores.
    rrf_scores: dict[int, float] = {}
    for rank, idx in enumerate(semantic_ids[0], start=1):
        if idx >= 0:
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (60 + rank)
    for rank, idx in enumerate(keyword_ids, start=1):
        rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (60 + rank)

    ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
    results = []
    for idx in ranked_ids:
        item = dict(_chunks[idx])
        item["rrf_score"] = float(rrf_scores[idx])
        results.append(item)
    return results


def _generate_answer(question: str, retrieved: list[dict[str, Any]]) -> str:
    assert _tokenizer is not None and _generation_model is not None
    if not retrieved:
        return "I could not find relevant information in the available support knowledge base. Please contact customer support."

    evidence_blocks = []
    used_chars = 0
    for item in retrieved:
        title = str(item.get("title", "Support document"))
        chunk_id = str(item.get("chunk_id", "unknown"))
        source = str(item.get("source", "knowledge base"))
        text = str(item.get("text", "")).strip()
        block = f"[{chunk_id}] {title} (source: {source})\n{text}"
        if used_chars + len(block) > 3000:
            break
        evidence_blocks.append(block)
        used_chars += len(block)

    prompt = (
        "Answer the customer question using only the support information below. "
        "If the information does not answer the question, say that you cannot find the answer "
        "in the available information. Do not invent policies.\n\n"
        f"SUPPORT INFORMATION:\n{chr(10).join(evidence_blocks)}\n\n"
        f"CUSTOMER QUESTION: {question}\nANSWER:"
    )
    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(_device)
    with torch.no_grad():
        output_ids = _generation_model.generate(
            **inputs, max_new_tokens=160, do_sample=False
        )
    answer = _tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    return answer or "I could not generate a reliable answer. Please contact customer support."


def query_rag(question: str, top_k: int = 4) -> dict[str, Any]:
    question = str(question).strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    retrieved = _hybrid_search(question, top_k=top_k)
    answer = _generate_answer(question, retrieved)
    sources = [
        {
            "chunk_id": str(item.get("chunk_id", "unknown")),
            "title": str(item.get("title", "Support document")),
            "source": str(item.get("source", "knowledge base")),
            "category": str(item.get("category", "general")),
        }
        for item in retrieved
    ]
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(retrieved),
    }


def save_feedback(question: str, answer: str, rating: str, comment: str = "") -> dict[str, Any]:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "question": str(question).strip(),
        "answer": str(answer).strip(),
        "rating": str(rating).strip(),
        "comment": str(comment).strip(),
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "saved", "feedback_file": str(FEEDBACK_PATH)}
