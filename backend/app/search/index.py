# backend/app/search/index.py

from app.search.client import get_opensearch_client
from app.core.config import settings

INDEX_NAME = settings.OPENSEARCH_INDEX

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "english_custom": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "english_stop", "english_stemmer"],
                },
                "french_custom": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "french_elision", "french_stop", "french_stemmer"],
                },
            },
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "french_stop": {"type": "stop", "stopwords": "_french_"},
                "french_stemmer": {"type": "stemmer", "language": "french"},
                "french_elision": {
                    "type": "elision",
                    "articles_case": True,
                    "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c"],
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "segment_id": {"type": "integer"},
            "book_id": {"type": "integer"},
            "position": {"type": "integer"},
            "language": {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "en": {"type": "text", "analyzer": "english_custom"},
                    "fr": {"type": "text", "analyzer": "french_custom"},
                },
            },
        }
    },
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
