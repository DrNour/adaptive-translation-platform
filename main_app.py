import streamlit as st
import sqlite3
from datetime import datetime

DB_FILE = "adaptive_learning.db"

# -----------------------------
# DATABASE & INIT
# -----------------------------
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

    # Practice table
    c.execute('''CREATE TABLE IF NOT EXISTS practice (
                    practice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    prompt TEXT,
                    reference TEXT
                 )''')

    # Student practice assignments
    c.execute('''CREATE TABLE IF NOT EXISTS student_practice (
                    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    practice_id INTEGER,
                    status TEXT DEFAULT 'recommended',
                    assigned_at TEXT,
                    completed_at TEXT
                 )''')

    # Student progress table
    c.execute('''CREATE TABLE IF NOT EXISTS student_progress (
                    username TEXT PRIMARY KEY,
                    points INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1
                 )''')

    # Badges table
    c.execute('''CREATE TABLE IF NOT EXISTS badges (
                    username TEXT,
                    badge_name TEXT,
                    awarded_at TEXT
                 )''')

    # Add sample users if they don’t exist
    c.execute("INSERT OR IGNORE INTO users VALUES ('student1','pass','Student')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('instructor1','pass','Instructor')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin','pass','Admin')")

    # Add sample tasks
    c.execute("INSERT OR IGNORE INTO tasks (task_id, text) VALUES (1, 'Translate the following paragraph about AI.')")
    c.execute("INSERT OR IGNORE INTO tasks (task_id, text) VALUES (2, 'Translate the news headline about climate change.')")

    # Add sample practice exercises
    c.execute("INSERT OR IGNORE INTO practice (practice_id, category, prompt, reference) VALUES (1, 'Idioms', 'Translate: Break the ice', 'كسر الجليد')")
    c.execute("INSERT OR IGNORE INTO practice (practice_id, category, prompt, reference) VALUES (2, 'Collocations', 'Translate: Make a decision', 'اتخاذ قرار')")

    conn.commit()
    conn.close()
    assign_practice_to_students()


def assign_practice_to_students():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Get all students
    c.execute("SELECT username FROM users WHERE role='Student'")
    students = [row[0] for row in c.fetchall()]
    # Get all practice items
    c.execute("SELECT practice_id FROM practice")
    practices = [row[0] for row in c.fetchall()]

    for student in students:
        for pid in practices:
            c.execute("INSERT OR IGNORE INTO student_practice (username, practice_id, assigned_at) VALUES (?, ?, ?)",
                      (student, pid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


# -----------------------------
# USER & DASHBOARD FUNCTIONS
# -----------------------------
def validate_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    res = c.fetchone()
    conn.close()
    if res:
        st.session_state.role = res[0]
        return True
    return False


def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?,?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT task_id, text FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks


def get_student_practice(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT sp.rowid, p.category, p.prompt, p.reference, sp.status
                 FROM student_practice sp
                 JOIN practice p ON sp.practice_id = p.practice_id
                 WHERE sp.username=?''', (username,))
    rows = c.fetchall()
    conn.close()
    return rows


def save_submission(username, task_id, text, machine_text, student_text):
    # For simplicity, submissions just increase points
    add_points(username, 10)


def add_points(username, points):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO student_progress (username, points) VALUES (?,0)", (username,))
    c.execute("UPDATE student_progress SET points = points + ? WHERE username = ?", (points, username))
    conn.commit()
    conn.close()


def award_badge(username, badge_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO badges VALUES (?, ?, ?)", (username, badge_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def mark_practice_completed(rowid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE student_practice SET status='completed', completed_at=? WHERE rowid=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rowid))
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
            st.success("Registration successful!")
        else:
            st.error("Username already exists.")


# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
def student_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    st.title("🎓 Student Dashboard")
    st.subheader("📌 Translation Tasks")
    tasks = get_tasks()
    if tasks:
        for tid, text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            student_text = st.text_area("Your Translation", key=f"task_{tid}")
            if st.button(f"Submit Task {tid}"):
                save_submission(st.session_state.username, tid, text, "", student_text)
                award_badge(st.session_state.username, "First Submission")
                st.success("Submission saved, points awarded!")
    else:
        st.info("No tasks available yet.")

    st.subheader("🗂 My Practice Queue")
    queue = get_student_practice(st.session_state.username)
    if queue:
        for rowid, category, prompt, reference, status in queue:
            st.markdown(f"**[{status.upper()}]** ({category}) {prompt}")
            if status == "recommended":
                ans = st.text_area("Your translation", key=f"prac_{rowid}")
                if st.button("Submit Practice", key=f"btn_{rowid}"):
                    mark_practice_completed(rowid)
                    st.success("Practice completed!")
    else:
        st.info("No practice assigned yet.")


# -----------------------------
# INSTRUCTOR DASHBOARD
# -----------------------------
def instructor_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("👨‍🏫 Instructor Dashboard")

    st.subheader("📌 Manage Translation Tasks")
    task_text = st.text_area("New Task")
    if st.button("Add Task"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (text) VALUES (?)", (task_text,))
        conn.commit()
        conn.close()
        st.success("Task added!")

    st.subheader("📌 Practice Bank")
    cat = st.text_input("Practice Category")
    prompt = st.text_area("Practice Prompt")
    ref = st.text_area("Reference Translation")
    if st.button("Add Practice"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO practice (category, prompt, reference) VALUES (?, ?, ?)", (cat, prompt, ref))
        conn.commit()
        conn.close()
        st.success("Practice added!")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
def admin_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.title("🛠 Admin Dashboard")

    st.subheader("👥 Manage Users")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, role FROM users")
    users = c.fetchall()
    st.table(users)
    conn.close()


# -----------------------------
# MAIN APP
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
        else:
            st.error("Unknown role!")


if __name__ == "__main__":
    main()
