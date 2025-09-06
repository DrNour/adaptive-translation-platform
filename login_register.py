import streamlit as st
import json
import os
import hashlib

# Path to store user data
USER_FILE = "users.json"

# Load users from file, or create empty dict if file doesn't exist
if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "remember_me" not in st.session_state:
    st.session_state.remember_me = False

# Registration
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

# Login
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

# Logout
def logout():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.remember_me = False
        if os.path.exists("remembered_user.json"):
            os.remove("remembered_user.json")
        st.success("Logged out")

# Forgot Password
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

# Check for remembered user
if os.path.exists("remembered_user.json") and not st.session_state.logged_in:
    with open("remembered_user.json", "r") as f:
        remembered = json.load(f)
        st.session_state.logged_in = True
        st.session_state.username = remembered["username"]

# Main App
if st.session_state.logged_in:
    st.write(f"Welcome, {st.session_state.username}!")
    logout()
else:
    option = st.radio("Choose an option", ["Login", "Register", "Forgot Password"])
    if option == "Login":
        login()
    elif option == "Register":
        register()
    else:
        forgot_password()
