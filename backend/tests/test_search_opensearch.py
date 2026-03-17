"""Test 3 — _search_opensearch: verifies the pair-based query logic (mocked client).

Now that get_opensearch_client and settings are module-level imports in
app.api.dictionary, we patch them there directly.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.api.dictionary import _search_opensearch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hit(pair_id, text_en, text_fr, seg_en=None, seg_fr=None):
    return {
        "_score": 1.0,
        "_source": {
            "pair_id":       pair_id,
            "book_id":       1,
            "book_title":    "Thirty-six reasons for winning the lost",
            "position":      pair_id,
            "segment_id_en": seg_en or pair_id * 2 - 1,
            "segment_id_fr": seg_fr or pair_id * 2,
            "text_en":       text_en,
            "text_fr":       text_fr,
        },
    }


def _os_response(*hits):
    return {"hits": {"hits": list(hits)}}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_returns_list_of_dicts_on_success():
    """Each hit becomes a flat dict with both source and alignment texts."""
    hit = _make_hit(1, "The gospel must be preached.", "L'évangile doit être prêché.")
    mock_client = MagicMock()
    mock_client.search.return_value = _os_response(hit)

    with patch("app.api.dictionary.get_opensearch_client", return_value=mock_client), \
         patch("app.api.dictionary.settings") as mock_settings:
        mock_settings.OPENSEARCH_INDEX = "segments"
        results = _search_opensearch("gospel", "en", 10)

    assert results is not None
    assert len(results) == 1
    r = results[0]
    assert r["text"] == "The gospel must be preached."
    assert r["alignment_text"] == "L'évangile doit être prêché."
    assert r["lang"] == "en"
    assert r["alignment_lang"] == "fr"


def test_searches_correct_field_for_lang_en():
    """Query body must target text_en when lang='en'."""
    mock_client = MagicMock()
    mock_client.search.return_value = _os_response()

    with patch("app.api.dictionary.get_opensearch_client", return_value=mock_client), \
         patch("app.api.dictionary.settings") as mock_settings:
        mock_settings.OPENSEARCH_INDEX = "segments"
        _search_opensearch("gospel", "en", 5)

    body = mock_client.search.call_args[1]["body"]
    should = body["query"]["bool"]["should"]

    phrase_field = list(should[0]["match_phrase"].keys())[0]
    assert phrase_field == "text_en"
    assert any("text_en" in f for f in should[1]["multi_match"]["fields"])


def test_searches_correct_field_for_lang_fr():
    """Query body must target text_fr when lang='fr'."""
    mock_client = MagicMock()
    mock_client.search.return_value = _os_response()

    with patch("app.api.dictionary.get_opensearch_client", return_value=mock_client), \
         patch("app.api.dictionary.settings") as mock_settings:
        mock_settings.OPENSEARCH_INDEX = "segments"
        _search_opensearch("perdus", "fr", 5)

    body = mock_client.search.call_args[1]["body"]
    phrase_field = list(body["query"]["bool"]["should"][0]["match_phrase"].keys())[0]
    assert phrase_field == "text_fr"


def test_no_secondary_get_call():
    """With pair documents, client.get() must never be called."""
    hit = _make_hit(1, "The gospel.", "L'évangile.")
    mock_client = MagicMock()
    mock_client.search.return_value = _os_response(hit)

    with patch("app.api.dictionary.get_opensearch_client", return_value=mock_client), \
         patch("app.api.dictionary.settings") as mock_settings:
        mock_settings.OPENSEARCH_INDEX = "segments"
        _search_opensearch("gospel", "en", 5)

    mock_client.get.assert_not_called()


def test_returns_none_on_exception():
    """If OpenSearch raises, the function returns None."""
    mock_client = MagicMock()
    mock_client.search.side_effect = ConnectionError("OpenSearch unavailable")

    with patch("app.api.dictionary.get_opensearch_client", return_value=mock_client), \
         patch("app.api.dictionary.settings") as mock_settings:
        mock_settings.OPENSEARCH_INDEX = "segments"
        result = _search_opensearch("gospel", "en", 5)

    assert result is None
