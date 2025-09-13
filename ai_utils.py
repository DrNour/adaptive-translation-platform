def generate_feedback(bleu, chrf, semantic, edits, effort):
    feedback = []

    if bleu > 70:
        feedback.append("Great word choice and accurate translation!")
    elif bleu > 40:
        feedback.append("Good, but watch out for literal translations and missing words.")
    else:
        feedback.append("Consider revising key words and sentence structure.")

    if chrf > 70:
        feedback.append("Excellent character-level consistency.")
    elif chrf > 40:
        feedback.append("Check small details like word endings or morphology.")
    else:
        feedback.append("Pay attention to spelling, morphology, and word forms.")

    if semantic > 70:
        feedback.append("Meaning is well-preserved.")
    elif semantic > 40:
        feedback.append("Some meaning may have changed; recheck context.")
    else:
        feedback.append("The translation diverges from the original meaning.")

    if edits < 20 and effort < 20:
        feedback.append("Minimal edits required — very efficient!")
    elif edits < 50:
        feedback.append("Moderate edits needed; focus on improving fluency.")
    else:
        feedback.append("High editing required; review translation strategies.")

    return "\n".join(feedback)

def recommend_practice(metrics):
    weakest = min(metrics, key=metrics.get)
    if weakest in ["BLEU", "Semantic"]:
        return "Focus on translating sentence meaning and word choice."
    elif weakest == "chrF":
        return "Practice paying attention to morphology and spelling."
    elif weakest in ["Edits", "Effort"]:
        return "Try editing machine translations more efficiently."
    else:
        return "Keep practicing to improve all areas."
