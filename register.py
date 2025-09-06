import streamlit as st
import sqlite3

# ----------------------------
# Database setup
# ----------------------------
def init_db():
    conn = sqlite3.connect("translation_platform.db")
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
    conn = sqlite3.connect("translation_platform.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # username already exists
    finally:
        conn.close()

# ----------------------------
# Streamlit Registration Page
# ----------------------------
def main():
    st.title("🔑 Register for Translation Platform")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["student", "instructor"])

    if st.button("Register"):
        if username and password:
            success = add_user(username, password, role)
            if success:
                st.success("✅ Registration successful! You can now log in.")
                st.info("Go to the login page to access your dashboard.")
            else:
                st.error("⚠️ Username already exists. Please choose another.")
        else:
            st.warning("Please fill in all fields.")

if __name__ == "__main__":
    init_db()
    main()
