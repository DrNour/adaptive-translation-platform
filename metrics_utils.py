# tutor_utils.py
import re
import json
import math

# Optional heavy imports with graceful fallback
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    SEM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    HAVE_SENT_TRANS = True
except Exception:
    SEM_MODEL = None
    HAVE_SENT_TRANS = False

try:
    import language_tool_python
    LANG_TOOL = language_tool_python.LanguageTool('en-US')
    HAVE_LANGTOOL = True
except Exception:
    LANG_TOOL = None
    HAVE_LANGTOOL = False

# For collocation frequency heuristics
try:
    import nltk
    from nltk.corpus import brown
    nltk.download('brown', quiet=True)
    HAVE_NLTK = True
except Exception:
    HAVE_NLTK = False

# Idiom DB loader (assumes db_utils idioms table or idioms.json)
def load_idioms_from_file(path="idioms.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Accept either {eng: {"arabic":..., "category":...}} or simple mapping
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

# ------------- DETECTORS -------------
def semantic_similarity_score(source, student_translation, reference=None):
    """
    Returns score 0..100; higher = more semantically similar.
    If SentenceTransformer not available, fallback to simple ratio.
    If reference provided, compare student->reference, else compare source->student (cross-lingual risk).
    """
    if not student_translation:
        return 0.0
    if HAVE_SENT_TRANS and SEM_MODEL:
        try:
            # If both are same language, straightforward; otherwise still may work with multilingual model
            a = SEM_MODEL.encode(source if reference is None else reference, convert_to_tensor=True)
            b = SEM_MODEL.encode(student_translation, convert_to_tensor=True)
            sim = float(st_util.cos_sim(a, b).item())
            return max(0.0, min(100.0, sim * 100.0))
        except Exception:
            pass
    # fallback: rough token overlap ratio
    from difflib import SequenceMatcher
    ref = reference if reference else source
    ratio = SequenceMatcher(None, ref, student_translation).ratio()
    return round(ratio * 100.0, 2)

def detect_idiomatic_issues(source_text, student_translation, idioms_dict):
    """
    Returns dict: {idiom_text: {"status": "idiomatic"|"non-idiomatic-missing"|"non-idiomatic-literal", "expected": arabic}}
    """
    detected = {}
    s_low = source_text.lower()
    st_low = (student_translation or "").lower()
    for eng, data in idioms_dict.items():
        eng_low = eng.lower()
        if eng_low in s_low:
            expected = data.get("arabic") if isinstance(data, dict) else data
            # If expected Arabic appears in student translation -> idiomatic
            if expected and expected.strip() and expected in (student_translation or ""):
                detected[eng] = {"status": "idiomatic", "expected": expected}
            else:
                # literal English words appearing in Arabic text -> literal translation
                if eng_low in st_low:
                    detected[eng] = {"status": "non-idiomatic-literal", "expected": expected}
                else:
                    detected[eng] = {"status": "non-idiomatic-missing", "expected": expected}
    return detected

def detect_fluency_grammar(student_translation, lang="en"):
    """
    Returns list of grammar/fluency matches (message, replacements).
    For English uses LanguageTool if available. For Arabic, returns simple heuristics (punctuation, repeated tokens).
    """
    if not student_translation:
        return []
    if lang.startswith("en") and HAVE_LANGTOOL and LANG_TOOL:
        try:
            matches = LANG_TOOL.check(student_translation)
            results = []
            for m in matches[:10]:
                results.append({"message": m.message, "replacements": m.replacements[:3], "offset": m.offset})
            return results
        except Exception:
            pass
    # Arabic / fallback heuristics
    issues = []
    # Check for long run-on sentences (very simple)
    if len(student_translation.split()) > 50:
        issues.append({"message": "Very long sentence — consider splitting for clarity", "replacements": []})
    # repeated punctuation or multiple spaces
    if "  " in student_translation:
        issues.append({"message": "Multiple consecutive spaces", "replacements": ["single space"]})
    if re.search(r"[!?.]{3,}", student_translation):
        issues.append({"message": "Excessive punctuation", "replacements": [".", "!", "?"]})
    return issues

def detect_collocation_issues(student_translation, top_n=3):
    """
    Heuristic: check low-frequency adjacent bigrams in Brown corpus. Returns list of flagged bigrams.
    Requires NLTK Brown corpus; otherwise returns empty list.
    """
    if not HAVE_NLTK:
        return []
    words = re.findall(r"\w+", student_translation.lower())
    if len(words) < 2:
        return []
    bigrams = list(zip(words, words[1:]))
    freqdist = nltk.FreqDist(brown.words())
    warnings = []
    for bg in bigrams:
        # frequency heuristic: if both tokens appear but bigram rare
        bg_freq = sum(1 for _ in brown if False)  # placeholder to avoid heavy calc if needed
    # Simpler: flag rare word combinations using corpus bigram frequency
    from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
    finder = BigramCollocationFinder.from_words(words)
    scored = finder.score_ngrams(BigramAssocMeasures.likelihood_ratio)
    # scored is list of ((w1,w2), score). Lower score -> rarer; pick lowest scorers
    if not scored:
        return []
    scored_sorted = sorted(scored, key=lambda x: x[1])
    flags = [f"{a} {b}" for ((a,b), _s) in scored_sorted[:min(top_n, len(scored_sorted))]]
    return flags

# ------------- CLASSIFIER & HINT MAPPING -------------
def classify_translation_issues(source, student_translation, reference=None, idioms_dict=None, student_lang="en"):
    """
    Runs all detectors and returns a structured report:
    {
      "semantic_score": 85.5,
      "semantic_flag": True/False,
      "idiom_issues": {...},
      "grammar_matches": [...],
      "collocation_flags": [...],
      "priority": ["semantic","idiom","grammar", ...]
    }
    """
    report = {}
    sem = semantic_similarity_score(source, student_translation, reference)
    report["semantic_score"] = sem
    heur_sem_threshold = 65.0
    report["semantic_flag"] = sem < heur_sem_threshold

    idiom_issues = detect_idiomatic_issues(source, student_translation, idioms_dict or {})
    report["idiom_issues"] = idiom_issues

    grammar_matches = detect_fluency_grammar(student_translation, lang=student_lang)
    report["grammar_matches"] = grammar_matches

    colloc = detect_collocation_issues(student_translation)
    report["collocation_flags"] = colloc

    # priority ordering: semantic > idiom > grammar > collocation
    priority = []
    if report["semantic_flag"]:
        priority.append("semantic")
    if idiom_issues:
        priority.append("idiom")
    if grammar_matches:
        priority.append("grammar")
    if colloc:
        priority.append("collocation")
    report["priority"] = priority
    return report

# ------------- SUGGESTIONS / TUTOR MAPPING -------------
def suggest_activities_from_report(report):
    """
    Map detected issues to suggested activities and short hints.
    Returns list of suggestions: {type, short_hint, longer_hint, activity: {type, prompt_id or prompt_text}}
    """
    suggestions = []

    # semantic
    if report.get("semantic_flag"):
        suggestions.append({
            "type": "semantic",
            "short": "Meaning change detected — review key content words.",
            "long": "Your translation may have omitted or changed important meaning. Re-check named entities, negation, modality, and metaphors. Try paraphrasing the source sentence and aligning content words.",
            "activity": {"type":"practice", "category":"semantic", "prompt": "Paraphrase the source preserving meaning; translate both versions and compare."}
        })

    # idiom
    for idiom, info in (report.get("idiom_issues") or {}).items():
        status = info["status"]
        expected = info.get("expected")
        if status == "idiomatic":
            suggestions.append({
                "type":"idiom",
                "short": f"Idiom used correctly: {idiom}",
                "long": f"Good: you used the idiomatic rendering '{expected}'. Keep notes of such equivalents.",
                "activity": {"type":"note", "prompt": f"Add this idiom to your personal idiom bank: {idiom} -> {expected}"}
            })
        else:
            suggestions.append({
                "type":"idiom",
                "short": f"Non-idiomatic rendering of '{idiom}'",
                "long": f"The idiom '{idiom}' appears in the source. Prefer idiomatic Arabic '{expected}' rather than literal translation. Compare both and revise.",
                "activity": {"type":"practice", "category":"idiom", "prompt": f"Translate: '{idiom}' idiomatically into Arabic (expected: {expected})."}
            })

    # grammar
    for gm in report.get("grammar_matches", [])[:5]:
        suggestions.append({
            "type":"grammar",
            "short": "Fluency / grammar issue",
            "long": f"{gm.get('message')}. Suggested edits: {', '.join(gm.get('replacements',[]))}",
            "activity": {"type":"exercise", "category":"grammar", "prompt": gm.get("message")}
        })

    # collocation
    for cf in report.get("collocation_flags", [])[:3]:
        suggestions.append({
            "type":"collocation",
            "short": f"Uncommon collocation: {cf}",
            "long": f"The phrase '{cf}' appears to be uncommon. Consider alternative collocations that are more natural in the target language.",
            "activity": {"type":"practice", "category":"collocation", "prompt": f"Replace the phrase '{cf}' with a natural collocation."}
        })

    # sort: we want highest pedagogical priority first (semantic -> idiom -> grammar -> collocation)
    priority_map = {"semantic":0, "idiom":1, "grammar":2, "collocation":3}
    suggestions_sorted = sorted(suggestions, key=lambda x: priority_map.get(x["type"], 99))
    return suggestions_sorted

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

