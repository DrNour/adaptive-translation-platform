# Self-contained helper functions
def load_idioms_from_file(filepath="idioms.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def classify_translation_issues(source_text, student_translation, idioms_dict, lang="en"):
    return {
        "semantic_score": 0,
        "semantic_flag": False,
        "idiom_issues": {},
        "grammar": []
    }
import sqlite3
import json
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io

DB_FILE = "app.db"

# -----------------------------
# Helper functions
# -----------------------------
def load_idioms_from_file(filepath="idioms.json"):
    """Load idioms from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def classify_translation_issues(source_text, student_translation, idioms_dict, lang="en"):
    """
    Dummy implementation.
    Replace with your actual logic to check semantic, idiom, and grammar issues.
    """
    # Example return structure
    return {
        "semantic_score": 0,
        "semantic_flag": False,
        "idiom_issues": {},
        "grammar": []
    }

# -----------------------------
# Database setup
# -----------------------------
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

