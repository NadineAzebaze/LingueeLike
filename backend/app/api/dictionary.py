# backend/app/api/dictionary.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Segment, Book
from app.nlp.highlighter import find_highlights_in_text

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _search_opensearch(q_clean: str, lang: str, limit: int) -> list[int] | None:
    """Query OpenSearch for matching segment IDs. Returns None on failure (triggers SQLite fallback)."""
    try:
        from app.search.client import get_opensearch_client
        from app.core.config import settings

        client = get_opensearch_client()
        text_field = f"text.{lang}"

        body = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase": {text_field: {"query": q_clean, "boost": 2}}},
                        {"match_phrase": {"text": {"query": q_clean}}},
                    ],
                    "minimum_should_match": 1,
                    "filter": {
                        "term": {"language": lang}
                    },
                }
            },
            "_source": ["segment_id"],
        }

        response = client.search(index=settings.OPENSEARCH_INDEX, body=body)
        return [hit["_source"]["segment_id"] for hit in response["hits"]["hits"]]

    except Exception:
        return None


def _build_result(segment, book, lang):
    """Build a result dict from a Segment and its alignment."""
    if lang == "en":
        alignment = segment.alignments_en[0].segment_fr if segment.alignments_en else None
    else:
        alignment = segment.alignments_fr[0].segment_en if segment.alignments_fr else None

    return {
        "segment_id": segment.id,
        "book_id": segment.book_id,
        "book_title": book.title if book else "",
        "language": segment.language,
        "text": segment.text,
        "alignment_text": alignment.text if alignment else None,
        "alignment_language": alignment.language if alignment else None,
        "alignment_id": alignment.id if alignment else None,
    }


@router.get("/search")
def search(q: str = Query(..., min_length=1), lang: str = Query("en"), limit: int = 20, db: Session = Depends(get_db)):
    q_clean = q.strip()
    results = []

    # Try OpenSearch first
    segment_ids = _search_opensearch(q_clean, lang, limit)

    if segment_ids is not None:
        for sid in segment_ids:
            segment = db.get(Segment, sid)
            if not segment:
                continue
            book = db.get(Book, segment.book_id)
            results.append(_build_result(segment, book, lang))
    else:
        # SQLite fallback
        pattern = f"%{q_clean}%"
        stmt = (
            select(Segment.id)
            .join(Book, Book.id == Segment.book_id)
            .where(Segment.language == lang)
            .where(Segment.text.ilike(pattern))
            .limit(limit)
        )
        rows = db.execute(stmt).scalars().all()

        for sid in rows:
            segment = db.get(Segment, sid)
            book = db.get(Book, segment.book_id)
            results.append(_build_result(segment, book, lang))

    # Positional alignment highlighting
    for item in results:
        item["alignment_highlights"] = find_highlights_in_text(
            query=q_clean,
            source_text=item["text"],
            target_text=item["alignment_text"] or "",
            source_lang=lang,
        )

    return {"query": q_clean, "lang": lang, "count": len(results), "results": results}
