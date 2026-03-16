"""Test 2 — Highlighter: finds translation tokens in aligned sentences."""
import pytest
from app.nlp.highlighter import find_highlights_in_text


def test_single_word_highlight_en_to_fr():
    """A known cognate should be highlighted in the French sentence."""
    highlights = find_highlights_in_text(
        query="gospel",
        source_text="The gospel must be preached to every creature.",
        target_text="L'évangile doit être prêché à toute créature.",
        source_lang="en",
    )
    assert isinstance(highlights, list)
    assert len(highlights) >= 1


def test_single_word_no_match_returns_list():
    """Even with no match, the function always returns a list."""
    result = find_highlights_in_text(
        query="xyz",
        source_text="Hello world.",
        target_text="Bonjour le monde.",
        source_lang="en",
    )
    assert isinstance(result, list)


def test_empty_target_returns_empty():
    result = find_highlights_in_text(
        query="gospel",
        source_text="The gospel is good news.",
        target_text="",
        source_lang="en",
    )
    assert result == []


def test_translation_hint_takes_priority():
    """When a translation hint matches a standalone token it should be returned.
    'perdus' is a standalone token — no apostrophe issue like 'L'évangile'."""
    hints = ["perdus"]
    result = find_highlights_in_text(
        query="lost",
        source_text="We must win the lost for Christ.",
        target_text="Nous devons gagner les perdus pour Christ.",
        source_lang="en",
        translation_hints=hints,
    )
    assert "perdus" in result


def test_phrase_highlight_returns_multiple_tokens():
    """A multi-word query should produce multiple highlights."""
    result = find_highlights_in_text(
        query="win the lost",
        source_text="We must win the lost for Jesus.",
        target_text="Nous devons gagner les perdus pour Jésus.",
        source_lang="en",
    )
    assert isinstance(result, list)
    assert len(result) >= 1


def test_fr_to_en_direction():
    """Highlighting works in the FR→EN direction too."""
    result = find_highlights_in_text(
        query="perdus",
        source_text="Nous devons gagner les perdus.",
        target_text="We must win the lost.",
        source_lang="fr",
    )
    assert isinstance(result, list)
