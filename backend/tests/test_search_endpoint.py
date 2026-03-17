"""Test 4 — FastAPI /search endpoint (mocked OpenSearch + DB)."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.dictionary import get_db


# ---------------------------------------------------------------------------
# DB stub — used only for WordTranslation/StemForm queries (highlighting)
# ---------------------------------------------------------------------------

def _make_db_stub():
    stub = MagicMock()
    stub.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
    stub.execute.return_value.scalars.return_value.all.return_value = []
    return stub


@pytest.fixture
def client():
    db_stub = _make_db_stub()
    app.dependency_overrides[get_db] = lambda: db_stub
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _os_pair_result():
    return [{
        "segment_id":       1,
        "alignment_id":     2,
        "book_id":          1,
        "book_title":       "Thirty-six reasons for winning the lost",
        "text":             "The gospel must be preached.",
        "text_highlighted": "The <mark>gospel</mark> must be preached.",
        "alignment_text":   "L'évangile doit être prêché.",
        "lang":             "en",
        "alignment_lang":   "fr",
    }]


def test_search_returns_200(client):
    with patch("app.api.dictionary._search_opensearch", return_value=_os_pair_result()):
        resp = client.get("/search?q=gospel&lang=en")
    assert resp.status_code == 200


def test_search_response_structure(client):
    with patch("app.api.dictionary._search_opensearch", return_value=_os_pair_result()):
        data = client.get("/search?q=gospel&lang=en").json()

    assert data["query"] == "gospel"
    assert data["lang"] == "en"
    assert data["count"] == 1
    result = data["results"][0]
    assert result["text"] == "The gospel must be preached."
    assert result["alignment_text"] == "L'évangile doit être prêché."
    assert result["alignment_language"] == "fr"
    assert "alignment_highlights" in result


def test_search_missing_query_returns_422(client):
    resp = client.get("/search")
    assert resp.status_code == 422


def test_search_returns_empty_when_opensearch_fails(client):
    """When OpenSearch returns None, the endpoint returns an empty result set."""
    with patch("app.api.dictionary._search_opensearch", return_value=None):
        resp = client.get("/search?q=gospel&lang=en")

    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_search_fr_lang(client):
    fr_result = [{
        "segment_id":       2,
        "alignment_id":     1,
        "book_id":          1,
        "book_title":       "Thirty-six reasons for winning the lost",
        "text":             "L'évangile doit être prêché.",
        "text_highlighted": "L'<mark>évangile</mark> doit être prêché.",
        "alignment_text":   "The gospel must be preached.",
        "lang":             "fr",
        "alignment_lang":   "en",
    }]
    with patch("app.api.dictionary._search_opensearch", return_value=fr_result):
        data = client.get("/search?q=évangile&lang=fr").json()

    assert data["lang"] == "fr"
    result = data["results"][0]
    assert result["language"] == "fr"
    assert result["alignment_language"] == "en"
