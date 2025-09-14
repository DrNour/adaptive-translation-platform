import nltk
nltk.download('punkt')
import streamlit as st
from db_utils import (
    register_user, login_user, get_user_role,
    add_practice_item, assign_practices_to_user, get_user_practice_queue,
    get_all_submissions, get_all_users, approve_user,
    export_submissions_with_errors, export_instructor_report_pdf,
    load_idioms_from_file, classify_translation_issues, highlight_errors, suggest_activities
)
import sqlite3

DB_FILE = "app.db"

# ----------------- DATABASE INIT & ADMIN -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create tables
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        approved INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        source_text TEXT,
        student_translation TEXT,
        reference TEXT,
        target_lang TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS practice_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        prompt TEXT,
        reference TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS practice_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        practice_id INTEGER
    )""")
    conn.commit()
    # Insert admin safely
    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role, approved) VALUES (?,?,?,1)",
        ("admin", "admin123", "Admin", 1)
    )
    conn.commit()
    conn.close()

# Initialize DB
init_db()

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

# ----------------- ADMIN DASHBOARD -----------------
def admin_dashboard():
    st.title("🛠 Admin Dashboard")

    users = get_all_users()
    st.markdown("### 👥 Pending Users for Approval")
    pending_users = [u for u in users if u["approved"] == 0]
    if pending_users:
        for u in pending_users:
            st.write(f"- {u['username']} ({u['role']})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Approve {u['username']}", key=f"approve_{u['username']}"):
                    approve_user(u['username'])
                    st.success(f"{u['username']} approved")
                    st.experimental_rerun()
            with col2:
                if st.button(f"Reject {u['username']}", key=f"reject_{u['username']}"):
                    st.info(f"{u['username']} rejected (manual deletion required)")
    else:
        st.info("No pending users.")

    st.markdown("### 📋 All Users")
    for u in users:
        status = "✅ Approved" if u["approved"] else "❌ Pending"
        st.write(f"- {u['username']} ({u['role']}) → {status}")

    st.markdown("### 📝 All Submissions")
    submissions = get_all_submissions()
    if submissions:
        for sub in submissions:
            st.write(f"**{sub['username']} → {sub['target_lang']}**")
            st.write(f"Source: {sub['source_text']}")
            st.write(f"Student Translation: {sub['student_translation']}")
            st.write(f"Reference: {sub['reference']}")
            st.write("---")
    else:
        st.info("No submissions yet.")

# ----------------- MAIN -----------------
def main():
    if not st.session_state.username:
        login_section()
    elif st.session_state.role == "Student":
        student_dashboard()
    elif st.session_state.role == "Instructor":
        instructor_dashboard()
    elif st.session_state.role == "Admin":
        admin_dashboard()

if __name__ == "__main__":
    main()
