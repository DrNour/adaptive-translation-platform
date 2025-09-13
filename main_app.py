import nltk
nltk.download('punkt')
import streamlit as st
from datetime import datetime
from db_utils import (
    init_db, register_user, validate_login, get_user_role,
    save_submission, get_student_practice,
    mark_practice_completed, update_points_and_streak,
    assign_practice_for_student, add_practice_item, get_leaderboard,
    get_adaptive_tasks
)
from metrics_utils import (
    compute_bleu_chrf, compute_semantic_score, compute_edits_effort,
    compute_error_pattern, plot_radar_for_student_metrics
)
from ai_utils import provide_motivational_feedback, suggest_translation_corrections

# -----------------------------
# LOGIN & REGISTRATION
# -----------------------------
def show_login():
    st.markdown("### 🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if validate_login(username, password):
            role = get_user_role(username)
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"Logged in as {username} ({role})")
            st.experimental_rerun()
        else:
            st.error("Invalid login")

def show_register():
    st.markdown("### 📝 Register")
    username = st.text_input("Username", key="r_user")
    password = st.text_input("Password", type="password", key="r_pass")
    role = st.selectbox("Role", ["Student", "Instructor"])
    if st.button("Register"):
        ok = register_user(username, password, role)
        if ok:
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Username already exists.")

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
def student_dashboard():
    st.sidebar.markdown(f"👤 {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    st.title("🎓 Student Dashboard")

    # -----------------------------
    # Gamification: Points & Streak
    # -----------------------------
    points, streak = update_points_and_streak(st.session_state.username, 0)
    st.subheader("🏅 My Gamification Stats")
    st.metric("Points", points)
    st.metric("Streak (days)", streak)
    st.info(provide_motivational_feedback(points, streak))

    # -----------------------------
    # Adaptive Practice Assignment
    # -----------------------------
    assign_practice_for_student(st.session_state.username)

    # -----------------------------
    # Adaptive Translation Tasks
    # -----------------------------
    st.subheader("📌 Translation Tasks")
    tasks = get_adaptive_tasks(st.session_state.username)
    if not tasks:
        st.info("No tasks assigned yet.")
    else:
        for tid, text in tasks:
            st.markdown(f"**Task {tid}:** {text}")
            mt_text = st.text_area("Machine Translation (for comparison)", key=f"mt_{tid}")
            post_edit = st.text_area("Your Translation / Post-edit", key=f"pe_{tid}")
            if st.button(f"Submit Task {tid}"):
                bleu, chrf = compute_bleu_chrf(text, post_edit)
                semantic = compute_semantic_score(text, post_edit)
                edits, effort = compute_edits_effort(mt_text, post_edit)
                save_submission(st.session_state.username, tid, text, mt_text, post_edit,
                                bleu, chrf, semantic, edits, effort)
                points, streak = update_points_and_streak(st.session_state.username, 10)
                st.success("Submission saved! Points +10 awarded.")
                # Feedback
                pattern = compute_error_pattern(st.session_state.username)
                feedback = suggest_translation_corrections(text, post_edit, pattern)
                for f in feedback:
                    st.warning(f"💡 {f}")
                st.experimental_rerun()

    # -----------------------------
    # Practice Queue
    # -----------------------------
    st.subheader("🗂 My Practice Queue")
    queue = get_student_practice(st.session_state.username)
    if not queue:
        st.info("No practice items yet.")
    else:
        for sp_id, pid, cat, prompt, ref, status, assigned_at, completed_at in queue:
            st.markdown(f"**[{status.upper()}]** ({cat}) {prompt}")
            if status == "recommended":
                if st.button(f"Do Practice {sp_id}"):
                    st.session_state.active_practice = (sp_id, prompt, ref)
                    st.experimental_rerun()
            if status == "completed":
                st.caption(f"Completed: {completed_at}")

        if "active_practice" in st.session_state and st.session_state.active_practice:
            sp_id, prompt, ref = st.session_state.active_practice
            st.text_area("Practice prompt", prompt, disabled=True)
            ans = st.text_area("Your translation", key=f"prac_{sp_id}")
            if st.button("Submit Practice"):
                mark_practice_completed(sp_id, ans, st.session_state.username)
                points, streak = update_points_and_streak(st.session_state.username, 5)
                st.success("Practice completed! Points +5 awarded.")
                st.session_state.active_practice = None
                st.experimental_rerun()

    # -----------------------------
    # Error Pattern & Radar Chart
    # -----------------------------
    st.subheader("📊 My Progress")
    pattern = compute_error_pattern(st.session_state.username)
    if pattern:
        st.json(pattern)
        fig = plot_radar_for_student_metrics({
            "BLEU": pattern.get("avg_bleu", 0),
            "chrF": pattern.get("avg_chrf", 0),
            "Semantic": pattern.get("avg_semantic", 0),
            "Effort": min(100, pattern.get("avg_effort", 0)),
            "Edits": min(100, pattern.get("avg_edits", 0))
        })
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# INSTRUCTOR DASHBOARD
# -----------------------------
def instructor_dashboard():
    st.sidebar.markdown(f"👤 {st.session_state.username} ({st.session_state.role})")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    st.title("👨‍🏫 Instructor Dashboard")

    st.subheader("📌 Practice Bank")
    cat = st.text_input("Category")
    prompt = st.text_area("Practice prompt")
    ref = st.text_area("Reference translation")
    if st.button("Add Practice"):
        add_practice_item(cat, prompt, ref)
        st.success("Practice added!")

    st.subheader("🏆 Leaderboard")
    leaderboard = get_leaderboard()
    st.table(leaderboard)

# -----------------------------
# MAIN APP
# -----------------------------
def main():
    init_db()

    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None

    if st.session_state.username is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            show_login()
        with tab2:
            show_register()
    else:
        role = st.session_state.role
        if role is None:
            st.error("Role is not set. Please log in again.")
        elif role.lower() == "student":
            student_dashboard()
        elif role.lower() == "instructor":
            instructor_dashboard()
        else:
            st.info("Role not recognized.")

if __name__ == "__main__":
    main()

