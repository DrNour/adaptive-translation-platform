import streamlit as st
import json
import os
import hashlib
from deep_translator import GoogleTranslator
import difflib
import Levenshtein
from datetime import datetime

# ----------------- File paths -----------------
USER_FILE = "users.json"
DATA_FILE = "submissions.json"
REMEMBER_FILE = "remembered_user.json"

# ----------------- Initialize data -----------------
for f in [USER_FILE, DATA_FILE, REMEMBER_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({}, file)

with open(USER_FILE, "r") as f:
    users = json.load(f)
with open(DATA_FILE, "r") as f:
    submissions = json.load(f)

# ----------------- Helpers -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def translate_text(text, dest_lang):
    try:
        return GoogleTranslator(source='auto', target=dest_lang).translate(text)
    except:
        return "[Translation failed]"

def extract_glossary(text):
    words = text.split()
    freq = {}
    for word in words:
        word = word.lower()
        if len(word) > 3:
            freq[word] = freq.get(word, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

def compute_word_diff(old, new):
    old_words = old.split()
    new_words = new.split()
    sm = difflib.SequenceMatcher(None, old_words, new_words)
    html_left = ""
    html_right = ""
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        old_chunk = " ".join(old_words[i1:i2])
        new_chunk = " ".join(new_words[j1:j2])
        if tag == "equal":
            html_left += old_chunk + " "
            html_right += new_chunk + " "
        elif tag == "replace":
            html_left += f"<span style='background-color:red' title='Replaced'>{old_chunk}</span> "
            html_right += f"<span style='background-color:yellow' title='Replacement'>{new_chunk}</span> "
        elif tag == "delete":
            html_left += f"<span style='background-color:red' title='Deleted'>{old_chunk}</span> "
        elif tag == "insert":
            html_right += f"<span style='background-color:green' title='Inserted'>{new_chunk}</span> "
    return html_left, html_right

def compute_effort(old, new, start_time, end_time):
    edits = Levenshtein.distance(old, new)
    time_spent = (end_time - start_time).total_seconds()
    return edits, time_spent

# ----------------- Session state -----------------
for key in ["logged_in", "username", "role", "remember_me", "source_text", "mt_text", "post_edit", "start_time"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ----------------- Authentication -----------------
def register_user(username, password, role):
    if username in users:
        return False, "Username already exists!"
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "status": "pending"  # Admin approval needed
    }
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)
    return True, "User registered successfully!"

def login_user(username, password, remember=False):
    # Admin login bypass
    if username == "admin" and password == "StrongAdminPassword123!":
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = "Admin"
        return True, "Logged in as Admin"

    user = users.get(username)
    if user:
        if user["password"] == hash_password(password):
            if user.get("status", "approved") != "approved":
                return False, "Your account is pending admin approval."
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.remember_me = remember
            return True, f"Logged in as {username}"
    return False, "Invalid username or password"

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.remember_me = False
    st.session_state.mt_text = ""
    st.session_state.post_edit = ""
    if os.path.exists(REMEMBER_FILE):
        os.remove(REMEMBER_FILE)

# ----------------- Dashboards -----------------
# Student, Instructor, Admin dashboards remain same as previous code snippet

# ----------------- Main App -----------------
if not st.session_state.logged_in:
    st.title("Adaptive Translation Platform")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember me")
        if st.button("Login"):
            success, msg = login_user(username, password, remember)
            if success:
                if remember:
                    with open(REMEMBER_FILE, "w") as f:
                        json.dump({"username": username}, f)
                st.success(msg)
            else:
                st.error(msg)
    with col2:
        st.subheader("Register")
        new_username = st.text_input("New username")
        new_password = st.text_input("New password", type="password")
        role = st.selectbox("Role", ["Student", "Instructor"])
        if st.button("Register"):
            if role == "Admin":
                st.error("Cannot register as Admin!")
            else:
                success, msg = register_user(new_username, new_password, role)
                if success:
                    st.success(msg + " Wait for admin approval.")
                else:
                    st.error(msg)
else:
    st.sidebar.button("Logout", on_click=logout_user)
    if st.session_state.role == "Admin":
        admin_dashboard()
    elif st.session_state.role == "Instructor":
        instructor_dashboard()
    else:
        student_dashboard()
