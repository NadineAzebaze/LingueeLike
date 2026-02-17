# backend/app/search/index.py

from app.search.client import get_opensearch_client
from app.core.config import settings

INDEX_NAME = settings.OPENSEARCH_INDEX

INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "segment_id": {"type": "integer"},
            "book_id": {"type": "integer"},
            "position": {"type": "integer"},
            "lang": {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "standard",
                "search_analyzer": "standard"
            },
            "text_normalized": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
            },
            "aligned_id": {"type": "integer"}
        }
    }
}


def create_index(client=None):
    client = client or get_opensearch_client()
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        print(f"Created index '{INDEX_NAME}'")


def delete_index(client=None):
    client = client or get_opensearch_client()
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
        print(f"Deleted index '{INDEX_NAME}'")
