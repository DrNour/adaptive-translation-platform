# db_utils.py
import sqlite3
from datetime import datetime

DB_PATH = "app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
        task_id INTEGER PRIMARY KEY,
        text TEXT
    )
    """)
    # Submissions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_id INTEGER,
        original TEXT,
        mt TEXT,
        post_edit TEXT,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        edits REAL,
        effort REAL,
        fluency REAL,
        collocations REAL,
        idioms REAL,
        submitted_at TEXT
    )
    """)
    # Practice items
    c.execute("""
    CREATE TABLE IF NOT EXISTS practice (
        practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT
    )
    """)
    # Student practice assignments
    c.execute("""
    CREATE TABLE IF NOT EXISTS student_practice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER,
        status TEXT DEFAULT 'recommended',
        assigned_at TEXT,
        completed_at TEXT
    )
    """)
    # Insert default user and task
    c.execute("INSERT OR IGNORE INTO users VALUES ('student1','pass','Student')")
    c.execute("INSERT OR IGNORE INTO tasks (task_id, text) VALUES (1, 'Translate the following paragraph about AI.')")
    conn.commit()
    conn.close()

def register_user(username, password, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?,?)", (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_role(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else None

def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, original, mt, post_edit,
                    bleu, chrf, semantic, edits, effort,
                    fluency, collocations, idioms):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO submissions (username, task_id, original, mt, post_edit,
        bleu, chrf, semantic, edits, effort, fluency, collocations, idioms, submitted_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (username, task_id, original, mt, post_edit,
          bleu, chrf, semantic, edits, effort, fluency, collocations, idioms,
          datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    SELECT sp.id, p.practice_id, p.category, p.prompt, p.reference, sp.status, sp.assigned_at, sp.completed_at
    FROM student_practice sp
    JOIN practice p ON sp.practice_id = p.practice_id
    WHERE sp.username=?
    """, (username,))
    queue = c.fetchall()
    conn.close()
    return queue

def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?,?,?)", (category, prompt, reference))
    conn.commit()
    conn.close()

def mark_practice_completed(sp_id, answer, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE student_practice SET status='completed', completed_at=? WHERE id=?",
              (datetime.now().isoformat(), sp_id))
    conn.commit()
    conn.close()

def get_practice_bank():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM practice")
    items = c.fetchall()
    conn.close()
    return items
