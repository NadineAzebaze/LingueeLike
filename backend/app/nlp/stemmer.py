# backend/app/nlp/stemmer.py

import re
import unicodedata

STOP_WORDS_EN = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "and", "but", "if", "or", "because", "as",
    "until", "while", "of", "at", "by", "for", "with", "about", "against",
    "between", "through", "during", "before", "after", "above", "below",
    "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "now", "into",
})

STOP_WORDS_FR = frozenset({
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "on",
    "me", "te", "se", "lui", "leur", "y", "en",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses",
    "notre", "votre", "nos", "vos", "leurs",
    "ce", "cet", "cette", "ces", "qui", "que", "qu", "quoi",
    "dont", "ou", "et", "mais", "donc", "or", "ni", "car",
    "ne", "pas", "plus", "jamais", "rien", "aucun",
    "est", "sont", "suis", "sommes", "etes", "etait", "ont", "a",
    "au", "aux", "avec", "dans", "par", "pour", "sur", "sans",
    "sous", "entre", "vers", "chez", "si", "tout", "tous", "toute",
    "toutes", "c", "n", "s", "j",
})

IRREGULAR_EN = {
    "lost": "lose", "found": "find", "said": "say", "came": "come",
    "went": "go", "done": "do", "made": "make", "gave": "give",
    "took": "take", "known": "know", "seen": "see", "been": "be",
    "had": "have", "won": "win", "kept": "keep", "left": "leave",
    "brought": "bring", "thought": "think", "told": "tell",
    "sold": "sell", "bought": "buy", "caught": "catch",
    "taught": "teach", "sought": "seek", "built": "build",
    "sent": "send", "spent": "spend", "felt": "feel", "met": "meet",
    "led": "lead", "read": "read", "wrote": "write", "written": "write",
    "spoke": "speak", "spoken": "speak", "broke": "break", "broken": "break",
    "chose": "choose", "chosen": "choose", "drove": "drive", "driven": "drive",
    "gave": "give", "given": "give", "grew": "grow", "grown": "grow",
    "knew": "know", "ran": "run", "rose": "rise", "risen": "rise",
    "sang": "sing", "sung": "sing", "sat": "sit", "stood": "stand",
    "swam": "swim", "swum": "swim", "wore": "wear", "worn": "wear",
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def clean_token(word: str) -> str:
    return re.sub(r"[^\w]", "", word, flags=re.UNICODE).lower()


def is_stop_word(word: str, lang: str) -> bool:
    bare = strip_accents(word)
    if lang == "en":
        return bare in STOP_WORDS_EN
    return bare in STOP_WORDS_FR


def stem_en(word: str) -> str:
    w = word.lower()
    if w in IRREGULAR_EN:
        return IRREGULAR_EN[w]
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ied") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ing") and len(w) > 5:
        base = w[:-3]
        if len(base) >= 2 and base[-1] == base[-2]:
            return base[:-1]
        return base
    if w.endswith("ation") and len(w) > 6:
        return w[:-5]
    if w.endswith("ness") and len(w) > 5:
        return w[:-4]
    if w.endswith("ment") and len(w) > 5:
        return w[:-4]
    if w.endswith("able") and len(w) > 5:
        return w[:-4]
    if w.endswith("ed") and len(w) > 3:
        base = w[:-2]
        if len(base) >= 2 and base[-1] == base[-2]:
            return base[:-1]
        return base
    if w.endswith("er") and len(w) > 4:
        return w[:-2]
    if w.endswith("ly") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def stem_fr(word: str) -> str:
    w = strip_accents(word.lower())
    for suffix, replacement in [
        ("euses", "eux"), ("euse", "eux"),
        ("aient", ""), ("ions", ""),
        ("ees", "e"), ("es", "e"), ("ee", "e"),
        ("ant", ""), ("ent", ""),
        ("ais", ""), ("ait", ""),
    ]:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[:-len(suffix)] + replacement
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def stem(word: str, lang: str) -> str:
    cleaned = clean_token(word)
    if not cleaned or len(cleaned) < 2:
        return ""
    if lang == "en":
        return stem_en(cleaned)
    return stem_fr(cleaned)


def other_lang(lang: str) -> str:
    """Return the opposite language code: 'en' ↔ 'fr'."""
    return "fr" if lang == "en" else "en"


def tokenize_and_stem(text: str, lang: str) -> list:
    """Tokenize, filter stop words, stem. Returns list of (stem, surface_form)."""
    result = []
    for token in text.split():
        cleaned = clean_token(token)
        if not cleaned or len(cleaned) < 2:
            continue
        if is_stop_word(cleaned, lang):
            continue
        s = stem(cleaned, lang)
        if s and len(s) >= 2:
            result.append((s, cleaned))
    return result
