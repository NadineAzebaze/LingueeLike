# backend/app/search/client.py

from opensearchpy import OpenSearch
from app.core.config import settings

_client: OpenSearch | None = None


def get_opensearch_client() -> OpenSearch:
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[{"host": settings.OPENSEARCH_HOST, "port": settings.OPENSEARCH_PORT}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            timeout=30,
        )
    return _client
