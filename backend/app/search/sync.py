# backend/app/search/sync.py

from opensearchpy import helpers
from sqlalchemy.orm import Session
from app.db.models import Segment
from app.search.client import get_opensearch_client
from app.search.index import INDEX_NAME, create_index


def _segment_to_doc(seg):
    return {
        "_index": INDEX_NAME,
        "_id": seg.id,
        "_source": {
            "segment_id": seg.id,
            "book_id": seg.book_id,
            "position": seg.position,
            "language": seg.language,
            "text": seg.text,
        },
    }


def index_all_segments(db: Session, batch_size: int = 500):
    """Bulk-index all segments from SQLite into OpenSearch."""
    client = get_opensearch_client()
    create_index(client)

    segments = db.query(Segment).all()
    actions = [_segment_to_doc(seg) for seg in segments]

    success, errors = helpers.bulk(client, actions, chunk_size=batch_size)
    print(f"Indexed {success} segments. Errors: {len(errors)}")
    return success


def index_segments(segments: list):
    """Index a list of newly imported segments."""
    client = get_opensearch_client()
    create_index(client)

    actions = [_segment_to_doc(seg) for seg in segments]
    if actions:
        success, errors = helpers.bulk(client, actions)
        print(f"Indexed {success} new segments. Errors: {len(errors)}")
