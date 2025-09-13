import streamlit as st
import sqlite3
from datetime import datetime

# -----------------------------
# DATABASE FUNCTIONS
# -----------------------------

DB_PATH = "adaptive_learning.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create tables if they don't exist
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS practice (
        practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT
    )
    """)
    c.execute("""
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
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_id INTEGER,
        original_text TEXT,
        mt_text TEXT,
        post_edit TEXT,
        bleu REAL,
        chrf REAL,
        semantic REAL,
        edits INTEGER,
        effort REAL,
        submitted_at TEXT,
        FOREIGN KEY(username) REFERENCES users(username),
        FOREIGN KEY(task_id) REFERENCES tasks(task_id)
    )
    """)
    conn.commit()
    conn.close()

def register_user(username, password, role):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False

def get_user_role(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks

def save_submission(username, task_id, original_text, mt_text, post_edit,
                    bleu, chrf, semantic, edits, effort):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO submissions
        (username, task_id, original_text, mt_text, post_edit, bleu, chrf, semantic, edits, effort, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (username, task_id, original_text, mt_text, post_edit,
         bleu, chrf, semantic, edits, effort, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_student_practice(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT sp.rowid, sp.practice_id, p.category, p.prompt, p.reference, sp.status, sp.assigned_at, sp.completed_at
                 FROM student_practice sp
                 JOIN practice p ON sp.practice_id = p.practice_id
                 WHERE sp.username=?""", (username,))
    items = c.fetchall()
    conn.close()
    return items

def mark_practice_completed(rowid, user_ans, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE student_practice SET status='completed', completed_at=? WHERE rowid=? AND username=?",
              (datetime.now().isoformat(), rowid, username))
    conn.commit()
    conn.close()

# -----------------------------
# APP PAGES
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
            st.success("Registration successful! You can now login.")
        else:
            st.error("Username already exists.")

def student_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    st.title("🎓 Student Dashboard")
    st.subheader("📌 Translation Tasks")
    tasks = get_tasks()
    if not tasks:
        st.info("No tasks assigned yet.")
    else:
        for tid, text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            mt_text = st.text_area("Machine Translation (for comparison)", key=f"mt_{tid}")
            post_edit = st.text_area("Your Translation / Post-edit", key=f"pe_{tid}")
            if st.button(f"Submit Task {tid}"):
                # Placeholder metrics
                bleu = 0
                chrf = 0
                semantic = 0
                edits = 0
                effort = 0
                save_submission(st.session_state.username, tid, text, mt_text, post_edit,
                                bleu, chrf, semantic, edits, effort)
                st.success("Submission saved!")

def instructor_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("👨‍🏫 Instructor Dashboard")
    st.write("Instructor features can be added here.")

def admin_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("🛠 Admin Dashboard")
    st.write("Admin features can be added here.")

# -----------------------------
# MAIN
# -----------------------------

def main():
    init_db()
    if "username" not in st.session_state:
        st.session_state.username = None

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
        elif role == "Admin":
            admin_dashboard()

if __name__ == "__main__":
    main()
