import sqlite3
import json
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io
import re

DB_FILE = "app.db"

# ----------------- DATABASE FUNCTIONS -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    conn.close()

def register_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, password, role, approved) VALUES (?,?,?,0)",
              (username, password, role))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND approved=1", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_role(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (username,))
    role = c.fetchone()
    conn.close()
    return role[0] if role else None

def add_practice_item(category, prompt, reference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO practice_bank (category, prompt, reference) VALUES (?,?,?)", (category, prompt, reference))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def assign_practices_to_user(username, practice_ids):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for pid in practice_ids:
        c.execute("INSERT INTO practice_assignments (username, practice_id) VALUES (?,?)", (username, pid))
    conn.commit()
    conn.close()

def get_user_practice_queue(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT p.category, p.prompt FROM practice_assignments a
                 JOIN practice_bank p ON a.practice_id = p.id
                 WHERE a.username=?""", (username,))
    rows = c.fetchall()
    conn.close()
    return [{"category": r[0], "prompt": r[1]} for r in rows]

def get_all_submissions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, source_text, student_translation, reference, target_lang FROM submissions")
    rows = c.fetchall()
    conn.close()
    return [
        {"username": r[0], "source_text": r[1], "student_translation": r[2], "reference": r[3], "target_lang": r[4]}
        for r in rows
    ]

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, role, approved FROM users")
    rows = c.fetchall()
    conn.close()
    return [{"username": r[0], "role": r[1], "approved": r[2]} for r in rows]

def approve_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET approved=1 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def delete_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def update_user_role(username, new_role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE username=?", (new_role, username))
    conn.commit()
    conn.close()

# ----------------- TUTOR UTILITIES -----------------
def load_idioms_from_file(filepath="idioms.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def classify_translation_issues(source, translation, idioms_dict=None, lang="en"):
    # Minimal example: real logic can be more complex
    report = {"semantic_flag": False, "semantic_score": 1.0, "idiom_issues": {}, "grammar": []}
    if idioms_dict:
        for idiom in idioms_dict:
            if idiom in source and idiom not in translation:
                report["idiom_issues"][idiom] = {"status": "non-idiomatic"}
    return report

def highlight_errors(translation, report):
    # Simple HTML highlighting
    highlighted = translation
    for idiom, info in report.get("idiom_issues", {}).items():
        if info["status"] == "non-idiomatic":
            highlighted = highlighted.replace(idiom, f"<span style='color:red'>{idiom}</span>")
    return highlighted

def suggest_activities(report):
    suggestions = []
    if report.get("semantic_flag"):
        suggestions.append({"type": "semantic", "prompt": "Review semantic meaning."})
    for idiom, info in report.get("idiom_issues", {}).items():
        if info["status"] == "non-idiomatic":
            suggestions.append({"type": "idiom", "prompt": f"Practice idiom: {idiom}"})
    for g in report.get("grammar", []):
        suggestions.append({"type": "grammar", "prompt": g})
    return suggestions

# ----------------- EXPORT FUNCTIONS -----------------
def export_submissions_with_errors(filepath="submissions_with_errors.csv"):
    submissions = get_all_submissions()
    idioms_dict = load_idioms_from_file("idioms.json")
    headers = ["username", "source_text", "student_translation", "reference", "target_lang",
               "semantic_score", "semantic_flag", "idiom_issues", "grammar_issues"]
    export_rows = []
    for sub in submissions:
        rep = classify_translation_issues(sub["source_text"], sub["student_translation"], idioms_dict, lang=sub["target_lang"])
        export_rows.append([
            sub["username"], sub["source_text"], sub["student_translation"], sub["reference"], sub["target_lang"],
            rep.get("semantic_score"), rep.get("semantic_flag"),
            json.dumps(rep.get("idiom_issues", {}), ensure_ascii=False),
            json.dumps(rep.get("grammar", []), ensure_ascii=False)
        ])
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(export_rows)
    return filepath

def export_instructor_report_pdf(filepath="instructor_report.pdf"):
    submissions = get_all_submissions()
    idioms_dict = load_idioms_from_file("idioms.json")
    error_counts = {"semantic": 0, "idiom": 0, "grammar": 0}
    idiom_misses = {}
    for sub in submissions:
        rep = classify_translation_issues(sub["source_text"], sub["student_translation"], idioms_dict, lang=sub["target_lang"])
        if rep.get("semantic_flag"):
            error_counts["semantic"] += 1
        for idiom, info in rep.get("idiom_issues", {}).items():
            if info.get("status") == "non-idiomatic":
                error_counts["idiom"] += 1
                idiom_misses[idiom] = idiom_misses.get(idiom, 0) + 1
        if rep.get("grammar"):
            error_counts["grammar"] += len(rep["grammar"])

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("Instructor Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Error Distribution:", styles["Heading2"]))
    data = [["Error Type", "Count"]] + [[k, v] for k, v in error_counts.items()]
    table = Table(data)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                               ("GRID", (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    if idiom_misses:
        elements.append(Paragraph("Most Frequently Mistranslated Idioms:", styles["Heading2"]))
        idiom_data = [["Idiom", "Miss Count"]] + sorted(idiom_misses.items(), key=lambda x: -x[1])[:5]
        idiom_table = Table(idiom_data)
        idiom_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(idiom_table)
        elements.append(Spacer(1, 12))

    plt.bar(error_counts.keys(), error_counts.values())
    plt.title("Error Distribution")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    elements.append(Image(buf, width=400, height=200))

    doc.build(elements)
    return filepath
