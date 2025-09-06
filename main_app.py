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

# ----------------- Admin credentials -----------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "StrongAdminPassword123!"  # Change this
ADMIN_ROLE = "Admin"

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
    users[username] = {"password": hash_password(password), "role": role}
    with open(USER_FILE, "w") as f:
        json.dump(users, f)
    return True, "User registered successfully!"

def login_user(username, password, remember=False):
    if username in users and users[username]["password"] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = users[username]["role"]
        st.session_state.remember_me = remember
        if remember:
            with open(REMEMBER_FILE, "w") as f:
                json.dump({"username": username}, f)
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

# ----------------- Auto-login -----------------
if os.path.exists(REMEMBER_FILE) and not st.session_state.logged_in:
    with open(REMEMBER_FILE) as f:
        remembered = json.load(f)
        username = remembered.get("username")
        if username and username in users:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]

# ----------------- Dashboards -----------------
def student_dashboard():
    st.title(f"Student Dashboard: {st.session_state.username}")
    source_text = st.text_area("Enter text:", key="source_input")

    lang_choice = st.selectbox("Translate to:", ["Arabic", "English"])
    target_lang = "ar" if lang_choice == "Arabic" else "en"

    if st.button("Translate"):
        mt_text = translate_text(source_text, target_lang)
        st.session_state.mt_text = mt_text
        st.session_state.source_text = source_text
        st.session_state.start_time = datetime.now()
        glossary = extract_glossary(source_text)
        st.subheader("Glossary Suggestions")
        st.write(", ".join(glossary))

    if st.session_state.mt_text:
        st.subheader("Post-Edit Machine Translation")
        st.session_state.post_edit = st.text_area("Edit MT here:", value=st.session_state.mt_text, key="post_edit_area")
        if st.button("Save Post-Edited Translation"):
            end_time = datetime.now()
            edits, time_spent = compute_effort(st.session_state.mt_text, st.session_state.post_edit, st.session_state.start_time, end_time)
            user_subs = submissions.get(st.session_state.username, [])
            user_subs.append({
                "source": st.session_state.source_text,
                "mt": st.session_state.mt_text,
                "post_edit": st.session_state.post_edit,
                "start_time": st.session_state.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "edits": edits,
                "time_spent_sec": time_spent
            })
            submissions[st.session_state.username] = user_subs
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=4)
            st.success("Saved successfully!")

    if st.checkbox("Show my previous submissions"):
        user_subs = submissions.get(st.session_state.username, [])
        for i, sub in enumerate(user_subs, 1):
            st.write(f"**Submission {i}**")
            st.write(f"Source: {sub['source']}")
            left_html, right_html = compute_word_diff(sub['mt'], sub['post_edit'])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**MT Text:**<div style='font-family:monospace'>{left_html}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Post-Edit Text:**<div style='font-family:monospace'>{right_html}</div>", unsafe_allow_html=True)
            st.write(f"Character edits: {sub['edits']}, Time spent: {sub['time_spent_sec']:.1f} sec")
            st.write("---")

def instructor_dashboard():
    st.title(f"Instructor Dashboard: {st.session_state.username}")
    students = list(submissions.keys())
    selected_student = st.selectbox("Select student:", ["All"] + students)
    if selected_student == "All":
        for student, subs in submissions.items():
            st.subheader(f"Student: {student}")
            for i, sub in enumerate(subs, 1):
                st.write(f"Submission {i}")
                left_html, right_html = compute_word_diff(sub['mt'], sub['post_edit'])
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**MT Text:**<div style='font-family:monospace'>{left_html}</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**Post-Edit Text:**<div style='font-family:monospace'>{right_html}</div>", unsafe_allow_html=True)
                st.write(f"Character edits: {sub['edits']}, Time spent: {sub['time_spent_sec']:.1f} sec")
                st.write("---")
    else:
        subs = submissions.get(selected_student, [])
        for i, sub in enumerate(subs, 1):
            st.write(f"Submission {i}")
            left_html, right_html = compute_word_diff(sub['mt'], sub['post_edit'])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**MT Text:**<div style='font-family:monospace'>{left_html}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Post-Edit Text:**<div style='font-family:monospace'>{right_html}</div>", unsafe_allow_html=True)
            st.write(f"Character edits: {sub['edits']}, Time spent: {sub['time_spent_sec']:.1f} sec")
            st.write("---")

def admin_dashboard():
    st.title("Administrator Dashboard")

    # Role switcher
    view_as = st.radio("View app as:", ["Admin Full", "Student", "Instructor"], index=0)

    if view_as == "Admin Full":
        st.subheader("You are in full admin mode.")
        st.write("You can see both student and instructor dashboards together.")
        st.markdown("---")
        st.subheader("Student Dashboard")
        student_dashboard()
        st.markdown("---")
        st.subheader("Instructor Dashboard")
        instructor_dashboard()
    elif view_as == "Student":
        st.subheader("Viewing as Student")
        student_dashboard()
    elif view_as == "Instructor":
        st.subheader("Viewing as Instructor")
        instructor_dashboard()

# ----------------- App Routing -----------------
if st.session_state.logged_in:
    if st.session_state.username == ADMIN_USERNAME:
        admin_dashboard()
    elif st.session_state.role == "Instructor":
        instructor_dashboard()
    else:
        student_dashboard()
else:
    st.subheader("Login or Register")
    username = st.text_input("Username", key="auth_user")
    password = st.text_input("Password", type="password", key="auth_pass")
    role = st.selectbox("Role", ["Student", "Instructor"], key="auth_role")
    remember = st.checkbox("Remember Me", key="auth_remember")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "Admin"
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
            if role == "Admin":
                st.error("Cannot register as Admin!")
            else:
                success, msg = register_user(username, password, role)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
