from app.db.database import SessionLocal
from app.scripts.import_tmx import import_tmx

db = SessionLocal()
import_tmx("data/tmx/test.tmx", db)
db.close()