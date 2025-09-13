import streamlit as st
from db_utils import (
    init_db, register_user, validate_login, get_user_role,
    get_tasks, save_submission, get_student_practice,
    add_practice_item, assign_practice_for_student, mark_practice_completed
)

# -----------------------------
# LOGIN & REGISTER
# -----------------------------
def show_login():
    st.markdown("### 🔐 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if validate_login(username, password):
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.success(f"Logged in as {username} ({st.session_state.role})")
        else:
            st.error("Invalid username or password")

def show_register():
    st.markdown("### 📝 Register")
    username = st.text_input("Username", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    role = st.selectbox("Role", ["Student", "Instructor", "Admin"])
    if st.button("Register"):
        if register_user(username, password, role):
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Username already exists.")

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
def student_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} (Student)")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    st.title("🎓 Student Dashboard")

    # Show tasks
    st.subheader("📌 Translation Tasks")
    tasks = get_tasks()
    if not tasks:
        st.info("No tasks available yet.")
    else:
        for tid, text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            post_edit = st.text_area("Your translation / post-edit", key=f"pe_{tid}")
            if st.button(f"Submit Task {tid}", key=f"submit_{tid}"):
                # For now, dummy metrics
                save_submission(st.session_state.username, tid, text, "", post_edit,
                                bleu=0, chrf=0, semantic=0, edits=0, effort=0)
                st.success("Submission saved!")

    # Practice queue
    st.subheader("🗂 My Practice Queue")
    assign_practice_for_student(st.session_state.username)  # auto-assign
    queue = get_student_practice(st.session_state.username)
    if not queue:
        st.info("No practice items yet.")
    else:
        for sp_id, pid, cat, prompt, ref, status, assigned_at, completed_at in queue:
            st.markdown(f"**[{status.upper()}]** ({cat}) {prompt}")
            if status == "recommended":
                ans = st.text_area(f"Your answer for Practice {sp_id}", key=f"prac_{sp_id}")
                if st.button(f"Submit Practice {sp_id}", key=f"submit_prac_{sp_id}"):
                    mark_practice_completed(sp_id, ans, st.session_state.username)
                    st.success("Practice completed!")
                    st.experimental_rerun()

# -----------------------------
# INSTRUCTOR DASHBOARD
# -----------------------------
def instructor_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} (Instructor)")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    st.title("👨‍🏫 Instructor Dashboard")

    st.subheader("📌 Practice Bank")
    cat = st.text_input("Category", key="ins_cat")
    prompt = st.text_area("Practice prompt", key="ins_prompt")
    ref = st.text_area("Reference translation", key="ins_ref")
    if st.button("Add Practice"):
        add_practice_item(cat, prompt, ref)
        st.success("Practice added!")

# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
def admin_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: {st.session_state.username} (Admin)")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    st.title("🛠 Admin Dashboard")
    st.info("For now, admin dashboard is minimal. You can see instructor and student registrations here in future updates.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    init_db()

    if "username" not in st.session_state:
        st.session_state.username = None
        st.session_state.role = None

    if st.session_state.username is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            show_login()
        with tab2:
            show_register()
    else:
        role = st.session_state.role
        if role == "Student":
            student_dashboard()
        elif role == "Instructor":
            instructor_dashboard()
        elif role == "Admin":
            admin_dashboard()
        else:
            st.error("Unknown role!")

if __name__ == "__main__":
    main()
