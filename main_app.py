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
for key in ["logged_in", "username", "role", "remember_me", "source_text", "mt_text", "post_edit", "start_time", "src_lang", "dest_lang"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ----------------- Authentication -----------------
def register_user(username, password, role):
    if username in users:
        return False, "Username already exists!"
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "status": "pending"
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
def student_dashboard():
    st.title(f"Student Dashboard ({st.session_state.username})")
    st.subheader("Translate / Post-edit")

    # Language direction
    if st.session_state.dest_lang is None:
        st.session_state.dest_lang = "ar"

    source_text = st.text_area("Enter text to translate:", value=st.session_state.source_text or "")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Translate"):
            if source_text:
                st.session_state.source_text = source_text
                st.session_state.mt_text = translate_text(source_text, st.session_state.dest_lang)
                st.session_state.start_time = datetime.now()
    with col2:
        if st.button("Swap English ↔ Arabic"):
            # Swap destination language
            st.session_state.dest_lang = "en" if st.session_state.dest_lang=="ar" else "ar"
            if source_text:
                st.session_state.mt_text = translate_text(source_text, st.session_state.dest_lang)
                st.session_state.start_time = datetime.now()
                st.success(f"Swapped translation to {st.session_state.dest_lang.upper()}")

    # Show MT
    if st.session_state.mt_text:
        st.text_area("Machine Translation", value=st.session_state.mt_text, key="mt_text_area")

        # Post-edit
        post_edit = st.text_area("Post-edit translation:", value=st.session_state.mt_text, key="post_edit_area")
        if st.button("Submit Post-edit"):
            end_time = datetime.now()
            edits, time_spent = compute_effort(st.session_state.mt_text, post_edit, st.session_state.start_time, end_time)
            submissions[st.session_state.username] = {
                "source_text": st.session_state.source_text,
                "mt_text": st.session_state.mt_text,
                "post_edit": post_edit,
                "edits": edits,
                "time_sec": time_spent
            }
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=4)
            st.success(f"Submitted! Edits: {edits}, Time spent: {time_spent:.1f}s")
            left, right = compute_word_diff(st.session_state.mt_text, post_edit)
            st.markdown(f"**Track Changes (MT vs Post-edit):**")
            st.markdown(f"<div>{left}</div><div>{right}</div>", unsafe_allow_html=True)

def instructor_dashboard():
    st.title(f"Instructor Dashboard ({st.session_state.username})")
    st.subheader("Student Submissions")
    if submissions:
        for student, data in submissions.items():
            st.markdown(f"**Student:** {student}")
            st.markdown(f"Source: {data['source_text']}")
            st.markdown(f"MT: {data['mt_text']}")
            st.markdown(f"Post-edit: {data['post_edit']}")
            st.markdown(f"Edits: {data['edits']}, Time: {data['time_sec']:.1f}s")
            st.markdown("---")
    else:
        st.info("No submissions yet.")

def admin_dashboard():
    st.title("Administrator Dashboard")

    # Pending approvals
    st.subheader("Pending User Approvals")
    pending_users = [u for u, v in users.items() if v.get("status") == "pending"]
    for u in pending_users:
        if st.button(f"Approve {u}"):
            users[u]["status"] = "approved"
            with open(USER_FILE, "w") as f:
                json.dump(users, f, indent=4)
            st.success(f"{u} approved!")

    # Role switcher
    view_as = st.radio("View app as:", ["Admin Full", "Student", "Instructor"], index=0)
    if view_as == "Admin Full":
        st.subheader("Student Dashboard")
        student_dashboard()
        st.markdown("---")
        st.subheader("Instructor Dashboard")
        instructor_dashboard()
    elif view_as == "Student":
        student_dashboard()
    elif view_as == "Instructor":
        instructor_dashboard()

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
