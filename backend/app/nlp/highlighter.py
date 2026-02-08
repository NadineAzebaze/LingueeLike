# backend/app/nlp/highlighter.py

from sqlalchemy.orm import Session
from app.db.models import WordTranslation, StemForm
from app.nlp.stemmer import stem, clean_token, is_stop_word, strip_accents


def _char_similarity(a: str, b: str) -> float:
    """Character bigram Jaccard similarity between two strings."""
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0
    bigrams_a = set(a[i:i+2] for i in range(len(a) - 1))
    bigrams_b = set(b[i:i+2] for i in range(len(b) - 1))
    intersection = bigrams_a & bigrams_b
    union = bigrams_a | bigrams_b
    return len(intersection) / len(union) if union else 0.0


def lookup_translations(query: str, source_lang: str, db: Session, top_k: int = 10) -> dict:
    """
    For each content word in query, look up target translations
    from the corpus-based word index.

    Returns ALL candidate surface forms so that find_highlights_in_text
    can pick the best matches in context.

    Returns {query_word: [target_surface_form_1, ...]}.
    """
    target_lang = "fr" if source_lang == "en" else "en"
    result = {}

    for word in query.strip().split():
        cleaned = clean_token(word)
        if not cleaned or len(cleaned) < 2:
            continue
        if is_stop_word(cleaned, source_lang):
            continue

        word_stem = stem(cleaned, source_lang)
        if not word_stem or len(word_stem) < 2:
            continue

        all_translations = (
            db.query(WordTranslation)
            .filter(
                WordTranslation.source_stem == word_stem,
                WordTranslation.source_lang == source_lang,
                WordTranslation.target_lang == target_lang,
            )
            .all()
        )

        if not all_translations:
            continue

        # Sort by Dice score desc, then by character similarity desc (cognate preference)
        source_bare = strip_accents(word_stem)
        all_translations.sort(
            key=lambda t: (t.score, _char_similarity(source_bare, strip_accents(t.target_stem))),
            reverse=True,
        )

        # Keep top_k candidates — context-based filtering happens in find_highlights_in_text
        good = all_translations[:top_k]

        target_surfaces = []
        for t in good:
            forms = (
                db.query(StemForm.surface_form)
                .filter(
                    StemForm.stem == t.target_stem,
                    StemForm.language == target_lang,
                )
                .all()
            )
            for f in forms:
                target_surfaces.append((f[0], t.score, _char_similarity(source_bare, strip_accents(t.target_stem))))
        if target_surfaces:
            result[cleaned] = target_surfaces

    return result


def find_highlights_in_text(alignment_text: str, translation_map: dict, max_highlights: int = 2) -> list:
    """
    Given an alignment sentence and a map of {query_word: [(surface, score, char_sim), ...]},
    find the best matching words in the alignment text.

    Prioritises cognates (high char_sim) and high Dice scores.
    Limits output to max_highlights words to avoid over-highlighting.
    """
    if not alignment_text or not translation_map:
        return []

    # Build lookup: accent-stripped surface → (score, char_sim)
    target_lookup = {}
    for query_word, surfaces in translation_map.items():
        for item in surfaces:
            if isinstance(item, tuple):
                surface, score, char_sim = item
            else:
                surface, score, char_sim = item, 1.0, 0.0
            key = strip_accents(surface.lower())
            # Keep the best score for each surface form
            if key not in target_lookup or (score, char_sim) > target_lookup[key][1:]:
                target_lookup[key] = (surface, score, char_sim)

    # Also add query words themselves as cognate candidates (for proper nouns etc.)
    for query_word in translation_map:
        bare = strip_accents(query_word.lower())
        if bare not in target_lookup:
            target_lookup[bare] = (query_word, 0.5, 1.0)  # high char_sim as cognate

    # Find matches in alignment text and rank them
    candidates = []
    for token in alignment_text.split():
        cleaned = clean_token(token)
        if not cleaned or len(cleaned) < 2:
            continue
        bare = strip_accents(cleaned)
        if bare in target_lookup:
            surface, score, char_sim = target_lookup[bare]
            clean_tok = token.strip(".,;:!?\"\u2019'()[]{}«»")
            if clean_tok:
                # Rank: cognates first (high char_sim), then by Dice score
                candidates.append((clean_tok, char_sim, score))

    # Deduplicate and sort: prefer cognates, then high Dice score
    seen = set()
    unique = []
    for tok, csim, dscore in candidates:
        if tok not in seen:
            seen.add(tok)
            unique.append((tok, csim, dscore))

    unique.sort(key=lambda x: (x[1], x[2]), reverse=True)

    return [tok for tok, _, _ in unique[:max_highlights]]
