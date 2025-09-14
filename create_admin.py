import sqlite3

DB_FILE = "app.db"

def ensure_admin():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role, approved) VALUES (?,?,?,1)",
            ("admin", "admin123", "Admin", 1)
        )
        print("Admin user created: username='admin', password='admin123'")
    else:
        print("Admin already exists.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    ensure_admin()
