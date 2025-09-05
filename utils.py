import sqlite3
import pandas as pd
from datetime import datetime
import editdistance  # pip install editdistance

DB_PATH = "pe_platform.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS post_editing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            source_text TEXT NOT NULL,
            mt_output TEXT NOT NULL,
            student_edit TEXT NOT NULL,
            duration REAL,
            edit_distance REAL,
            mt_type TEXT CHECK(mt_type IN ('manual','auto')) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_progress(username, source_text, mt_output, student_edit, duration, mt_type='manual'):
    dist = editdistance.eval(mt_output, student_edit)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO post_editing
        (username, source_text, mt_output, student_edit, duration, edit_distance, mt_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, source_text, mt_output, student_edit, duration, dist, mt_type))
    conn.commit()
    conn.close()

def fetch_student_progress(username):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM post_editing WHERE username=?", conn, params=(username,))
    conn.close()
    return df

def fetch_all_progress():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM post_editing", conn)
    conn.close()
    return df

def calculate_metrics(df):
    metrics = df.groupby(['username','mt_type']).agg({
        'duration':'mean',
        'edit_distance':'mean',
        'id':'count'
    }).rename(columns={'id':'tasks_completed'}).reset_index()
    return metrics
