import streamlit as st
import json
import os
import hashlib
from googletrans import Translator
import re

# ----------------- File paths -----------------
USER_FILE = "users.json"
DATA_FILE = "submissions.json"

# ----------------- Load users and submissions -----------------
users = {}
if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as f:
        users = json.load(f)

submissions = {}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)

# ----------------- Helpers -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

translator = Translator()

def translate_text(text, dest="ar"):
    try:
        return translator.translate(text, dest=dest).text
    except:
        return "[Translation failed]"

def extract_glossary(text):
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {}
    for word in words:
        if len(word) > 3:
            freq[word] = freq.get(word, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

# ----------------- Session state -----------------
for key in ["logged_in", "username", "remember_me", "source_text", "mt_text", "post_edit"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ----------------- Authentication -----------------
def register_user(username, password):
    if username in users:
        return False, "Username already exists!"
    users[username] = hash_password(password)
    with open(USER_FILE, "w") as f:
        json.dump(users, f)
    return True, "User registered successfully!"

def login_user(username, password, remember=False):
    if username in users and users[username] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.remember_me = remember
        if remember:
            with open("remembered_user.json", "w") as f:
                json.dump({"username": username}, f)
        return True, f"Logged in as {username}"
    return False, "Invalid username or password"

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.remember_me = False
    if os.path.exists("remembered_user.json"):
        os.remove("remembered_user.json")

# ----------------- Dashboard -----------------
def show_dashboard():
    st.title(f"Welcome, {st.session_state.username}!")
    st.subheader("Translation & Post-Editing Practice")

    source_text = st.text_area("Enter English text to translate:", key="source_input")

    if st.button("Translate"):
        mt_text = translate_text(source_text, dest="ar")
        st.session_state.mt_text = mt_text
        st.session_state.source_text = source_text
        glossary = extract_glossary(source_text)
        st.subheader("Glossary Suggestions")
        st.write(", ".join(glossary))

    if st.session_state.mt_text:
        st.subheader("Machine Translation Output")
        st.text_area("Edit translation as needed:", st.session_state.mt_text, key="post_edit")

        if st.button("Save Post-Edited Translation"):
            user_submissions = submissions.get(st.session_state.username, [])
            user_submissions.append({
                "source": st.session_state.source_text,
                "mt": st.session_state.mt_text,
                "post_edit": st.session_state.post_edit
            })
            submissions[st.session_state.username] = user_submissions
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=4)
            st.success("Your post-edited translation has been saved!")

    if st.checkbox("Show my previous submissions"):
        user_submissions = submissions.get(st.session_state.username, [])
        for i, sub in enumerate(user_submissions, 1):
            st.write(f"**Submission {i}:**")
            st.write(f"Source: {sub['source']}")
            st.write(f"MT: {sub['mt']}")
            st.write(f"Post-edited: {sub['post_edit']}")
            st.write("---")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

# ----------------- Teacher/Admin -----------------
ADMIN_USERNAME = "teacher"
ADMIN_PASSWORD = "admin123"  # change to a strong password

def show_teacher_dashboard():
    st.title("Teacher Dashboard - All Student Submissions")
    
    if not submissions:
        st.info("No student submissions yet.")
        return

    student_list = list(submissions.keys())
    selected_student = st.selectbox("Select student to view submissions:", ["All"] + student_list)

    if selected_student == "All":
        for student, subs in submissions.items():
            st.subheader(f"Student: {student}")
            for i, sub in enumerate(subs, 1):
                st.write(f"**Submission {i}:**")
                st.write(f"Source: {sub['source']}")
                st.write(f"MT: {sub['mt']}")
                st.write(f"Post-edited: {sub['post_edit']}")
                st.write("---")
    else:
        subs = submissions.get(selected_student, [])
        if not subs:
            st.info("No submissions for this student yet.")
        for i, sub in enumerate(subs, 1):
            st.write(f"**Submission {i}:**")
            st.write(f"Source: {sub['source']}")
            st.write(f"MT: {sub['mt']}")
            st.write(f"Post-edited: {sub['post_edit']}")
            st.write("---")
    
    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

# ----------------- App -----------------
# Auto-login remembered user
if os.path.exists("remembered_user.json") and not st.session_state.logged_in:
    with open("remembered_user.json") as f:
        remembered = json.load(f)
        st.session_state.logged_in = True
        st.session_state.username = remembered["username"]

# Routing
if st.session_state.logged_in:
    if st.session_state.username == ADMIN_USERNAME:
        show_teacher_dashboard()
    else:
        show_dashboard()
else:
    st.subheader("Login or Register")
    username = st.text_input("Username", key="auth_user")
    password = st.text_input("Password", type="password", key="auth_pass")
    remember = st.checkbox("Remember me", key="auth_remember")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            # Check if admin
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                success, msg = login_user(username, password, remember)
                if success:
                    st.success(msg)
                    st.experimental_rerun()
                else:
                    st.error(msg)
    with col2:
        if st.button("Register"):
            success, msg = register_user(username, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)
