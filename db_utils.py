import sqlite3
from datetime import datetime

DB_FILE = "adaptive_learning.db"

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    # Tasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT
        )
    ''')
    # Submissions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            username TEXT,
            task_id INTEGER,
            source_text TEXT,
            mt_text TEXT,
            student_text TEXT,
            bleu REAL,
            chrf REAL,
            semantic REAL,
            edits REAL,
            effort REAL,
            submitted_at TEXT
        )
    ''')
    # Practice table
    c.execute('''
        CREATE TABLE IF NOT EXISTS practice (
            practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            prompt TEXT,
            reference TEXT
        )
    ''')
    # Student practice table
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_practice (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            practice_id INTEGER,
            status TEXT DEFAULT 'recommended',
            assigned_at TEXT,
            completed_at TEXT,
            student_answer TEXT
        )
    ''')
    conn.commit()
    conn.close()

# -----------------------------
# USER FUNCTIONS
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_user_role(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else None

# -----------------------------
# TASK FUNCTIONS
# -----------------------------
def get_adaptive_tasks(username):
    # In a real app, you could filter tasks per student
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT task_id, source_text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, source_text, mt_text, student_text, bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (username, task_id, source_text, mt_text, student_text, bleu, chrf, semantic, edits, effort, submitted_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (username, task_id, source_text, mt_text, student_text, bleu, chrf, semantic, edits, effort, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# -----------------------------
# PRACTICE FUNCTIONS
# -----------------------------
def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?,?,?)", (category, prompt, reference))
    conn.commit()
    conn.close()

def assign_practice_for_student(username):
    """Automatically assign unassigned practices to a student."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Find unassigned practices
    c.execute('''
        SELECT practice_id FROM practice
        WHERE practice_id NOT IN (
            SELECT practice_id FROM student_practice WHERE username=?
        )
    ''', (username,))
    unassigned = c.fetchall()
    for (pid,) in unassigned:
        c.execute('''
            INSERT INTO student_practice (username, practice_id, status, assigned_at)
            VALUES (?,?,?,?)
        ''', (username, pid, 'recommended', datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT sp.rowid, sp.practice_id, p.category, p.prompt, p.reference, sp.status, sp.assigned_at, sp.completed_at
        FROM student_practice sp
        JOIN practice p ON sp.practice_id = p.practice_id
        WHERE sp.username=?
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_practice_completed(sp_id, answer, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE student_practice
        SET status='completed', completed_at=?, student_answer=?
        WHERE rowid=? AND username=?
    """, (datetime.now().isoformat(), answer, sp_id, username))
    conn.commit()
    conn.close()
