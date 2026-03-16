# backend/app/search/index.py

from app.search.client import get_opensearch_client
from app.core.config import settings

INDEX_NAME = settings.OPENSEARCH_INDEX

# Each document represents one aligned pair (source sentence + translation).
# Language-specific analyzers improve recall via stemming and stopword handling.
INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "normalizer": {
                "lowercase_ascii": {
                    "type": "custom",
                    "filter": ["lowercase", "asciifolding"]
                }
            },
            "analyzer": {
                "english_custom": {"type": "english"},
                "french_custom":  {"type": "french"}
            }
        }
    },
    "mappings": {
        "properties": {
            "pair_id":       {"type": "integer"},
            "book_id":       {"type": "integer"},
            "position":      {"type": "integer"},
            "segment_id_en": {"type": "integer"},
            "segment_id_fr": {"type": "integer"},

            # English side
            "text_en": {
                "type": "text",
                "analyzer": "english_custom",
                "fields": {
                    "normalized": {
                        "type": "keyword",
                        "normalizer": "lowercase_ascii"
                    }
                }
            },

            # French side
            "text_fr": {
                "type": "text",
                "analyzer": "french_custom",
                "fields": {
                    "normalized": {
                        "type": "keyword",
                        "normalizer": "lowercase_ascii"
                    }
                }
            }
        }
    }
}


def create_index(client=None):
    client = client or get_opensearch_client()
    client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING, ignore=400)
    print(f"Created index '{INDEX_NAME}'")


def delete_index(client=None):
    client = client or get_opensearch_client()
    client.indices.delete(index=INDEX_NAME, ignore=404)
    print(f"Deleted index '{INDEX_NAME}'")
