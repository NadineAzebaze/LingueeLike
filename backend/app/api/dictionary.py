# backend/app/api/dictionary.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Segment, Book
from app.nlp.highlighter import lookup_translations, find_highlights_in_text

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def search(q: str = Query(..., min_length=1), lang: str = Query("en"), limit: int = 20, db: Session = Depends(get_db)):
    dialect = db.bind.dialect.name
    q_clean = q.strip()

    results = []

    # --- SQLITE / fallback ---
    if dialect != "postgresql":
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
            segment = db.get(Segment, r["segment_id"])

            # Trouver l'alignement opposé
            if lang == "en":
                alignment = segment.alignments_en[0].segment_fr if segment.alignments_en else None
            else:
                alignment = segment.alignments_fr[0].segment_en if segment.alignments_fr else None

            results.append({
                "segment_id": r["segment_id"],
                "book_id": r["book_id"],
                "book_title": r["book_title"],
                "language": r["language"],
                "text": r["text"],
                "alignment_text": alignment.text if alignment else None,
                "alignment_language": alignment.language if alignment else None,
                "alignment_id": alignment.id if alignment else None,
            })

        # Look up word translations from corpus-based index
        translation_map = lookup_translations(q_clean, lang, db)

        for item in results:
            item["alignment_highlights"] = find_highlights_in_text(
                item["alignment_text"] or "", translation_map
            )

        return {"query": q_clean, "lang": lang, "count": len(results), "results": results}
