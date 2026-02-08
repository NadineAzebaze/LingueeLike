# backend/rebuild_index_runner.py

from app.db.database import SessionLocal
from app.nlp.indexer import build_word_index

db = SessionLocal()
count = build_word_index(db)
print(f"Word translation index rebuilt: {count} entries")
db.close()
