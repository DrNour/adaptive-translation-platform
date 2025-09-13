import sqlite3
from datetime import datetime

DB_NAME = "app.db"

# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)

    # Tasks
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    """)

    # Submissions
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
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(task_id) REFERENCES tasks(task_id)
        )
    """)

    # Practice Bank
    c.execute("""
        CREATE TABLE IF NOT EXISTS practice (
            practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            prompt TEXT,
            reference TEXT
        )
    """)

    # Student Practice
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_practice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            practice_id INTEGER,
            status TEXT DEFAULT 'recommended',
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(practice_id) REFERENCES practice(practice_id)
        )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# USER MANAGEMENT
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
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# -----------------------------
# TASKS & SUBMISSIONS
# -----------------------------
def get_adaptive_tasks(username):
    # For simplicity, return all tasks
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
# PRACTICE MANAGEMENT
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
    """
    Assign all unassigned practices to a student.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get all practice IDs
    c.execute("SELECT practice_id FROM practice")
    all_practices = [row[0] for row in c.fetchall()]
    # Get already assigned
    c.execute("SELECT practice_id FROM student_practice WHERE username=?", (username,))
    assigned = [row[0] for row in c.fetchall()]
    # Assign missing
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
