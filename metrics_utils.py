# metrics_utils.py
import plotly.graph_objects as go

def compute_bleu_chrf(src, tgt):
    # Dummy implementation
    return 70.0, 65.0

def compute_semantic_score(src, tgt):
    return 80.0

def compute_edits_effort(mt, post_edit):
    return 5.0, 20.0

def plot_radar_for_student_metrics(metrics):
    fig = go.Figure()
    categories = list(metrics.keys())
    values = list(metrics.values())
    values += values[:1]
    categories += categories[:1]
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])))
    return fig
