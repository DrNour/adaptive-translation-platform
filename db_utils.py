import sqlite3
from datetime import datetime
import os

DB_FILE = "app_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT
                )''')
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT
                )''')
    # Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
                    username TEXT,
                    task_id INTEGER,
                    source TEXT,
                    mt TEXT,
                    post_edit TEXT,
                    bleu REAL,
                    chrf REAL,
                    semantic REAL,
                    edits REAL,
                    effort REAL,
                    timestamp TEXT
                )''')
    # Practice table
    c.execute('''CREATE TABLE IF NOT EXISTS practice (
                    practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    prompt TEXT,
                    reference TEXT
                )''')
    # Student practice assignments
    c.execute('''CREATE TABLE IF NOT EXISTS student_practice (
                    username TEXT,
                    practice_id INTEGER,
                    status TEXT,
                    assigned_at TEXT,
                    completed_at TEXT,
                    student_answer TEXT
                )''')
    conn.commit()
    conn.close()

# -----------------------------
# User functions
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0]==password:
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
# Task functions
# -----------------------------
def get_adaptive_tasks(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, source, mt, post_edit, bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO submissions
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (username, task_id, source, mt, post_edit, bleu, chrf, semantic, edits, effort, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# -----------------------------
# Practice functions
# -----------------------------
def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO practice (category,prompt,reference) VALUES (?,?,?)",
              (category, prompt, reference))
    conn.commit()
    conn.close()

def assign_practice_for_student(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Assign all unassigned practices
    c.execute("""INSERT INTO student_practice(username, practice_id, status, assigned_at)
                 SELECT ?, practice_id, 'recommended', ? FROM practice
                 WHERE practice_id NOT IN (SELECT practice_id FROM student_practice WHERE username=?)""",
              (username, datetime.now().isoformat(), username))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT rowid, practice_id, category, prompt, reference, status, assigned_at, completed_at
                 FROM student_practice sp
                 JOIN practice p ON sp.practice_id = p.practice_id
                 WHERE username=?""", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_practice_completed(sp_id, answer, username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE student_practice SET status='completed', completed_at=?, student_answer=?
                 WHERE rowid=? AND username=?""", (datetime.now().isoformat(), answer, sp_id, username))
    conn.commit()
    conn.close()
