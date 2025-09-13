import sqlite3
from datetime import datetime

DB_PATH = "adaptive_learning.db"

# -----------------------------
# DB INIT
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )''')
    # Tasks
    c.execute('''CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )''')
    # Submissions
    c.execute('''CREATE TABLE IF NOT EXISTS submissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_id INTEGER,
        original_text TEXT,
        mt_text TEXT,
        user_text TEXT,
        bleu REAL, chrf REAL, semantic REAL,
        edits REAL, effort REAL,
        feedback TEXT,
        timestamp TEXT
    )''')
    # Practices
    c.execute('''CREATE TABLE IF NOT EXISTS practices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT
    )''')
    # Student-Practice Queue
    c.execute('''CREATE TABLE IF NOT EXISTS student_practice(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER,
        status TEXT,
        assigned_at TEXT,
        completed_at TEXT,
        bleu REAL, chrf REAL, semantic REAL, edits REAL, effort REAL, feedback TEXT
    )''')
    conn.commit()
    conn.close()

# -----------------------------
# USER FUNCTIONS
# -----------------------------
def register_user(username,password,role):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    try:
        c.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",(username,password,role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_login(username,password):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
    res=c.fetchone()
    conn.close()
    return res is not None

def get_user_role(username):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?",(username,))
    res=c.fetchone()
    conn.close()
    return res[0] if res else None

def get_all_students():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT username FROM users WHERE role='Student'")
    res=[{"username":r[0]} for r in c.fetchall()]
    conn.close()
    # For simplicity, you can compute avg metrics from submissions here
    for s in res:
        s.update({"avg_bleu":0,"avg_chrf":0,"avg_semantic":0,"avg_edits":0,"avg_effort":0,
                  "completed_practices":0,"completed_practice_ids":[]})
    return res

# -----------------------------
# TASKS AND PRACTICE FUNCTIONS
# -----------------------------
def get_tasks():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT id,text FROM tasks")
    res=c.fetchall()
    conn.close()
    return res

def save_submission(username,task_id,original_text,mt_text,user_text,bleu,chrf,semantic,edits,effort,feedback):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute('''INSERT INTO submissions(username,task_id,original_text,mt_text,user_text,
                 bleu,chrf,semantic,edits,effort,feedback,timestamp)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
              (username,task_id,original_text,mt_text,user_text,bleu,chrf,semantic,edits,effort,str(feedback),str(datetime.now())))
    conn.commit()
    conn.close()

def get_submissions(username):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT bleu,chrf,semantic,edits,effort,timestamp FROM submissions WHERE username=?",(username,))
    res=[{"bleu":r[0],"chrf":r[1],"semantic":r[2],"edits":r[3],"effort":r[4],"timestamp":r[5]} for r in c.fetchall()]
    conn.close()
    return res

def get_practice_bank():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT id,category,prompt,reference FROM practices")
    res=[{"id":r[0],"category":r[1],"prompt":r[2],"reference":r[3]} for r in c.fetchall()]
    conn.close()
    return res

def add_practice_item(category,prompt,reference):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("INSERT INTO practices(category,prompt,reference) VALUES (?,?,?)",(category,prompt,reference))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT id,practice_id,category,prompt,reference,status,assigned_at,completed_at FROM student_practice WHERE username=?",(username,))
    res=c.fetchall()
    conn.close()
    return res

def mark_practice_completed(sp_id,ans,username,bleu=0,chrf=0,semantic=0,edits=0,effort=0,feedback=""):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute('''UPDATE student_practice SET status='completed',completed_at=?,bleu=?,chrf=?,semantic=?,edits=?,effort=?,feedback=?
                 WHERE id=?''',(str(datetime.now()),bleu,chrf,semantic,edits,effort,str(feedback),sp_id))
    conn.commit()
    conn.close()

def compute_error_pattern(username):
    submissions=get_submissions(username)
    if not submissions: return None
    avg_bleu=sum([s['bleu'] for s in submissions])/len(submissions)
    avg_chrf=sum([s['chrf'] for s in submissions])/len(submissions)
    avg_semantic=sum([s['semantic'] for s in submissions])/len(submissions)
    avg_edits=sum([s['edits'] for s in submissions])/len(submissions)
    avg_effort=sum([s['effort'] for s in submissions])/len(submissions)
    return {"avg_bleu":avg_bleu,"avg_chrf":avg_chrf,"avg_semantic":avg_semantic,"avg_edits":avg_edits,"avg_effort":avg_effort}

def compute_composite_score(username):
    pattern=compute_error_pattern(username)
    if not pattern: return {}
    return {
        "vocabulary":1-pattern.get("avg_bleu",0),
        "structure":1-pattern.get("avg_chrf",0),
        "meaning":1-pattern.get("avg_semantic",0),
        "editing":pattern.get("avg_effort",0)/100
    }
