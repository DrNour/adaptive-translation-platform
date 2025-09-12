import sacrebleu
import Levenshtein
import plotly.graph_objects as go
import numpy as np

def compute_bleu_chrf(ref, hyp):
    bleu = sacrebleu.corpus_bleu([hyp], [[ref]]).score if hyp else 0
    chrf = sacrebleu.corpus_chrf([hyp], [[ref]]).score if hyp else 0
    return bleu, chrf

def compute_semantic_score(ref, hyp):
    # placeholder semantic similarity (Levenshtein ratio)
    return Levenshtein.ratio(ref, hyp)*100 if hyp else 0

def compute_edits_effort(mt, pe):
    edits = Levenshtein.distance(mt, pe) if mt and pe else 0
    effort = (edits/len(mt))*100 if mt else 0
    return edits, effort

def plot_radar_for_student_metrics(metrics, title="Skill Profile"):
    axes = ["BLEU","chrF","Semantic","Effort","Edits"]
    vals = [metrics.get(k,0) for k in axes]
    vals += vals[:1]
    fig = go.Figure(data=[go.Scatterpolar(r=vals, theta=axes+axes[:1], fill="toself")])
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100])),showlegend=False)
    return fig
