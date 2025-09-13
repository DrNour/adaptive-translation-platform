# metrics_utils.py
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.util import ngrams
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go

# Download NLTK data if not already
nltk.download("punkt")

# -----------------------------
# METRICS
# -----------------------------

def compute_bleu_chrf(reference, hypothesis):
    # BLEU
    ref_tokens = nltk.word_tokenize(reference)
    hyp_tokens = nltk.word_tokenize(hypothesis)
    bleu_score = sentence_bleu([ref_tokens], hyp_tokens) * 100  # scale to 0-100

    # chrF (character n-gram F-score)
    def chrf(ref, hyp, n=6):
        ref_ngrams = list(ngrams(ref, n))
        hyp_ngrams = list(ngrams(hyp, n))
        overlap = len(set(ref_ngrams) & set(hyp_ngrams))
        total = max(len(hyp_ngrams), 1)
        return (overlap / total) * 100

    chrf_score = chrf(list(reference), list(hypothesis))
    return bleu_score, chrf_score

def compute_semantic_score(reference, hypothesis):
    vectorizer = TfidfVectorizer().fit([reference, hypothesis])
    vecs = vectorizer.transform([reference, hypothesis])
    score = cosine_similarity(vecs[0], vecs[1])[0][0] * 100  # scale 0-100
    return score

def compute_fluency_errors(text):
    # Simple heuristic: count repeated words, comma splice, multiple spaces
    import re
    errors = 0
    errors += len(re.findall(r'\b(\w+)\s+\1\b', text.lower()))  # repeated words
    errors += len(re.findall(r',\s+\w+', text))  # comma splice heuristic
    errors += len(re.findall(r'\s{2,}', text))  # extra spaces
    return errors

def compute_collocation_errors(text, collocations_list=None):
    if not collocations_list:
        collocations_list = ["make decision", "strong tea", "fast food"]  # example
    errors = 0
    for coll in collocations_list:
        if coll not in text.lower():
            errors += 1
    return errors

def compute_idiom_errors(text, idiom_list=None):
    if not idiom_list:
        idiom_list = ["break the ice", "hit the sack", "piece of cake"]  # example
    errors = 0
    for idiom in idiom_list:
        if idiom not in text.lower():
            errors += 1
    return errors

def compute_edits_effort(mt_text, user_translation):
    # Simple Levenshtein edit distance
    import difflib
    seq = difflib.SequenceMatcher(None, mt_text, user_translation)
    edits = int(seq.quick_ratio() * 100)  # rough proxy
    effort = 100 - edits  # effort inversely proportional
    return edits, effort

# -----------------------------
# VISUALIZATION
# -----------------------------

def plot_radar_for_student_metrics(metrics_dict):
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    values += values[:1]  # close the loop

    fig = go.Figure(
        data=[
            go.Scatterpolar(r=values, theta=categories + [categories[0]],
                            fill='toself', name='Your Metrics')
        ],
        layout=go.Layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True
        )
    )
    return fig
