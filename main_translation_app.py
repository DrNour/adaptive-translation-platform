import streamlit as st
import json
import os
import hashlib
from googletrans import Translator
import re

# ----------------- User Management -----------------
USER_FILE = "users.json"
DATA_FILE = "submissions.json"

if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)
else:
    submissions = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Session state
for key in ["logged_in", "username", "remember_me", "mt_text", "source_text"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ----------------- Authentication Functions -----------------
def register():
    st.subheader("Register")
    new_user = st.text_input("Username", key="reg_user")
    new_pass = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        if new_user in users:
            st.error("Username already exists!")
        else:
            users[new_user] = hash_password(new_pass)
            with open(USER_FILE, "w") as f:
                json.dump(users, f)
            st.success("User registered! You can now log in.")

def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    remember = st.checkbox("Remember me")
    if st.button("Login"):
        if username in users and users[username] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.remember_me = remember
            if remember:
                with open("remembered_user.json", "w") as f:
                    json.dump({"username": username}, f)
            st.success(f"Logged in as {username}")
        else:
            st.error("Invalid username or password")

def logout():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.remember_me = False
        if os.path.exists("remembered_user.json"):
            os.remove("remembered_user.json")
        st.success("Logged out")

def forgot_password():
    st.subheader("Forgot Password")
    user = st.text_input("Enter your username", key="forgot_user")
    if st.button("Reset Password"):
        if user in users:
            new_pass = st.text_input("Enter new password", type="password", key="new_pass")
            if new_pass:
                users[user] = hash_password(new_pass)
                with open(USER_FILE, "w") as f:
                    json.dump(users, f)
                st.success("Password reset successfully!")
        else:
            st.error("Username not found")

# Remembered user
if os.path.exists("remembered_user.json") and not st.session_state.logged_in:
    with open("remembered_user.json", "r") as f:
        remembered = json.load(f)
        st.session_state.logged_in = True
        st.session_state.username = remembered["username"]

# ----------------- Translation & Glossary -----------------
translator = Translator()

def translate_text(text, dest="ar"):
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except:
        return "[Translation failed]"

def extract_glossary(text):
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {}
    for word in words:
        if len(word) > 3:  # skip very short words
            freq[word] = freq.get(word, 0) + 1
    # return top 5 most frequent words
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:5]]

# ----------------- Dashboard -----------------
def show_dashboard():
    st.title(f"Welcome, {st.session_state.username}!")
    st.subheader("Translation & Post-Editing Practice")

    # Source text input
    source_text = st.text_area("Enter English text to translate:")

    if st.button("Translate"):
        mt_text = translate_text(source_text, dest="ar")
        st.session_state.mt_text = mt_text
        st.session_state.source_text = source_text

        # Glossary suggestions
        glossary = extract_glossary(source_text)
        st.subheader("Glossary Suggestions")
        st.write(", ".join(glossary))

    # Post-editing
    if st.session_state.mt_text:
        st.subheader("Machine Translation Output")
        st.text_area("Edit the translation as needed:", st.session_state.mt_text, key="post_edit")

        if st.button("Save Post-Edited Translation"):
            user_submissions = submissions.get(st.session_state.username, [])
            user_submissions.append({
                "source": st.session_state.source_text,
                "mt": st.session_state.mt_text,
                "post_edit": st.session_state["post_edit"]
            })
            submissions[st.session_state.username] = user_submissions
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=4)
            st.success("Your post-edited translation has been saved!")

    # Previous submissions
    if st.checkbox("Show my previous submissions"):
        user_submissions = submissions.get(st.session_state.username, [])
        for i, sub in enumerate(user_submissions, 1):
            st.write(f"**Submission {i}:**")
            st.write(f"Source: {sub['source']}")
            st.write(f"MT: {sub['mt']}")
            st.write(f"Post-edited: {sub['post_edit']}")
            st.write("---")

    logout()

# ----------------- App Routing -----------------
if st.session_state.logged_in:
    show_dashboard()
else:
    option = st.radio("Choose an option", ["Login", "Register", "Forgot Password"])
    if option == "Login":
        login()
    elif option == "Register":
        register()
    else:
        forgot_password()
