# backend/app/nlp/highlighter.py

from app.nlp.stemmer import stem, clean_token, is_stop_word, strip_accents


# Common adjectives that often have word order differences between EN and FR
COMMON_ADJECTIVES_EN = {
    'important', 'good', 'bad', 'big', 'small', 'great', 'new', 'old', 'first', 'last',
    'best', 'worst', 'high', 'low', 'long', 'short', 'young', 'old', 'early', 'late',
    'different', 'same', 'other', 'such', 'own', 'certain', 'little', 'few', 'several',
    'much', 'many', 'more', 'most', 'less', 'least', 'next', 'previous', 'following'
}

COMMON_ADJECTIVES_FR = {
    'important', 'bon', 'mauvais', 'grand', 'petit', 'nouveau', 'vieux', 'premier', 'dernier',
    'meilleur', 'pire', 'haut', 'bas', 'long', 'court', 'jeune', 'tot', 'tard',
    'different', 'meme', 'autre', 'tel', 'propre', 'certain', 'peu', 'plusieurs',
    'beaucoup', 'plus', 'moins', 'prochain', 'precedent', 'suivant'
}


def _is_likely_adjective(word, lang):
    """Check if a word is likely an adjective based on common adjective lists."""
    word_lower = word.lower()
    word_bare = strip_accents(word_lower)
    if lang == 'en':
        return word_bare in COMMON_ADJECTIVES_EN
    else:
        return word_bare in COMMON_ADJECTIVES_FR


def _char_similarity(a: str, b: str) -> float:
    """Character bigram Jaccard similarity between two strings."""
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0
    bigrams_a = set(a[i:i+2] for i in range(len(a) - 1))
    bigrams_b = set(b[i:i+2] for i in range(len(b) - 1))
    intersection = bigrams_a & bigrams_b
    union = bigrams_a | bigrams_b
    return len(intersection) / len(union) if union else 0.0


def find_highlights_in_text(query, source_text, target_text, source_lang, translation_hints=None):
    """
    Find the translation in target_text using phrase-aware positional alignment.

    For single words: checks translation_hints (from WordTranslation DB) first, then
    falls back to word-level positional alignment.
    For phrases: maps the phrase span from source to target and highlights all content words.
    translation_hints: list of surface forms that are known translations of the query.
    """
    if not target_text or not source_text:
        return []

    target_lang = "fr" if source_lang == "en" else "en"

    # Extract content words from query (don't filter stop words - they can be valid search terms)
    query_words = []
    for w in query.strip().split():
        q_clean = clean_token(w)
        if q_clean and len(q_clean) >= 2:
            query_words.append(q_clean)

    if not query_words:
        return []

    source_tokens = source_text.split()
    target_tokens = target_text.split()
    source_len = len(source_tokens)
    target_len = len(target_tokens)

    if source_len == 0 or target_len == 0:
        return []

    # Single word: check DB translation hints first (score-ordered), then positional alignment
    if len(query_words) == 1:
        if translation_hints:
            for hint in translation_hints:
                hint_bare = strip_accents(hint.lower())
                # Skip stop words and very short tokens (len < 4) which are unreliable
                if is_stop_word(hint_bare, target_lang) or len(hint_bare) < 4:
                    continue
                for tok in target_tokens:
                    tok_display = tok.strip(".,;:!?\"'\u2019()[]{}«»")
                    tok_bare = strip_accents(tok_display.lower())
                    # Exact match OR hint is the first part of a hyphenated compound (e.g. "soul" in "soul-winning")
                    if tok_bare == hint_bare or (
                        len(hint_bare) >= 3 and "-" in tok_display and tok_bare.startswith(hint_bare + "-")
                    ):
                        return [tok_display]
        return _find_single_word_highlight(
            query_words[0], source_tokens, target_tokens, source_lang, target_lang
        )

    # Multi-word phrase: use phrase span alignment
    return _find_phrase_span_highlight(
        query_words, source_tokens, target_tokens, source_lang, target_lang
    )


def _find_single_word_highlight(q_clean, source_tokens, target_tokens, source_lang, target_lang):
    """
    Find single word translation using positional alignment.
    Handles word order variations with expanded search for low-confidence matches.
    """
    source_len = len(source_tokens)
    target_len = len(target_tokens)

    q_bare = strip_accents(q_clean)
    q_pos = _find_word_position(source_tokens, q_bare, q_clean, source_lang)

    if q_pos < 0:
        return []

    q_relative = q_pos / source_len

    # Pre-compute target candidates (don't filter stop words - they can be valid translations)
    target_candidates = []
    for j, tok in enumerate(target_tokens):
        t_clean = clean_token(tok)
        if not t_clean or len(t_clean) < 2:
            continue
        # Note: NOT filtering stop words here - "must"/"devons" etc. are valid translations
        t_bare = strip_accents(t_clean)
        display = tok.strip(".,;:!?\"'\u2019()[]{}«»")
        if display:
            target_candidates.append((j, t_bare, len(t_clean), display))

    if not target_candidates:
        return []

    # Compute all scores first to determine if this is a cognate or non-cognate translation
    candidate_scores = []
    max_char_sim = 0.0

    for j, t_bare, t_len, display in target_candidates:
        t_relative = j / target_len
        pos_sim = 1.0 - abs(q_relative - t_relative)
        char_sim = _char_similarity(q_bare, t_bare)
        len_ratio = min(len(q_clean), t_len) / max(len(q_clean), t_len)
        candidate_scores.append((j, display, char_sim, pos_sim, len_ratio))
        max_char_sim = max(max_char_sim, char_sim)

    # Adaptive weighting: if max char_sim < 0.3, this is likely a non-cognate translation
    # Balance position and length to handle word order differences and avoid short stop words
    if max_char_sim < 0.3:
        # Non-cognate: balanced weights favoring position with length as tiebreaker
        char_weight, pos_weight, len_weight = 0.15, 0.70, 0.15
    else:
        # Cognate: favor character similarity
        char_weight, pos_weight, len_weight = 0.5, 0.45, 0.05

    # Find best candidate with adaptive weights
    best_tok = None
    best_score = -1.0
    best_pos_sim = 0.0

    for j, display, char_sim, pos_sim, len_ratio in candidate_scores:
        score = char_weight * char_sim + pos_weight * pos_sim + len_weight * len_ratio
        if score > best_score:
            best_score = score
            best_tok = display
            best_pos_sim = pos_sim

    # Special handling for adjectives and other words prone to word order variation
    is_adjective = _is_likely_adjective(q_clean, source_lang)

    # If this is likely an adjective or if confidence is low, apply relaxed positioning
    if (is_adjective or (best_score < 0.65 and best_pos_sim < 0.75)) and max_char_sim < 0.3:
        # For adjectives, reduce position weight significantly and favor length matching
        # This accommodates EN-FR adjective placement differences
        relaxed_char_weight = 0.15
        relaxed_pos_weight = 0.40  # Much lower for adjectives
        relaxed_len_weight = 0.45  # Much higher for adjectives

        for j, display, char_sim, pos_sim, len_ratio in candidate_scores:
            relaxed_score = (relaxed_char_weight * char_sim +
                           relaxed_pos_weight * pos_sim +
                           relaxed_len_weight * len_ratio)

            # For adjectives, accept if within 10% of best score
            # For non-adjectives, accept if within 5% of best score
            threshold = 0.90 if is_adjective else 0.95

            if relaxed_score > best_score * threshold:
                best_score = relaxed_score
                best_tok = display

    return [best_tok] if best_tok else []


def _find_phrase_span_highlight(query_words, source_tokens, target_tokens, source_lang, target_lang):
    """
    Find phrase translation by mapping the source phrase span to target span.
    Uses a wider window to accommodate word order differences between languages.
    """
    source_len = len(source_tokens)
    target_len = len(target_tokens)

    # Find positions of first and last query words in source
    first_word = query_words[0]
    last_word = query_words[-1]

    first_bare = strip_accents(first_word)
    last_bare = strip_accents(last_word)

    first_pos = _find_word_position(source_tokens, first_bare, first_word, source_lang)
    last_pos = _find_word_position(source_tokens, last_bare, last_word, source_lang)

    if first_pos < 0 or last_pos < 0:
        return []

    # Ensure correct order
    if first_pos > last_pos:
        first_pos, last_pos = last_pos, first_pos

    # Map source span to target span using relative positions
    source_start_rel = first_pos / source_len
    source_end_rel = (last_pos + 1) / source_len  # +1 to include the last word

    # Use wider buffer to accommodate word order differences (adjective placement, etc.)
    # Increase buffer from ±1 to ±2 words to catch reordered content
    buffer_size = 2
    target_start = max(0, int(source_start_rel * target_len) - buffer_size)
    target_end = min(target_len, int(source_end_rel * target_len) + buffer_size)

    # For very short phrases, ensure minimum window size
    min_window = 4  # At least 4 words window
    current_window = target_end - target_start
    if current_window < min_window:
        expansion = (min_window - current_window) // 2
        target_start = max(0, target_start - expansion)
        target_end = min(target_len, target_end + expansion)

    # Score candidates instead of just extracting all words
    # This helps prioritize more likely translations
    candidates = []
    for i in range(target_start, target_end):
        tok = target_tokens[i]
        t_clean = clean_token(tok)
        if not t_clean or len(t_clean) < 2:
            continue

        t_bare = strip_accents(t_clean)
        display = tok.strip(".,;:!?\"'\u2019()[]{}«»")

        if not display:
            continue

        # Calculate relevance score for this candidate
        score = 0.0

        # Check similarity to any query word (helps find reordered translations)
        for q_word in query_words:
            q_bare = strip_accents(q_word)
            char_sim = _char_similarity(q_bare, t_bare)
            score = max(score, char_sim)

        # Position bonus: words near the center of the window score higher
        window_center = (target_start + target_end) / 2
        pos_distance = abs(i - window_center) / max(1, (target_end - target_start) / 2)
        pos_bonus = 1.0 - (pos_distance * 0.3)  # Max 30% penalty for distance
        score = score * pos_bonus

        # Length bonus: prefer longer words (usually more content-ful)
        len_bonus = min(1.0, len(t_clean) / 8.0) * 0.2
        score += len_bonus

        candidates.append((score, display, i))

    # Sort by score and take top candidates
    candidates.sort(reverse=True, key=lambda x: x[0])

    # Extract highlights, avoiding duplicates and filtering by minimum score
    highlights = []
    min_score = 0.15  # Threshold for position-based matching

    for score, display, pos in candidates:
        if score >= min_score and display not in highlights:
            highlights.append(display)

    # Limit to reasonable number of highlights
    # Allow more highlights for longer phrases
    max_highlights = min(len(query_words) * 2 + 2, 8)
    return highlights[:max_highlights]


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

    # Substring match (handles contractions like l'église → église)
    for i, tok in enumerate(tokens):
        tok_bare = strip_accents(clean_token(tok))
        if len(tok_bare) > len(bare_form) and bare_form in tok_bare:
            return i

    return -1
