# backend/app/api/dictionary.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import WordTranslation, StemForm
from app.nlp.highlighter import find_highlights_in_text
from app.nlp.stemmer import stem, clean_token as _clean, is_stop_word, other_lang
from app.search.client import get_opensearch_client

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _search_opensearch(q_clean: str, lang: str, limit: int) -> list[dict] | None:
    """
    Hybrid OpenSearch search on bilingual pair documents.

    Each document contains both text_en and text_fr, so the aligned translation
    is retrieved in a single query — no secondary lookup required.

    Strategy: exact phrase match (high boost, slop=1) for precision
              + BM25 multi_match with fuzziness for recall.
    """
    try:
        client = get_opensearch_client()

        tgt_lang = other_lang(lang)
        src_field = f"text_{lang}"

        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                src_field: {
                                    "query": q_clean,
                                    "boost": 4,
                                    "slop": 1
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": q_clean,
                                "fields": [f"{src_field}^3", f"{src_field}.normalized"],
                                "type": "best_fields",
                                "operator": "OR",
                                "fuzziness": "AUTO",
                                "minimum_should_match": "60%"
                            }
                        }
                    ],
                    "minimum_should_match": 1
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
            src = hit["_source"]
            results.append({
                "segment_id":     src.get(f"segment_id_{lang}"),
                "alignment_id":   src.get(f"segment_id_{tgt_lang}"),
                "book_id":        src.get("book_id"),
                "book_title":     src.get("book_title", ""),
                "text":           src.get(src_field, ""),
                "alignment_text": src.get(f"text_{tgt_lang}", ""),
                "lang":           lang,
                "alignment_lang": tgt_lang,
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
    tgt_lang = other_lang(lang)
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
            if is_stop_word(trans.target_stem, tgt_lang):
                continue
            surfaces = (
                db.query(StemForm)
                .filter_by(stem=trans.target_stem, language=tgt_lang)
                .all()
            )
            hints.extend([s.surface_form for s in surfaces])

    return hints


@router.get("/search")
def search(q: str = Query(..., min_length=1), lang: str = Query("en"), limit: int = 20, db: Session = Depends(get_db)):
    q_clean = q.strip()
    results = []

    opensearch_results = _search_opensearch(q_clean, lang, limit)

    for item in (opensearch_results or []):
        results.append({
            "segment_id":         item["segment_id"],
            "book_id":            item["book_id"],
            "book_title":         item["book_title"],
            "language":           item["lang"],
            "text":               item["text"],
            "alignment_text":     item["alignment_text"] or None,
            "alignment_language": item["alignment_lang"],
            "alignment_id":       item["alignment_id"],
        })

    # Skip DB hint lookup when there is nothing to highlight
    if results:
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
