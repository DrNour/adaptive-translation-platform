# Simple placeholder functions for motivational feedback and hints

def provide_motivational_feedback(points, streak):
    if points < 20:
        return "Keep going! Every translation counts 📝"
    elif points < 50:
        return "Great job! Try to maintain your streak 🔥"
    else:
        return "Amazing! You are on fire! 🚀"

def suggest_translation_corrections(reference, student_translation, error_pattern=None):
    # Dummy hints: replace with NLP checks or Levenshtein-based hints
    hints = []
    if error_pattern:
        if error_pattern.get("avg_bleu",0) < 50:
            hints.append("Check your word choices and sentence structure.")
        if error_pattern.get("avg_edits",0) > 20:
            hints.append("Try to reduce unnecessary edits and simplify sentences.")
    return hints
