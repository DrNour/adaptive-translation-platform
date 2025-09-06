import streamlit as st
import sqlite3
import hashlib

# ---------------- Database Setup ----------------
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
''')
conn.commit()

# ---------------- Helper Functions ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, role):
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, hash_password(password), role))
        conn.commit()
        st.success("Registration successful! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Choose another.")

def authenticate_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    return c.fetchone()

# ---------------- Streamlit UI ----------------
st.title("Adaptive Translation Platform Login / Registration")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    role = st.selectbox("Role", ["Student", "Instructor"])
    if st.button("Register"):
        if new_user and new_password:
            register_user(new_user, new_password, role)
        else:
            st.error("Please provide both username and password.")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.success(f"Welcome {user[0]}! You are logged in as {user[2]}.")
            if user[2] == "Student":
                st.info("Redirecting to Student Dashboard...")
                # Here you can call student_dashboard.py functions
            else:
                st.info("Redirecting to Instructor Dashboard...")
                # Here you can call instructor_dashboard.py functions
        else:
            st.error("Incorrect username or password")
