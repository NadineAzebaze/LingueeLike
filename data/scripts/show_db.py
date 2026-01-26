# show_tables.py
import sqlite3
conn = sqlite3.connect("backend/linguee_like.db")
print([r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
conn.close()