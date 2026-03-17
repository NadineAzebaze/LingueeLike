# backend/app/scripts/import_md.py

import csv
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Book, Segment, Alignment


def import_aligned_csv(
    db: Session,
    csv_path: str,
    title: str,
    author: str = None,
    year: int = None,
):
    """
    Import a pre-segmented and aligned CSV file into the database.

    Expected CSV format (comma-separated, UTF-8):
        en,fr
        "Hello world.","Bonjour le monde."
        "How are you?","Comment allez-vous ?"
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Read aligned pairs from CSV
    pairs = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            en_text = row["en"].strip()
            fr_text = row["fr"].strip()
            if en_text and fr_text:
                pairs.append((en_text, fr_text))

    if not pairs:
        raise ValueError(f"No aligned pairs found in {csv_path}")

    # Create Book EN
    book_en = Book(
        title=f"{title} (EN)",
        author=author,
        year=year,
        language="en",
        source=csv_path,
    )
    db.add(book_en)

    # Create Book FR
    book_fr = Book(
        title=f"{title} (FR)",
        author=author,
        year=year,
        language="fr",
        source=csv_path,
    )
    db.add(book_fr)
    db.commit()
    db.refresh(book_en)
    db.refresh(book_fr)

    # Create segments and alignments
    new_segments = []
    for i, (en_text, fr_text) in enumerate(pairs, start=1):
        seg_en = Segment(
            book_id=book_en.id,
            position=i,
            language="en",
            text=en_text,
        )
        seg_fr = Segment(
            book_id=book_fr.id,
            position=i,
            language="fr",
            text=fr_text,
        )
        db.add(seg_en)
        db.add(seg_fr)
        db.flush()  # get IDs before creating alignment
        new_segments.extend([seg_en, seg_fr])

        alignment = Alignment(
            segment_en_id=seg_en.id,
            segment_fr_id=seg_fr.id,
            confidence=1.0,
        )
        db.add(alignment)

    db.commit()

    # Rebuild word translation index from corpus
    from app.nlp.indexer import build_word_index
    index_count = build_word_index(db)
    print(f"Word translation index rebuilt: {index_count} entries")

    return book_en, book_fr, len(pairs)


if __name__ == "__main__":
    from pathlib import Path
    from app.db.database import SessionLocal

    db = SessionLocal()
    csv_path = Path(__file__).parents[3] / "data" / "books" / "aligned_book.csv"

    book_en, book_fr, count = import_aligned_csv(
        db=db,
        csv_path=str(csv_path),
        title="Thirty-six reasons for winning the lost",
        author="Zacharias Tanee Fomum",
        year=2004,
    )
    print(f"Book EN: {book_en.title} (id={book_en.id})")
    print(f"Book FR: {book_fr.title} (id={book_fr.id})")
    print(f"Aligned segments imported: {count}")
