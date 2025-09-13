# db_utils.py
import sqlite3
from datetime import datetime

DB_PATH = "users.db"

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------

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
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    # Submissions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            task_id INTEGER,
            source_text TEXT,
            mt_text TEXT,
            user_translation TEXT,
            bleu REAL,
            chrf REAL,
            semantic REAL,
            edits REAL,
            effort REAL,
            fluency INTEGER,
            colloc INTEGER,
            idiom INTEGER,
            submitted_at TEXT
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

    # Student practice assignment
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_practice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            practice_id INTEGER,
            status TEXT,
            assigned_at TEXT,
            completed_at TEXT,
            user_answer TEXT
        )
    """)

    # Insert default user if not exists
    c.execute("INSERT OR IGNORE INTO users VALUES ('student1','pass','Student')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('instructor1','pass','Instructor')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin','Admin')")

    # Insert a default task if not exists
    c.execute("INSERT OR IGNORE INTO tasks (task_id, text) VALUES (1, 'Translate the following paragraph about AI.')")

    conn.commit()
    conn.close()

# -----------------------------
# USER MANAGEMENT
# -----------------------------

def register_user(username, password, role):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def validate_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_user_role(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# -----------------------------
# TASKS
# -----------------------------

def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

# -----------------------------
# SUBMISSIONS
# -----------------------------

def save_submission(username, task_id, source_text, mt_text, user_translation,
                    bleu, chrf, semantic, edits, effort,
                    fluency, colloc, idiom):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO submissions (username, task_id, source_text, mt_text, user_translation,
                                 bleu, chrf, semantic, edits, effort,
                                 fluency, colloc, idiom, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, task_id, source_text, mt_text, user_translation,
          bleu, chrf, semantic, edits, effort,
          fluency, colloc, idiom, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# -----------------------------
# PRACTICE
# -----------------------------

def get_practice_bank():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT practice_id, category, prompt, reference FROM practice")
    items = c.fetchall()
    conn.close()
    return items

def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?, ?, ?)",
              (category, prompt, reference))
    conn.commit()
    conn.close()

def assign_practices_to_user(username, practice_ids):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for pid in practice_ids:
        c.execute("""
            INSERT INTO student_practice (username, practice_id, status, assigned_at)
            VALUES (?, ?, 'recommended', ?)
        """, (username, pid, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT sp.id, sp.practice_id, p.category, p.prompt, p.reference, sp.status, sp.assigned_at, sp.completed_at
        FROM student_practice sp
        JOIN practice p ON sp.practice_id = p.practice_id
        WHERE sp.username=?
    """, (username,))
    items = c.fetchall()
    conn.close()
    return items

def mark_practice_completed(sp_id, answer, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE student_practice
        SET status='completed', completed_at=?, user_answer=?
        WHERE id=? AND username=?
    """, (datetime.now().isoformat(), answer, sp_id, username))
    conn.commit()
    conn.close()
