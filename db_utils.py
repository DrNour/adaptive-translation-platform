import sqlite3, os, json
from datetime import datetime

DB_FILE = "app.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        approved INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_id INTEGER,
        source_text TEXT,
        mt_text TEXT,
        post_edit TEXT,
        edits INTEGER,
        effort_percent REAL,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS practice_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS student_practice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER,
        status TEXT,
        assigned_at TEXT,
        completed_at TEXT
    )""")
    conn.commit()
    conn.close()

# Users
def register_user(username, password, role):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role, approved) VALUES (?,?,?,?)",
                  (username, password, role, 0 if role!="Admin" else 1))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT password, approved FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0]==password and row[1]==1:
        return True
    return False

def get_user_role(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None

# Tasks
def get_tasks():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, text FROM tasks")
    rows = c.fetchall()
    conn.close()
    return rows

def save_submission(username, task_id, src, mt, pe, bleu, chrf, sem, edits, effort):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO submissions
        (username, task_id, source_text, mt_text, post_edit,
         bleu, chrf, semantic, edits, effort_percent, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (username, task_id, src, mt, pe, bleu, chrf, sem, edits, effort, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_submissions(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM submissions WHERE username=?", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

# Idioms
def get_idioms():
    return []

def add_idiom(cat, exp, meaning):
    pass

def delete_idiom(id):
    pass

# Practice bank
def add_practice_item(cat, prompt, ref):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO practice_bank (category,prompt,reference,created_at) VALUES (?,?,?,?)",
              (cat,prompt,ref,datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_practice_bank():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM practice_bank")
    rows = c.fetchall()
    conn.close()
    return rows

def assign_practices_to_user(username, ids):
    conn = get_conn()
    c = conn.cursor()
    for pid in ids:
        c.execute("INSERT INTO student_practice (username,practice_id,status,assigned_at) VALUES (?,?,?,?)",
                  (username,pid,"recommended",datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT sp.id, sp.practice_id, pb.category, pb.prompt, pb.reference, sp.status, sp.assigned_at, sp.completed_at
                 FROM student_practice sp JOIN practice_bank pb ON sp.practice_id=pb.id
                 WHERE sp.username=?""",(username,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_practice_completed(sp_id, text, username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE student_practice SET status='completed', completed_at=? WHERE id=?",
              (datetime.utcnow().isoformat(), sp_id))
    conn.commit()
    conn.close()

# Heuristics
HEUR_FILE = "heuristics.json"
def load_heuristics():
    if os.path.exists(HEUR_FILE):
        with open(HEUR_FILE,"r") as f: return json.load(f)
    return {"semantic_threshold":65,"bleu_threshold":30,"chrf_threshold":40}

def save_heuristics(h):
    with open(HEUR_FILE,"w") as f: json.dump(h,f)

# Error patterns
def compute_error_pattern(username):
    subs = get_submissions(username)
    if not subs: return None
    df = pd.DataFrame(subs, columns=["id","user","task","src","mt","pe","bleu","chrf","semantic","edits","effort","created"])
    return {
        "avg_bleu": df["bleu"].mean(),
        "avg_chrf": df["chrf"].mean(),
        "avg_semantic": df["semantic"].mean(),
        "avg_edits": df["edits"].mean(),
        "avg_effort": df["effort"].mean()
    }
