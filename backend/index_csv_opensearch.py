import csv
from opensearchpy import OpenSearch

CSV_PATH = "../data/books/aligned_book.csv"
INDEX_NAME = "segments"

BOOK_ID_EN = 1
BOOK_ID_FR = 2

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    timeout=30,
)

def index_csv(csv_path):
    print("Indexation en cours...")

    total = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            pos = i + 1

            seg_id_en = pos * 2 - 1
            seg_id_fr = pos * 2

            text_en = row["en"].strip()
            text_fr = row["fr"].strip()

            # --- EN ---
            doc_en = {
                "segment_id": seg_id_en,
                "book_id": BOOK_ID_EN,
                "position": pos,
                "lang": "en",
                "text": text_en,
                "text_normalized": text_en.lower(),
                "aligned_id": seg_id_fr
            }

            client.index(
                index=INDEX_NAME,
                id=f"en-{seg_id_en}",
                body=doc_en
            )

            # --- FR ---
            doc_fr = {
                "segment_id": seg_id_fr,
                "book_id": BOOK_ID_FR,
                "position": pos,
                "lang": "fr",
                "text": text_fr,
                "text_normalized": text_fr.lower(),
                "aligned_id": seg_id_en
            }

            client.index(
                index=INDEX_NAME,
                id=f"fr-{seg_id_fr}",
                body=doc_fr
            )

            total += 1

            if total % 100 == 0:
                print(f"Indexe {total} paires...")

    print(f"\nIndexation terminee.")
    print(f"Total: {total} paires ({total} EN + {total} FR = {total * 2} documents)")

if __name__ == "__main__":
    index_csv(CSV_PATH)
