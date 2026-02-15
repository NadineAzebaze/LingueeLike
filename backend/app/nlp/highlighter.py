# backend/app/nlp/highlighter.py

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


def find_highlights_in_text(query, source_text, target_text, source_lang):
    """
    Find the translation of each query word in target_text using
    positional alignment between source_text and target_text.

    Scoring per target word:
      0.5 * char_similarity  (favours cognates)
      0.3 * position_similarity  (words at similar relative positions)
      0.2 * length_similarity  (translations tend to have similar length)
    """
    if not target_text or not source_text:
        return []

    target_lang = "fr" if source_lang == "en" else "en"
    source_tokens = source_text.split()
    target_tokens = target_text.split()
    source_len = len(source_tokens)
    target_len = len(target_tokens)

    if source_len == 0 or target_len == 0:
        return []

    # Pre-compute target candidates (skip stop words and short tokens)
    target_candidates = []
    for j, tok in enumerate(target_tokens):
        t_clean = clean_token(tok)
        if not t_clean or len(t_clean) < 2:
            continue
        if is_stop_word(t_clean, target_lang):
            continue
        t_bare = strip_accents(t_clean)
        display = tok.strip(".,;:!?\"'\u2019()[]{}«»")
        if display:
            target_candidates.append((j, t_bare, len(t_clean), display))

    if not target_candidates:
        return []

    highlights = []

    for qword in query.strip().split():
        q_clean = clean_token(qword)
        if not q_clean or len(q_clean) < 2:
            continue
        if is_stop_word(q_clean, source_lang):
            continue

        q_bare = strip_accents(q_clean)
        q_stem = stem(q_clean, source_lang)

        # Find position of query word in source text
        q_pos = _find_word_position(source_tokens, q_bare, q_clean, source_lang)
        if q_pos < 0:
            continue

        q_relative = q_pos / source_len

        # Score each target candidate
        best_tok = None
        best_score = -1.0

        for j, t_bare, t_len, display in target_candidates:
            t_relative = j / target_len

            pos_sim = 1.0 - abs(q_relative - t_relative)
            char_sim = _char_similarity(q_bare, t_bare)
            len_ratio = min(len(q_clean), t_len) / max(len(q_clean), t_len)

            score = 0.5 * char_sim + 0.3 * pos_sim + 0.2 * len_ratio

            if score > best_score:
                best_score = score
                best_tok = display

        if best_tok and best_tok not in highlights:
            highlights.append(best_tok)

    return highlights


def _find_word_position(tokens, bare_form, cleaned, lang):
    """Find the position of a word in a token list (exact or stemmed match)."""
    q_stem = stem(cleaned, lang)

    # Exact match first (accent-insensitive)
    for i, tok in enumerate(tokens):
        tok_bare = strip_accents(clean_token(tok))
        if tok_bare == bare_form:
            return i

    # Stemmed match
    for i, tok in enumerate(tokens):
        tok_clean = clean_token(tok)
        if tok_clean and stem(tok_clean, lang) == q_stem:
            return i

    return -1
