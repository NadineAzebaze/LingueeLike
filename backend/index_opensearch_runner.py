# backend/index_opensearch_runner.py
# Usage: python index_opensearch_runner.py

from app.db.database import SessionLocal
from app.search.sync import index_all_segments

db = SessionLocal()
index_all_segments(db)
db.close()
