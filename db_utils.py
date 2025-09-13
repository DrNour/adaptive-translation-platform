import sqlite3
from datetime import datetime

DB_NAME = "app.db"

# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)

    # Tasks table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    # Submissions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            task_id INTEGER,
            source_text TEXT,
            mt_text TEXT,
            post_edit TEXT,
            bleu REAL,
            chrf REAL,
            semantic REAL,
            edits REAL,
            effort REAL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Practice table
    c.execute("""
        CREATE TABLE IF NOT EXISTS practice (
            practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            prompt TEXT,
            reference TEXT
        )
    """)

    # Student practice
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_practice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            practice_id INTEGER,
            status TEXT DEFAULT 'recommended',
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# USERS
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return bool(result)

def get_user_role(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

# -----------------------------
# TASKS
# -----------------------------
def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, source_text, mt_text, post_edit,
                    bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO submissions
        (username, task_id, source_text, mt_text, post_edit, bleu, chrf, semantic, edits, effort)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, task_id, source_text, mt_text, post_edit, bleu, chrf, semantic, edits, effort))
    conn.commit()
    conn.close()

# -----------------------------
# PRACTICE
# -----------------------------
def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?, ?, ?)",
              (category, prompt, reference))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT sp.id, p.practice_id, p.category, p.prompt, p.reference, sp.status,
               sp.assigned_at, sp.completed_at
        FROM student_practice sp
        JOIN practice p ON sp.practice_id = p.practice_id
        WHERE sp.username=?
    """, (username,))
    queue = c.fetchall()
    conn.close()
    return queue

def assign_practice_for_student(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT practice_id FROM practice")
    all_practices = [row[0] for row in c.fetchall()]
    c.execute("SELECT practice_id FROM student_practice WHERE username=?", (username,))
    assigned = [row[0] for row in c.fetchall()]
    for pid in all_practices:
        if pid not in assigned:
            c.execute("INSERT INTO student_practice (username, practice_id) VALUES (?, ?)",
                      (username, pid))
    conn.commit()
    conn.close()

def mark_practice_completed(sp_id, answer, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE student_practice
        SET status='completed',
            completed_at=?
        WHERE id=? AND username=?
    """, (datetime.now(), sp_id, username))
    conn.commit()
    conn.close()
