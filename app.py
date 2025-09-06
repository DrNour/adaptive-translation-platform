import streamlit as st
import json
import student_dashboard
import instructor_dashboard

# Load user credentials
with open("users.json", "r") as f:
    users = json.load(f)

# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# Login page
def login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    role = st.sidebar.radio("Role", ["student", "instructor"])
    login_btn = st.sidebar.button("Login")

    if login_btn:
        if role == "student" and username in users["students"] and users["students"][username] == password:
            st.session_state.logged_in = True
            st.session_state.role = "student"
            st.session_state.username = username
        elif role == "instructor" and username in users["instructors"] and users["instructors"][username] == password:
            st.session_state.logged_in = True
            st.session_state.role = "instructor"
            st.session_state.username = username
        else:
            st.sidebar.error("Invalid credentials!")

# Logout button
def logout():
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({
        "logged_in": False, "role": None, "username": None
    }))

# Main logic
def main():
    if not st.session_state.logged_in:
        login()
    else:
        st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
        logout()

        if st.session_state.role == "student":
            student_dashboard.run()
        elif st.session_state.role == "instructor":
            instructor_dashboard.run()

if __name__ == "__main__":
    main()
