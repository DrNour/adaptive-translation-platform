import os
import sqlite3
import json
import csv
import streamlit as st
import nltk
nltk.download('punkt')

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io

# ---------------- Writable DB Path ----------------
DB_FILE = os.path.join(os.environ.get("HOME", "/tmp"), "app.db")  # writable on Streamlit Cloud

# ---------------- DB Utilities ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        approved INTEGER DEFAULT 0
    )""")
    # Submissions table
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        source_text TEXT,
        student_translation TEXT,
        reference TEXT,
        target_lang TEXT
    )""")
    # Practice bank table
    c.execute("""CREATE TABLE IF NOT EXISTS practice_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT
    )""")
    # Practice assignments
    c.execute("""CREATE TABLE IF NOT EXISTS practice_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER
    )""")
    conn.commit()

    # Insert admin safely
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role, approved) VALUES (?,?,?,1)",
        ("admin", "admin123", "Admin", 1)
    )
    conn.commit()
    conn.close()

def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, password, role, approved) VALUES (?,?,?,0)",
              (username, password, role))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND approved=1", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_role(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else None

def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO practice_bank (category, prompt, reference) VALUES (?,?,?)", (category, prompt, reference))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def assign_practices_to_user(username, practice_ids):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for pid in practice_ids:
        c.execute("INSERT INTO practice_assignments (username, practice_id) VALUES (?,?)", (username, pid))
    conn.commit()
    conn.close()

def get_user_practice_queue(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT p.category, p.prompt FROM practice_assignments a
                 JOIN practice_bank p ON a.practice_id = p.id
                 WHERE a.username=?""", (username,))
    rows = c.fetchall()
    conn.close()
    return [{"category": r[0], "prompt": r[1]} for r in rows]

def get_all_submissions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, source_text, student_translation, reference, target_lang FROM submissions")
    rows = c.fetchall()
    conn.close()
    return [
        {"username": r[0], "source_text": r[1], "student_translation": r[2], "reference": r[3], "target_lang": r[4]}
        for r in rows
    ]

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, role, approved FROM users")
    rows = c.fetchall()
    conn.close()
    return [{"username": r[0], "role": r[1], "approved": r[2]} for r in rows]

# ---------------- Tutor Utilities (placeholder) ----------------
def load_idioms_from_file(filename):
    return {}  # replace with your actual idioms loading

def classify_translation_issues(source, translation, idioms_dict, lang="en"):
    return {"semantic_flag": False, "idiom_issues": {}, "grammar": []}  # replace with actual logic

def highlight_errors(text, report):
    return text  # placeholder

def suggest_activities(report):
    return []  # placeholder

# ---------------- Streamlit App ----------------
if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.role = None

def login_section():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login_user(username, password):
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.success(f"Welcome, {username} ({st.session_state.role})")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials or not approved yet.")

    st.sidebar.header("Register")
    new_user = st.sidebar.text_input("New Username")
    new_pass = st.sidebar.text_input("New Password", type="password")
    role = st.sidebar.selectbox("Role", ["Student", "Instructor"])
    if st.sidebar.button("Register"):
        register_user(new_user, new_pass, role)
        st.info("Registration submitted. Awaiting admin approval.")

    # Admin login shortcut
    if st.sidebar.button("Login as Admin (Test)"):
        st.session_state.username = "admin"
        st.session_state.role = "Admin"
        st.experimental_rerun()

def student_dashboard():
    st.title("🎓 Student Dashboard")
    st.write("Student dashboard works!")  # placeholder

def instructor_dashboard():
    st.title("📊 Instructor Dashboard")
    st.write("Instructor dashboard works!")  # placeholder

def main():
    init_db()  # safe, writable
    if not st.session_state.username:
        login_section()
    elif st.session_state.role == "Student":
        student_dashboard()
    elif st.session_state.role == "Instructor":
        instructor_dashboard()
    elif st.session_state.role == "Admin":
        st.success("✅ Admin interface coming soon.")

if __name__ == "__main__":
    main()
