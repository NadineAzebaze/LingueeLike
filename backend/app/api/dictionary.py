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


def _search_opensearch(q_clean: str, lang: str, limit: int) -> list[dict] | None:
    """
    Hybrid OpenSearch search: exact phrase match (high boost) + BM25 multi_match (broad recall).
    Results are deduplicated and sorted by score descending.
    """
    try:
        from app.search.client import get_opensearch_client
        from app.core.config import settings

        client = get_opensearch_client()

        book_id = 1 if lang == "en" else 2

        # Hybrid query: phrase match for precision + BM25 for recall
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "text": {
                                    "query": q_clean,
                                    "boost": 4,
                                    "slop": 1
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": q_clean,
                                "fields": ["text^3", "text_normalized"],
                                "type": "best_fields",
                                "operator": "OR",
                                "fuzziness": "AUTO",
                                "minimum_should_match": "60%"
                            }
                        }
                    ],
                    "minimum_should_match": 1,
                    "filter": [
                        {"term": {"lang": lang}},
                        {"term": {"book_id": book_id}}
                    ]
                }
            },
            "size": limit,
            "sort": [
                {"_score": "desc"},
                {"position": "asc"}
            ]
        }

        response = client.search(index=settings.OPENSEARCH_INDEX, body=body)

        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            aligned_id = source.get("aligned_id")

            alignment = None
            if aligned_id:
                aligned_lang = "fr" if lang == "en" else "en"
                aligned_doc_id = f"{aligned_lang}-{aligned_id}"

                try:
                    aligned_response = client.get(
                        index=settings.OPENSEARCH_INDEX,
                        id=aligned_doc_id
                    )
                    alignment = aligned_response["_source"]
                except:
                    alignment = None

            results.append({
                "segment": source,
                "alignment": alignment
            })

        return results

    except Exception:
        return None


def _lookup_translation_hints(query: str, lang: str, db: Session) -> list[str]:
    """
    Look up known translations from the WordTranslation co-occurrence index.
    Returns surface forms of the top translation candidates for each query word,
    excluding stop words which are unreliable translation hints.
    """
    from app.db.models import WordTranslation, StemForm
    from app.nlp.stemmer import stem, clean_token as _clean, is_stop_word

    target_lang = "fr" if lang == "en" else "en"
    hints = []

    for word in query.strip().split():
        w_clean = _clean(word)
        if not w_clean or len(w_clean) < 2:
            continue
        w_stem = stem(w_clean, lang)

        translations = (
            db.query(WordTranslation)
            .filter_by(source_stem=w_stem, source_lang=lang)
            .order_by(WordTranslation.score.desc())
            .limit(5)
            .all()
        )

        for trans in translations:
            if is_stop_word(trans.target_stem, target_lang):
                continue
            surfaces = (
                db.query(StemForm)
                .filter_by(stem=trans.target_stem, language=target_lang)
                .all()
            )
            hints.extend([s.surface_form for s in surfaces])

    return hints


def _build_result(segment, book, lang):
    """SQLite fallback alignment."""
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

    opensearch_results = _search_opensearch(q_clean, lang, limit)

    if opensearch_results is not None:
        for item in opensearch_results:
            segment = item["segment"]
            alignment = item["alignment"]

            result = {
                "segment_id": segment["segment_id"],
                "book_id": segment["book_id"],
                "book_title": "",
                "language": segment["lang"],
                "text": segment["text"],
                "alignment_text": alignment["text"] if alignment else None,
                "alignment_language": alignment["lang"] if alignment else None,
                "alignment_id": alignment["segment_id"] if alignment else None,
            }
            results.append(result)
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

    # Highlighting (with DB translation hints for accuracy)
    translation_hints = _lookup_translation_hints(q_clean, lang, db)
    for item in results:
        item["alignment_highlights"] = find_highlights_in_text(
            query=q_clean,
            source_text=item["text"],
            target_text=item["alignment_text"] or "",
            source_lang=lang,
            translation_hints=translation_hints,
        )

    return {"query": q_clean, "lang": lang, "count": len(results), "results": results}