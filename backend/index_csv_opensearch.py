"""
Re-index the aligned CSV as bilingual pair documents.

Each OpenSearch document stores both the English and French sentence of an
aligned pair so that a single query returns the source sentence AND its
translation without a secondary lookup.

Usage (from backend/):
    python index_csv_opensearch.py [path/to/aligned_book.csv]
"""

import csv
import sys
import os

# Make app importable when run as a top-level script from backend/
sys.path.insert(0, os.path.dirname(__file__))

from opensearchpy import helpers
from app.search.client import get_opensearch_client
from app.search.index import INDEX_NAME, INDEX_MAPPING

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/books/aligned_book.csv")
BOOK_ID = 1


def _recreate_index(client):
    client.indices.delete(index=INDEX_NAME, ignore=404)
    client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
    print(f"Index '{INDEX_NAME}' recréé.")


def _iter_actions(csv_path):
    """Yield one bulk-action dict per aligned pair."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            pos = i + 1
            yield {
                "_index": INDEX_NAME,
                "_id": f"pair-{pos}",
                "_source": {
                    "pair_id":       pos,
                    "book_id":       BOOK_ID,
                    "position":      pos,
                    "segment_id_en": pos * 2 - 1,
                    "segment_id_fr": pos * 2,
                    "text_en":       row["en"].strip(),
                    "text_fr":       row["fr"].strip(),
                },
            }


def index_csv(csv_path):
    client = get_opensearch_client()
    _recreate_index(client)
    print("Indexation en cours...")

    success, errors = helpers.bulk(
        client,
        _iter_actions(csv_path),
        chunk_size=200,
        raise_on_error=False,
    )

    print(f"\nIndexation terminée — {success} paires indexées.")
    if errors:
        print(f"Erreurs : {len(errors)}")
        for err in errors[:5]:
            print(" ", err)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else CSV_PATH
    index_csv(path)
