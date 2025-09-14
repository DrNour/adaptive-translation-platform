import streamlit as st
import sqlite3
import nltk
nltk.download('punkt')

# ----------------- IMPORT DB UTILITIES -----------------
from db_utils import (
    init_db, register_user, login_user, get_user_role,
    add_practice_item, assign_practices_to_user, get_user_practice_queue,
    get_all_submissions, get_all_users,
    export_submissions_with_errors, export_instructor_report_pdf
)
# If tutor_utils code is inside db_utils.py, import from there
from db_utils import load_idioms_from_file, classify_translation_issues, highlight_errors, suggest_activities

# ----------------- INITIALIZE DATABASE -----------------
init_db()  # ensures all tables exist

# ----------------- AUTO-CREATE ADMIN -----------------
def ensure_admin():
    DB_FILE = "app.db"
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username='admin'")
        if not c.fetchone():
            c.execute(
                "INSERT INTO users (username, password, role, approved) VALUES (?,?,?,1)",
                ("admin", "admin123", "Admin", 1)
            )
            print("Admin account created: username='admin', password='admin123'")
        else:
            c.execute(
                "UPDATE users SET password='admin123', role='Admin', approved=1 WHERE username='admin'"
            )
            print("Admin account verified and approved.")

ensure_admin()

# ----------------- SESSION STATE -----------------
if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.role = None

# ----------------- LOGIN / REGISTER -----------------
def login_section():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login_user(username, password):
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.success(f"Welcome, {username} ({st.session_state.role})")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials or not approved yet.")

    st.sidebar.header("Register")
    new_user = st.sidebar.text_input("New Username")
    new_pass = st.sidebar.text_input("New Password", type="password")
    role = st.sidebar.selectbox("Role", ["Student", "Instructor"])
    if st.sidebar.button("Register"):
        register_user(new_user, new_pass, role)
        st.info("Registration submitted. Awaiting admin approval.")

# ----------------- STUDENT DASHBOARD -----------------
def student_dashboard():
    st.title("🎓 Student Dashboard")
    source_text = st.text_area("Source Text")
    post_edit = st.text_area("Your Translation", height=150)
    target_lang = st.selectbox("Target Language", ["en", "ar"])
    reference = st.text_area("Reference Translation (optional)", height=100)

    if st.button("Submit Translation"):
        idioms_dict = load_idioms_from_file("idioms.json")
        report = classify_translation_issues(source_text, post_edit, idioms_dict, lang=target_lang)

        st.markdown("### 🔍 Error Highlighting")
        highlighted = highlight_errors(post_edit, report)
        st.markdown(highlighted, unsafe_allow_html=True)

        st.markdown("### 🎯 Adaptive Suggestions")
        suggestions = suggest_activities(report)
        if not suggestions:
            st.success("✅ No major issues detected. Great job!")
        else:
            for idx, s in enumerate(suggestions):
                st.write(f"- {s['type'].capitalize()} → {s['prompt']}")
                if st.button(f"Add to practice queue ({s['type']})", key=f"pr_{idx}"):
                    pid = add_practice_item(s["type"], s["prompt"], "")
                    assign_practices_to_user(st.session_state.username, [pid])
                    st.success("Added to your practice queue.")

    st.markdown("### 📚 My Practice Queue")
    queue = get_user_practice_queue(st.session_state.username)
    for q in queue:
        st.write(f"- {q['category']}: {q['prompt']}")

# ----------------- INSTRUCTOR DASHBOARD -----------------
def instructor_dashboard():
    st.title("📊 Instructor Dashboard")
    submissions = get_all_submissions()
    users = get_all_users()
    idioms_dict = load_idioms_from_file("idioms.json")

    if not submissions:
        st.info("No student submissions yet.")
    else:
        error_counts = {"semantic": 0, "idiom": 0, "grammar": 0}
        idiom_misses = {}

        for sub in submissions:
            rep = classify_translation_issues(
                sub["source_text"], sub["student_translation"],
                idioms_dict, lang=sub["target_lang"]
            )
            if rep.get("semantic_flag"):
                error_counts["semantic"] += 1
            for idiom, info in rep.get("idiom_issues", {}).items():
                if info["status"] == "non-idiomatic":
                    error_counts["idiom"] += 1
                    idiom_misses[idiom] = idiom_misses.get(idiom, 0) + 1
            if rep.get("grammar"):
                error_counts["grammar"] += len(rep["grammar"])

        st.markdown("### ⚠️ Error Distribution")
        st.bar_chart(error_counts)

        if idiom_misses:
            st.markdown("### ❌ Most Frequently Mistranslated Idioms")
            for idiom, count in sorted(idiom_misses.items(), key=lambda x: -x[1])[:5]:
                st.write(f"- {idiom}: {count} times")

    if st.button("⬇️ Download Submissions + Errors as CSV"):
        filepath = export_submissions_with_errors("submissions_with_errors.csv")
        with open(filepath, "rb") as f:
            st.download_button("Download CSV File", f, file_name="submissions_with_errors.csv")

    if st.button("📄 Download Instructor Report (PDF)"):
        filepath = export_instructor_report_pdf("instructor_report.pdf")
        with open(filepath, "rb") as f:
            st.download_button("Download PDF File", f, file_name="instructor_report.pdf")

# ----------------- MAIN -----------------
def main():
    if not st.session_state.username:
        login_section()
    elif st.session_state.role == "Student":
        student_dashboard()
    elif st.session_state.role == "Instructor":
        instructor_dashboard()
    elif st.session_state.role == "Admin":
        st.success("✅ Admin interface coming soon.")

if __name__ == "__main__":
    main()
