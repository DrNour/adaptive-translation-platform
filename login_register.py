import streamlit as st
import sqlite3
import os

# Database setup
DB_FILE = "translation_platform.db"

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        conn.commit()
        conn.close()

def add_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    user = c.fetchone()
    conn.close()
    return user

# Streamlit App
st.title("🔐 Adaptive Translation Platform")

tab = st.tabs(["Login", "Register"])
with tab[0]:  # Login tab
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    role = st.selectbox("Role", ["student", "instructor"], key="login_role")
    if st.button("Login"):
        user = verify_user(username, password, role)
        if user:
            st.success(f"Welcome, {username}! You are logged in as {role}.")
            if role == "student":
                st.info("Redirecting to student dashboard...")
                os.system("streamlit run student_dashboard.py")
            else:
                st.info("Redirecting to instructor dashboard...")
                os.system("streamlit run instructor_dashboard.py")
        else:
            st.error("Invalid credentials. Please try again.")

with tab[1]:  # Registration tab
    st.subheader("Register")
    new_user = st.text_input("New Username", key="reg_user")
    new_pass = st.text_input("New Password", type="password", key="reg_pass")
    new_role = st.selectbox("Role", ["student", "instructor"], key="reg_role")
    if st.button("Register"):
        success = add_user(new_user, new_pass, new_role)
        if success:
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Username already exists. Try a different one.")

# Initialize DB
init_db()
