import sqlite3

DB_FILE = "app.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT,
    approved INTEGER DEFAULT 0
)
""")
c.execute("INSERT OR REPLACE INTO users (username, password, role, approved) VALUES (?,?,?,?)",
          ("Nour", "123", "Admin", 1))
conn.commit()
conn.close()

print("✅ Admin created: Nour / 123")
