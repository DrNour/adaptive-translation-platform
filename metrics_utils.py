import random
import plotly.graph_objects as go

def compute_bleu_chrf(source, translation):
    # Dummy metrics
    return round(random.uniform(0,1),2), round(random.uniform(0,1),2)

def compute_semantic_score(source, translation):
    return round(random.uniform(0,1),2)

def compute_edits_effort(mt, post_edit):
    return round(random.uniform(0,1),2), round(random.uniform(0,1),2)

def compute_error_pattern(username):
    return {
        "avg_bleu": random.randint(20,100),
        "avg_chrf": random.randint(20,100),
        "avg_semantic": random.randint(20,100),
        "avg_edits": random.randint(0,100),
        "avg_effort": random.randint(0,100)
    }

def plot_radar_for_student_metrics(metrics):
    categories = list(metrics.keys())
    values = list(metrics.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name="Metrics"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])))
    return fig
