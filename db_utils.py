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
            text TEXT
        )
    ''')

    # Submissions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            submitted_at TEXT,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(task_id) REFERENCES tasks(task_id)
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

    # Student practice queue
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_practice (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            practice_id INTEGER,
            status TEXT DEFAULT 'recommended',
            assigned_at TEXT,
            completed_at TEXT,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(practice_id) REFERENCES practice(practice_id)
        )
    ''')

    conn.commit()
    conn.close()


# -----------------------------
# USER MANAGEMENT
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False

def get_user_role(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


# -----------------------------
# TASKS AND SUBMISSIONS
# -----------------------------
def get_adaptive_tasks(username):
    # For simplicity: return all tasks
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, source_text, mt_text, user_translation,
                    bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (
            username, task_id, source_text, mt_text, user_translation,
            bleu, chrf, semantic, edits, effort, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, task_id, source_text, mt_text, user_translation,
          bleu, chrf, semantic, edits, effort, datetime.now().isoformat()))
    conn.commit()
    conn.close()


# -----------------------------
# PRACTICE MANAGEMENT
# -----------------------------
def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?, ?, ?)",
              (category, prompt, reference))
    conn.commit()
    conn.close()

def assign_practice_for_student(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Assign all unassigned practices
    c.execute('''
        INSERT INTO student_practice (username, practice_id, status, assigned_at)
        SELECT ?, practice_id, 'recommended', ?
        FROM practice
        WHERE practice_id NOT IN (
            SELECT practice_id FROM student_practice WHERE username=?
        )
    ''', (username, datetime.now().isoformat(), username))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT sp.rowid, p.practice_id, p.category, p.prompt, p.reference,
               sp.status, sp.assigned_at, sp.completed_at
        FROM student_practice sp
        JOIN practice p ON sp.practice_id = p.practice_id
        WHERE sp.username=?
    ''', (username,))
    queue = c.fetchall()
    conn.close()
    return queue

def mark_practice_completed(rowid, user_translation, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE student_practice
        SET status='completed', completed_at=?
        WHERE rowid=? AND username=?
    ''', (datetime.now().isoformat(), rowid, username))
    conn.commit()
    conn.close()
