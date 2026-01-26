# backend/app/api/dictionary.py
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Segment, Book

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/search")
def search(q: str = Query(..., min_length=1), lang: str = Query("en"), limit: int = 20, db: Session = Depends(get_db)):
    """
    Recherche compatible Postgres (TSVECTOR) et SQLite (LIKE).
    Retourne une liste d'objets { segment_id, book_id, book_title, language, text, score }.
    """
    dialect = db.bind.dialect.name  # 'sqlite' or 'postgresql'
    q_clean = q.strip()

    results = []
    if dialect == "postgresql":
        # Utiliser to_tsquery pour une recherche plus robuste
        # on crée un tsquery simple en remplaçant espaces par & (AND)
        ts_query = " & ".join([part for part in q_clean.split() if part])
        stmt = (
            select(
                Segment.id.label("segment_id"),
                Segment.book_id,
                Book.title.label("book_title"),
                Segment.language,
                Segment.text,
                func.ts_rank_cd(Segment.search_vector, func.to_tsquery(lang if lang in ("en","fr") else "english", ts_query)).label("score")
            )
            .join(Book, Book.id == Segment.book_id)
            .where(Segment.language == lang)
            .where(Segment.search_vector.op('@@')(func.to_tsquery(lang if lang in ("en","fr") else "english", ts_query)))
            .order_by(text("score DESC"))
            .limit(limit)
        )
        rows = db.execute(stmt).mappings().all()
        for r in rows:
            results.append({
                "segment_id": r["segment_id"],
                "book_id": r["book_id"],
                "book_title": r["book_title"],
                "language": r["language"],
                "text": r["text"],
                "score": float(r["score"]) if r["score"] is not None else 0.0
            })
    else:
        # SQLite ou autre : recherche basique avec LIKE (sécurisée via bind params)
        pattern = f"%{q_clean}%"
        stmt = (
            select(
                Segment.id.label("segment_id"),
                Segment.book_id,
                Book.title.label("book_title"),
                Segment.language,
                Segment.text
            )
            .join(Book, Book.id == Segment.book_id)
            .where(Segment.language == lang)
            .where(Segment.text.ilike(pattern))
            .limit(limit)
        )
        rows = db.execute(stmt).mappings().all()
        for r in rows:
            results.append({
                "segment_id": r["segment_id"],
                "book_id": r["book_id"],
                "book_title": r["book_title"],
                "language": r["language"],
                "text": r["text"],
                "score": None
            })

    return {"query": q_clean, "lang": lang, "count": len(results), "results": results}