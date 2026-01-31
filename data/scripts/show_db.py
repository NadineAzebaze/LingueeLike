import sqlite3

conn = sqlite3.connect(r"C:\Users\AZEBAZE Nadine\Documents\linguee_like\backend\linguee_like.db")
rows = conn.execute("SELECT id FROM segments LIMIT 5").fetchall()
print(rows)
conn.close()