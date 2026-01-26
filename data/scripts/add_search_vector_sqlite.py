# data/scripts/add_search_vector_sqlite.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "backend"))

from sqlalchemy import text, inspect
from app.db import database

def main():
    engine = database.engine
    url = str(engine.url)
    print("Detected database URL:", url)

    if "sqlite" not in url:
        print("This script is intended for SQLite databases. It will not modify Postgres.")
        return

    with engine.connect() as conn:
        insp = inspect(conn)
        tables = insp.get_table_names()
        if "segments" not in tables:
            print("Table 'segments' not found in the database. Nothing to do.")
            return

        cols = [c["name"] for c in insp.get_columns("segments")]
        if "search_vector" in cols:
            print("Column 'search_vector' already exists. Nothing to do.")
            return

        print("Adding column 'search_vector' (TEXT) to table 'segments' ...")
        conn.execute(text('ALTER TABLE segments ADD COLUMN search_vector TEXT;'))
        print("Column added successfully.")

        # show resulting columns
        cols_after = [c["name"] for c in insp.get_columns("segments")]
        print("Columns now:", cols_after)

if __name__ == "__main__":
    main()