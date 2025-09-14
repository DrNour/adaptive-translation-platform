import sqlite3

conn = sqlite3.connect("app.db")
c = conn.cursor()

# Add admin user (approved immediately)
c.execute("""
INSERT OR REPLACE INTO users (username, password, role, approved) 
VALUES (?, ?, ?, ?)
""", ("admin", "admin123", "Admin", 1))

conn.commit()
conn.close()

print("Admin user added! Login with username='admin', password='admin123'")
