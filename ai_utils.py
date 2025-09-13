from db_utils import get_practice_bank, student_practice, add_practice_item
from datetime import datetime
import random

def add_ai_practices_to_queue(username,num_exercises=3):
    """
    Assigns AI-generated or random practices based on weaknesses.
    """
    # For simplicity, randomly pick practices
    practices=get_practice_bank()
    if not practices: return
    import sqlite3
    conn=sqlite3.connect("adaptive_learning.db")
    c=conn.cursor()
    for _ in range(num_exercises):
        p=random.choice(practices)
        c.execute('''INSERT INTO student_practice(username,practice_id,category,prompt,reference,status,assigned_at)
                     VALUES (?,?,?,?,?,?,?)''',(username,p["id"],p["category"],p["prompt"],p["reference"],"recommended",str(datetime.now())))
    conn.commit()
    conn.close()
