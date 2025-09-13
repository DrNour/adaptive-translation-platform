from nltk.translate.bleu_score import sentence_bleu
import plotly.graph_objects as go

def compute_bleu_chrf(ref, hyp):
    # dummy chrF as example
    bleu = sentence_bleu([ref.split()], hyp.split())
    chrf = len(set(ref.split()) & set(hyp.split())) / max(1,len(ref.split()))
    return bleu, chrf

def compute_semantic_score(ref, hyp):
    # simplified semantic score (placeholder)
    return 0.8 if ref==hyp else 0.6

def compute_edits_effort(mt_text, user_text):
    edits = abs(len(mt_text.split())-len(user_text.split()))
    effort = min(100, edits*5)
    return edits, effort

def plot_radar_for_student_metrics(metrics_dict):
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Metrics'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])))
    return fig
