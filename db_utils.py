import sqlite3
from datetime import datetime, timedelta

DB = "adaptive_app.db"

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        points INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_login TEXT
    )
    """)

    # Tasks with difficulty (1=easy, 5=hard)
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        difficulty INTEGER DEFAULT 3
    )
    """)

    # Submissions
    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_id INTEGER,
        source TEXT,
        mt_text TEXT,
        post_edit TEXT,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        edits INTEGER,
        effort REAL,
        submitted_at TEXT
    )
    """)

    # Practice bank
    c.execute("""
    CREATE TABLE IF NOT EXISTS practice_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        completed_at TEXT,
        student_answer TEXT
    )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# USER FUNCTIONS
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB)
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
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == password

def get_user_role(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else None

# -----------------------------
# TASK FUNCTIONS
# -----------------------------
def get_adaptive_tasks(username, max_tasks=3):
    from metrics_utils import compute_error_pattern

    pattern = compute_error_pattern(username)
    avg_score = pattern.get("avg_semantic", 50) if pattern else 50

    # Decide difficulty based on performance
    if avg_score >= 80:
        difficulty = 5
    elif avg_score >= 60:
        difficulty = 4
    elif avg_score >= 40:
        difficulty = 3
    elif avg_score >= 20:
        difficulty = 2
    else:
        difficulty = 1

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, text FROM tasks
        WHERE difficulty=?
        ORDER BY RANDOM()
        LIMIT ?
    """, (difficulty, max_tasks))
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, source, mt_text, post_edit, bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO submissions 
        (username, task_id, source, mt_text, post_edit, bleu, chrf, semantic, edits, effort, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, task_id, source, mt_text, post_edit, bleu, chrf, semantic, edits, effort, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# -----------------------------
# PRACTICE FUNCTIONS
# -----------------------------
def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO practice_bank (category, prompt, reference) VALUES (?, ?, ?)",
              (category, prompt, reference))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT sp.id, pb.id, pb.category, pb.prompt, pb.reference, sp.status, sp.assigned_at, sp.completed_at
        FROM student_practice sp
        JOIN practice_bank pb ON sp.practice_id = pb.id
        WHERE sp.username=?
        ORDER BY sp.assigned_at
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_practice_completed(sp_id, student_answer, username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        UPDATE student_practice
        SET status='completed', completed_at=?, student_answer=?
        WHERE id=? AND username=?
    """, (datetime.now().isoformat(), student_answer, sp_id, username))
    conn.commit()
    conn.close()

def assign_practice_for_student(username, max_assign=3):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT id FROM practice_bank
        WHERE id NOT IN (
            SELECT practice_id FROM student_practice WHERE username=?
        )
        LIMIT ?
    """, (username, max_assign))
    new_items = c.fetchall()
    today = datetime.now().isoformat()
    for (pid,) in new_items:
        c.execute("""
            INSERT INTO student_practice (username, practice_id, assigned_at)
            VALUES (?, ?, ?)
        """, (username, pid, today))
    conn.commit()
    conn.close()

# -----------------------------
# GAMIFICATION
# -----------------------------
def update_points_and_streak(username, points_gain):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT points, streak, last_login FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row:
        points, streak, last_login = row
        points += points_gain
        today = datetime.now().date()
        last_date = datetime.fromisoformat(last_login).date() if last_login else None
        if last_date == today - timedelta(days=1):
            streak += 1
        elif last_date != today:
            streak = 1
        c.execute("UPDATE users SET points=?, streak=?, last_login=? WHERE username=?",
                  (points, streak, datetime.now().isoformat(), username))
    else:
        points = points_gain
        streak = 1
        c.execute("INSERT OR REPLACE INTO users (username, points, streak, last_login) VALUES (?, ?, ?, ?)",
                  (username, points, streak, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return points, streak

def get_leaderboard(top_n=10):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT username, points, streak
        FROM users
        ORDER BY points DESC, streak DESC
        LIMIT ?
    """, (top_n,))
    rows = c.fetchall()
    conn.close()
    return rows
