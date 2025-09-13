import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
from nltk.translate.bleu_score import sentence_bleu
import plotly.graph_objects as go

# -----------------------------
# DATABASE UTILS
# -----------------------------
DB_PATH = "adaptive_learning.db"

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
        category TEXT,
        prompt TEXT,
        reference TEXT,
        status TEXT,
        assigned_at TEXT,
        completed_at TEXT,
        bleu REAL, chrf REAL, semantic REAL, edits REAL, effort REAL, feedback TEXT
    )''')
    # Student progress for gamification
    c.execute('''CREATE TABLE IF NOT EXISTS student_progress(
        username TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        badges TEXT DEFAULT ''
    )''')
    conn.commit()
    conn.close()

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

def get_tasks():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT id,text FROM tasks")
    res=c.fetchall()
    conn.close()
    return res

def save_submission(username,task_id,original_text,mt_text,user_text,bleu,chrf,semantic,edits,effort,feedback=""):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute('''INSERT INTO submissions(username,task_id,original_text,mt_text,user_text,
                 bleu,chrf,semantic,edits,effort,feedback,timestamp)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
              (username,task_id,original_text,mt_text,user_text,bleu,chrf,semantic,edits,effort,feedback,str(datetime.now())))
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

def compute_error_pattern(username):
    submissions=get_submissions(username)
    if not submissions: return None
    avg_bleu=sum([s['bleu'] for s in submissions])/len(submissions)
    avg_chrf=sum([s['chrf'] for s in submissions])/len(submissions)
    avg_semantic=sum([s['semantic'] for s in submissions])/len(submissions)
    avg_edits=sum([s['edits'] for s in submissions])/len(submissions)
    avg_effort=sum([s['effort'] for s in submissions])/len(submissions)
    return {"avg_bleu":avg_bleu,"avg_chrf":avg_chrf,"avg_semantic":avg_semantic,"avg_edits":avg_edits,"avg_effort":avg_effort}

# -----------------------------
# AI UTILS
# -----------------------------
def add_ai_practices_to_queue(username,num_exercises=3):
    practices = get_practice_bank()
    if not practices: return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for _ in range(num_exercises):
        p = random.choice(practices)
        c.execute('''INSERT INTO student_practice(username,practice_id,category,prompt,reference,status,assigned_at)
                     VALUES (?,?,?,?,?,?,?)''', (username, p["id"], p["category"], p["prompt"], p["reference"], "recommended", str(datetime.now())))
    conn.commit()
    conn.close()

# -----------------------------
# METRICS UTILS
# -----------------------------
def compute_bleu_chrf(ref,hyp):
    bleu=sentence_bleu([ref.split()],hyp.split())
    chrf=len(set(ref.split()) & set(hyp.split())) / max(1,len(ref.split()))
    return bleu,chrf

def compute_semantic_score(ref,hyp):
    return 0.8 if ref==hyp else 0.6

def compute_edits_effort(mt_text,user_text):
    edits=abs(len(mt_text.split())-len(user_text.split()))
    effort=min(100,edits*5)
    return edits,effort

def plot_radar_for_student_metrics(metrics_dict):
    categories=list(metrics_dict.keys())
    values=list(metrics_dict.values())
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Metrics'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])))
    return fig

# -----------------------------
# GAMIFICATION UTILS
# -----------------------------
def mark_practice_completed(sp_id, ans, username, bleu=0,chrf=0,semantic=0,edits=0,effort=0,feedback=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Mark practice completed
    c.execute('''UPDATE student_practice SET status='completed',completed_at=?,bleu=?,chrf=?,semantic=?,edits=?,effort=?,feedback=?
                 WHERE id=?''', (str(datetime.now()), bleu, chrf, semantic, edits, effort, feedback, sp_id))
    # Points and badges
    c.execute("SELECT points,badges FROM student_progress WHERE username=?", (username,))
    res = c.fetchone()
    if res:
        points, badges = res
        points += 10
        badges_list = badges.split(',') if badges else []
    else:
        points = 10
        badges_list = []

    # Check badges
    c.execute("SELECT COUNT(*) FROM student_practice WHERE username=? AND status='completed'", (username,))
    completed_count = c.fetchone()[0]
    if completed_count == 1 and "First Practice" not in badges_list:
        badges_list.append("First Practice")
    if completed_count == 5 and "5 Practices Completed" not in badges_list:
        badges_list.append("5 Practices Completed")

    c.execute("INSERT OR REPLACE INTO student_progress(username,points,badges) VALUES (?,?,?)",
              (username, points, ','.join(badges_list)))
    conn.commit()
    conn.close()

# -----------------------------
# APP UI
# -----------------------------
def show_login():
    st.markdown("### 🔐 Login")
    username=st.text_input("Username")
    password=st.text_input("Password", type="password")
    if st.button("Login"):
        if validate_login(username,password):
            st.session_state.username=username
            st.session_state.role=get_user_role(username)
            st.experimental_rerun()
        else:
            st.error("Invalid login")

def show_register():
    st.markdown("### 📝 Register")
    username=st.text_input("Username", key="r_user")
    password=st.text_input("Password", type="password", key="r_pass")
    role=st.selectbox("Role", ["Student","Instructor"])
    if st.button("Register"):
        ok=register_user(username,password,role)
        if ok:
            st.success("Registered! You can login immediately.")
        else:
            st.error("Username already exists.")

def student_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("🎓 Student Dashboard")

    # Tasks
    st.subheader("📌 Translation Tasks")
    tasks=get_tasks()
    if not tasks: st.info("No tasks assigned yet.")
    else:
        for tid,text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            mt_text=st.text_area("Machine Translation (for comparison)", key=f"mt_{tid}")
            post_edit=st.text_area("Your Translation / Post-edit", key=f"pe_{tid}")
            if st.button(f"Submit Task {tid}"):
                bleu,chrf=compute_bleu_chrf(text,post_edit)
                semantic=compute_semantic_score(text,post_edit)
                edits,effort=compute_edits_effort(mt_text,post_edit)
                save_submission(st.session_state.username,tid,text,mt_text,post_edit,bleu,chrf,semantic,edits,effort)
                st.success("Submission saved!")

    # Progress radar
    st.subheader("📊 My Progress")
    pattern=compute_error_pattern(st.session_state.username)
    if pattern:
        st.json(pattern)
        fig=plot_radar_for_student_metrics({
            "BLEU": pattern.get("avg_bleu",0),
            "chrF": pattern.get("avg_chrf",0),
            "Semantic": pattern.get("avg_semantic",0),
            "Effort": min(1,pattern.get("avg_effort",0)/100),
            "Edits": min(1,pattern.get("avg_edits",0)/100)
        })
        st.plotly_chart(fig,use_container_width=True)

    # Practice queue
    st.subheader("🗂 My Practice Queue")
    queue=get_student_practice(st.session_state.username)
    if not queue: st.info("No practice items yet. Adding AI-generated exercises...")
    if not queue:
        add_ai_practices_to_queue(st.session_state.username)
        queue=get_student_practice(st.session_state.username)
    for sp_id,pid,cat,prompt,ref,status,assigned_at,completed_at in queue:
        st.markdown(f"**[{status.upper()}]** ({cat}) {prompt}")
        if status=="recommended":
            if st.button(f"Do Practice {sp_id}"):
                st.session_state.active_practice=(sp_id,prompt,ref)
                st.experimental_rerun()
        if status=="completed":
            st.caption(f"Completed: {completed_at}")

    if "active_practice" in st.session_state and st.session_state.active_practice:
        sp_id,prompt,ref=st.session_state.active_practice
        st.text_area("Practice prompt",prompt,disabled=True)
        ans=st.text_area("Your translation", key=f"prac_{sp_id}")
        if st.button("Submit Practice"):
            mark_practice_completed(sp_id,ans,st.session_state.username)
            st.success("Practice completed!")
            st.session_state.active_practice=None
            st.experimental_rerun()

    # Gamification stats
    st.subheader("🏆 My Gamification Stats")
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT points,badges FROM student_progress WHERE username=?",(st.session_state.username,))
    res=c.fetchone()
    conn.close()
    if res:
        points,badges=res
        st.markdown(f"**Points:** {points}")
        st.markdown(f"**Badges:** {badges if badges else 'None'}")

    # Leaderboard
    st.subheader("🏅 Leaderboard")
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT username,points FROM student_progress ORDER BY points DESC LIMIT 10")
    leaders=c.fetchall()
    conn.close()
    if leaders:
        df=pd.DataFrame(leaders,columns=["Username","Points"])
        st.table(df)

def instructor_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("👨‍🏫 Instructor Dashboard")
    st.subheader("📌 Practice Bank")
    cat=st.text_input("Category")
    prompt=st.text_area("Practice prompt")
    ref=st.text_area("Reference translation")
    if st.button("Add Practice"):
        add_practice_item(cat,prompt,ref)
        st.success("Practice added!")

def main():
    init_db()
    if "username" not in st.session_state:
        st.session_state.username=None
    if st.session_state.username is None:
        tab1,tab2=st.tabs(["Login","Register"])
        with tab1: show_login()
        with tab2: show_register()
    else:
        role=st.session_state.role
        if role=="Student": student_dashboard()
        elif role=="Instructor": instructor_dashboard()

if __name__=="__main__":
    main()
