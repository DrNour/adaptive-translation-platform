import streamlit as st
import sqlite3
import os

# ----------------------------
# Database initialization
# ----------------------------
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

def verify_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    user = c.fetchone()
    conn.close()
    return user

# ----------------------------
# Streamlit Login Page
# ----------------------------
def main():
    st.title("🔐 Translation Platform Login")

    st.write("Don't have an account? [Register here](register.py)")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["student", "instructor"])

    if st.button("Login"):
        user = verify_user(username, password, role)
        if user:
            st.success(f"✅ Welcome, {username}! You are logged in as {role}.")
            if role == "student":
                st.info("Redirecting to student dashboard...")
                os.system("streamlit run student_dashboard.py")
            else:
                st.info("Redirecting to instructor dashboard...")
                os.system("streamlit run instructor_dashboard.py")
        else:
            st.error("❌ Invalid credentials. Please try again.")

if __name__ == "__main__":
    init_db()
    main()
