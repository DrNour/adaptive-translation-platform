import math
from collections import defaultdict
import plotly.graph_objects as go
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.chrf_score import sentence_chrf

# -----------------------------
# METRIC COMPUTATIONS
# -----------------------------
def compute_bleu_chrf(reference, hypothesis):
    # reference must be list of tokens
    ref_tokens = [reference.split()]
    hyp_tokens = hypothesis.split()
    bleu = sentence_bleu(ref_tokens, hyp_tokens) * 100
    chrf = sentence_chrf(ref_tokens, hyp_tokens) * 100
    return round(bleu, 2), round(chrf, 2)

def compute_semantic_score(reference, hypothesis):
    # Simplified placeholder; can integrate with embeddings later
    ref_tokens = set(reference.split())
    hyp_tokens = set(hypothesis.split())
    overlap = len(ref_tokens & hyp_tokens)
    score = (overlap / max(len(ref_tokens), 1)) * 100
    return round(score, 2)

def compute_edits_effort(mt_text, post_edit):
    edits = sum(1 for a, b in zip(mt_text, post_edit) if a != b) + abs(len(mt_text)-len(post_edit))
    effort = min(100, edits * 2)
    return edits, round(effort, 2)

# -----------------------------
# ERROR PATTERN FOR STUDENT
# -----------------------------
def compute_error_pattern(username):
    # Dummy implementation: returns averages
    # Replace with proper queries from submissions table if desired
    import sqlite3
    DB = "adaptive_app.db"
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT bleu, chrf, semantic, edits, effort
        FROM submissions
        WHERE username=?
    """, (username,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    n = len(rows)
    avg_bleu = sum(r[0] for r in rows)/n
    avg_chrf = sum(r[1] for r in rows)/n
    avg_semantic = sum(r[2] for r in rows)/n
    avg_edits = sum(r[3] for r in rows)/n
    avg_effort = sum(r[4] for r in rows)/n

    return {
        "avg_bleu": round(avg_bleu, 2),
        "avg_chrf": round(avg_chrf, 2),
        "avg_semantic": round(avg_semantic, 2),
        "avg_edits": round(avg_edits, 2),
        "avg_effort": round(avg_effort, 2)
    }

# -----------------------------
# RADAR CHART
# -----------------------------
def plot_radar_for_student_metrics(metrics_dict):
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    values += values[:1]  # repeat first for closed radar

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories + categories[:1],
                fill='toself',
                name='Performance'
            )
        ]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        showlegend=False
    )
    return fig
