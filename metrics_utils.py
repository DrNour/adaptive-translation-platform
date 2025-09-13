import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.util import ngrams
from difflib import SequenceMatcher
import plotly.graph_objects as go

nltk.download('punkt')

# -----------------------------
# METRICS FUNCTIONS
# -----------------------------

def compute_bleu_chrf(reference, hypothesis):
    """
    Compute BLEU and chrF scores.
    BLEU: standard n-gram overlap metric.
    chrF: character n-gram F-score (approximated here).
    """
    ref_tokens = nltk.word_tokenize(reference.lower())
    hyp_tokens = nltk.word_tokenize(hypothesis.lower())

    bleu = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.25,0.25,0.25,0.25)) * 100

    # Approximate chrF as character n-gram F1
    def get_char_ngrams(text, n=3):
        return [text[i:i+n] for i in range(len(text)-n+1)]

    ref_ngrams = get_char_ngrams(reference.lower())
    hyp_ngrams = get_char_ngrams(hypothesis.lower())

    intersection = len(set(ref_ngrams) & set(hyp_ngrams))
    precision = intersection / max(len(hyp_ngrams),1)
    recall = intersection / max(len(ref_ngrams),1)
    chrf = 2 * precision * recall / max(precision + recall, 1e-8) * 100

    return round(bleu,2), round(chrf,2)

def compute_semantic_score(reference, hypothesis):
    """
    Simplified semantic similarity score: based on SequenceMatcher ratio.
    """
    ratio = SequenceMatcher(None, reference.lower(), hypothesis.lower()).ratio()
    return round(ratio*100,2)

def compute_edits_effort(mt_text, user_translation):
    """
    Compute number of edits (Levenshtein-like) and effort percentage.
    """
    matcher = SequenceMatcher(None, mt_text, user_translation)
    ratio = matcher.ratio()
    edits = round((1 - ratio) * 100,2)  # percentage of edits
    effort = edits  # for simplicity, effort = edits percentage
    return edits, effort

# -----------------------------
# ERROR PATTERN AND RADAR
# -----------------------------
def compute_error_pattern(username, submissions):
    """
    Compute average metrics for a student.
    submissions: list of dicts with 'bleu','chrf','semantic','edits','effort'
    """
    if not submissions:
        return None
    avg_bleu = sum(s['bleu'] for s in submissions)/len(submissions)
    avg_chrf = sum(s['chrf'] for s in submissions)/len(submissions)
    avg_semantic = sum(s['semantic'] for s in submissions)/len(submissions)
    avg_edits = sum(s['edits'] for s in submissions)/len(submissions)
    avg_effort = sum(s['effort'] for s in submissions)/len(submissions)
    return {
        'avg_bleu': round(avg_bleu,2),
        'avg_chrf': round(avg_chrf,2),
        'avg_semantic': round(avg_semantic,2),
        'avg_edits': round(avg_edits,2),
        'avg_effort': round(avg_effort,2)
    }

def plot_radar_for_student_metrics(metrics):
    """
    metrics: dict with BLEU, chrF, Semantic, Edits, Effort
    """
    categories = list(metrics.keys())
    values = list(metrics.values())
    values += values[:1]  # Close the radar

    fig = go.Figure(
        data=[
            go.Scatterpolar(r=values, theta=categories + [categories[0]],
                            fill='toself', name='Student Metrics')
        ]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        showlegend=False
    )
    return fig
