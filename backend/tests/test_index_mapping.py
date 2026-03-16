"""Test 5 — Index mapping structure (no I/O, validates schema correctness)."""
import pytest
from app.search.index import INDEX_MAPPING


def test_mapping_has_required_pair_fields():
    props = INDEX_MAPPING["mappings"]["properties"]
    required = {"pair_id", "book_id", "position", "segment_id_en", "segment_id_fr", "text_en", "text_fr"}
    assert required.issubset(props.keys()), f"Missing fields: {required - props.keys()}"


def test_mapping_integer_fields():
    props = INDEX_MAPPING["mappings"]["properties"]
    for field in ("pair_id", "book_id", "position", "segment_id_en", "segment_id_fr"):
        assert props[field]["type"] == "integer", f"{field} should be integer"


def test_mapping_text_fields_have_analyzer():
    props = INDEX_MAPPING["mappings"]["properties"]
    assert props["text_en"]["type"] == "text"
    assert props["text_fr"]["type"] == "text"
    assert "analyzer" in props["text_en"]
    assert "analyzer" in props["text_fr"]


def test_mapping_text_fields_have_normalized_subfield():
    props = INDEX_MAPPING["mappings"]["properties"]
    for lang in ("en", "fr"):
        subfields = props[f"text_{lang}"].get("fields", {})
        assert "normalized" in subfields, f"text_{lang} missing .normalized subfield"
        assert subfields["normalized"]["type"] == "keyword"


def test_mapping_language_analyzers_are_distinct():
    """EN and FR fields must use different language analyzers."""
    props = INDEX_MAPPING["mappings"]["properties"]
    assert props["text_en"]["analyzer"] != props["text_fr"]["analyzer"]


def test_mapping_no_legacy_fields():
    """Old single-segment fields should not exist in the new mapping."""
    props = INDEX_MAPPING["mappings"]["properties"]
    legacy = {"text", "text_normalized", "lang", "aligned_id"}
    overlap = legacy & props.keys()
    assert not overlap, f"Legacy fields still present: {overlap}"


def test_settings_define_lowercase_ascii_normalizer():
    normalizers = INDEX_MAPPING["settings"]["analysis"]["normalizer"]
    assert "lowercase_ascii" in normalizers
    filters = normalizers["lowercase_ascii"]["filter"]
    assert "lowercase" in filters
    assert "asciifolding" in filters
