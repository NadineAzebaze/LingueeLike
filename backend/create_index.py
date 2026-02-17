from opensearchpy import OpenSearch
#quand tu changes le mapping.

INDEX_NAME = "segments"

mapping = {
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
            "text": {"type": "text", "analyzer": "standard"},
            "text_normalized": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "aligned_id": {"type": "integer"}
        }
    }
}

os = OpenSearch("http://localhost:9200")
os.indices.create(index=INDEX_NAME, body=mapping)

print(f"Index '{INDEX_NAME}' créé proprement.")