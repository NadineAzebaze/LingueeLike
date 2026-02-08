# backend/import_md_runner.py

from app.db.database import SessionLocal
from app.scripts.import_md import import_aligned_csv

db = SessionLocal()

csv_path = "../data/books/aligned_book.csv"

book_en, book_fr, count = import_aligned_csv(
    db=db,
    csv_path=csv_path,
    title="Thirty-six reasons for winning the lost",
    author="Zacharias Tanee Fomum",
    year=2004,
)

print(f"Book EN: {book_en.title} (id={book_en.id})")
print(f"Book FR: {book_fr.title} (id={book_fr.id})")
print(f"Aligned segments imported: {count}")
