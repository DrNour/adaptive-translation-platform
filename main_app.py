import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.graph_objects as go

DB_PATH = "adaptive_learning.db"

# -----------------------------
# DATABASE
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
        src TEXT,
        mt_output TEXT,
        post_edit TEXT,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        edits INTEGER,
        effort REAL,
        submitted_at TEXT
    )''')
    # Practices
    c.execute('''CREATE TABLE IF NOT EXISTS practice_bank(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        ref TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_practice(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER,
        category TEXT,
        prompt TEXT,
        ref TEXT,
        status TEXT,
        assigned_at TEXT,
        completed_at TEXT,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        edits INTEGER,
        effort REAL,
        feedback TEXT
    )''')
    # Gamification
    c.execute('''CREATE TABLE IF NOT EXISTS student_progress(
        username TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        badges TEXT DEFAULT ''
    )''')
    conn.commit()
    conn.close()

# -----------------------------
# AUTH
# -----------------------------
def register_user(username, password, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",
                  (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
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

# -----------------------------
# DASHBOARD HELPERS
# -----------------------------
def compute_error_pattern(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(bleu),AVG(chrf),AVG(semantic),AVG(edits),AVG(effort) FROM submissions WHERE username=?",
              (username,))
    res = c.fetchone()
    conn.close()
    if res:
        return {
            "avg_bleu": res[0] or 0,
            "avg_chrf": res[1] or 0,
            "avg_semantic": res[2] or 0,
            "avg_edits": res[3] or 0,
            "avg_effort": res[4] or 0
        }
    return {}

def plot_radar_for_student_metrics(metrics: dict):
    labels = list(metrics.keys())
    values = list(metrics.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=labels, fill='toself', name="Performance"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    return fig

def add_practice_item(cat, prompt, ref):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO practice_bank(category,prompt,ref) VALUES (?,?,?)", (cat, prompt, ref))
    conn.commit()
    conn.close()

def get_practice_bank():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM practice_bank", conn)
    conn.close()
    return df

def get_student_practice(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM student_practice WHERE username=?", (username,))
    res = c.fetchall()
    conn.close()
    return res

def mark_practice_completed(sp_id, ans, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE student_practice SET status='completed', completed_at=? WHERE id=?",
              (str(datetime.now()), sp_id))

    # Gamification
    c.execute("SELECT points,badges FROM student_progress WHERE username=?", (username,))
    res = c.fetchone()
    if res:
        points, badges = res
        points += 10
        badges_list = badges.split(',') if badges else []
    else:
        points = 10
        badges_list = []

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
# UI COMPONENTS
# -----------------------------
def show_login():
    st.markdown("### 🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if validate_login(username, password):
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.experimental_rerun()
        else:
            st.error("Invalid login")

def show_register():
    st.markdown("### 📝 Register")
    username = st.text_input("Username", key="r_user")
    password = st.text_input("Password", type="password", key="r_pass")
    role = st.selectbox("Role", ["Student", "Instructor"])
    if st.button("Register"):
        ok = register_user(username, password, role)
        if ok:
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Username already exists.")

def student_dashboard():
    st.sidebar.markdown(f"👤 {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    st.title("🎓 Student Dashboard")

    # Progress
    st.subheader("📊 My Progress")
    pattern = compute_error_pattern(st.session_state.username)
    if pattern:
        st.json(pattern)
        fig = plot_radar_for_student_metrics({
            "BLEU": pattern.get("avg_bleu", 0),
            "chrF": pattern.get("avg_chrf", 0),
            "Semantic": pattern.get("avg_semantic", 0),
            "Effort": min(100, pattern.get("avg_effort", 0)),
            "Edits": min(100, pattern.get("avg_edits", 0))
        })
        st.plotly_chart(fig, use_container_width=True)

    # Practices
    st.subheader("🗂 My Practice Queue")
    queue = get_student_practice(st.session_state.username)
    if not queue:
        st.info("No practice items yet. Ask your instructor to assign some.")
    for sp_id, pid, cat, prompt, ref, status, assigned_at, completed_at, *_ in queue:
        st.markdown(f"**[{status.upper()}]** ({cat}) {prompt}")
        if status == "recommended":
            if st.button(f"Do Practice {sp_id}"):
                st.session_state.active_practice = (sp_id, prompt, ref)
                st.experimental_rerun()
        if status == "completed":
            st.caption(f"Completed: {completed_at}")

    if st.session_state.active_practice is not None:
        sp_id, prompt, ref = st.session_state.active_practice
        st.text_area("Practice prompt", prompt, disabled=True)
        ans = st.text_area("Your translation", key=f"prac_{sp_id}")
        if st.button("Submit Practice"):
            mark_practice_completed(sp_id, ans, st.session_state.username)
            st.success("Practice completed!")
            st.session_state.active_practice = None
            st.experimental_rerun()

    # Gamification
    st.subheader("🏆 My Gamification Stats")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT points,badges FROM student_progress WHERE username=?", (st.session_state.username,))
    res = c.fetchone()
    conn.close()
    if res:
        points, badges = res
        st.markdown(f"**Points:** {points}")
        st.markdown(f"**Badges:** {badges if badges else 'None'}")

    # Leaderboard
    st.subheader("🏅 Leaderboard")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username,points FROM student_progress ORDER BY points DESC LIMIT 10")
    leaders = c.fetchall()
    conn.close()
    if leaders:
        df = pd.DataFrame(leaders, columns=["Username", "Points"])
        st.table(df)

def instructor_dashboard():
    st.sidebar.markdown(f"👤 {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    st.title("👨‍🏫 Instructor Dashboard")

    st.subheader("📌 Practice Bank")
    cat = st.text_input("Category")
    prompt = st.text_area("Practice prompt")
    ref = st.text_area("Reference translation")
    if st.button("Add Practice"):
        add_practice_item(cat, prompt, ref)
        st.success("Practice added!")

# -----------------------------
# MAIN
# -----------------------------
def main():
    init_db()
    if "username" not in st.session_state:
        st.session_state.username = None
    if "active_practice" not in st.session_state:
        st.session_state.active_practice = None

    if st.session_state.username is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            show_login()
        with tab2:
            show_register()
    else:
        role = st.session_state.role
        if role == "Student":
            student_dashboard()
        elif role == "Instructor":
            instructor_dashboard()

if __name__ == "__main__":
    main()
