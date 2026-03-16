"""Test 1 — NLP stemmer & utilities (pure logic, no I/O)."""
import pytest
from app.nlp.stemmer import stem, clean_token, is_stop_word, strip_accents, tokenize_and_stem


def test_stem_en_regular():
    assert stem("preaching", "en") == "preach"
    assert stem("running", "en") == "run"
    assert stem("gospels", "en") == "gospel"
    assert stem("salvation", "en") == "salv"   # "salvat-ion" → strips "-ation" → "salv"
    assert stem("quickly", "en") == "quick"


def test_stem_en_irregulars():
    assert stem("lost", "en") == "lose"
    assert stem("found", "en") == "find"
    assert stem("won", "en") == "win"


def test_stem_fr():
    assert stem("perdus", "fr") == "perdu"
    assert stem("gagnant", "fr") == "gagn"
    assert stem("raisons", "fr") == "raison"


def test_clean_token_strips_punctuation():
    assert clean_token("word,") == "word"
    assert clean_token("don't") == "dont"
    assert clean_token("«évangile»") == "évangile"


def test_is_stop_word():
    assert is_stop_word("the", "en") is True
    assert is_stop_word("gospel", "en") is False
    assert is_stop_word("les", "fr") is True
    assert is_stop_word("évangile", "fr") is False


def test_strip_accents():
    assert strip_accents("évangile") == "evangile"
    assert strip_accents("église") == "eglise"
    assert strip_accents("perdu") == "perdu"


def test_tokenize_and_stem_filters_stopwords():
    tokens = tokenize_and_stem("the gospel must be preached", "en")
    stems = [s for s, _ in tokens]
    assert "the" not in stems
    assert "must" not in stems
    assert "gospel" in stems
    assert "preach" in stems
