RED_FLAGS = ["difficulty_breathing", "chest_pain", "severe_bleeding"]


def get_urgency(answers):
    red_flags = answers.get("red_flags", [])
    pain = answers.get("pain_level", 1)

    reasons = []
    for flag in red_flags:
        if flag in RED_FLAGS:
            reasons.append("Red flag symptom: " + flag.replace("_", " "))
    if reasons:
        return "urgent", reasons

    if "high_fever" in red_flags:
        reasons.append("High fever")
    if pain >= 4:
        reasons.append("Strong pain")
    if reasons:
        return "priority", reasons

    return "routine", ["No red flag symptoms"]


def get_specialty(answers, codes):
    if "chest_pain" in answers.get("red_flags", []) and "cardiologist" in codes:
        return "cardiologist"

    preferred = answers.get("preferred_specialty")
    if preferred in codes:
        return preferred

    if "general_practitioner" in codes:
        return "general_practitioner"
    return codes[0]


def need_emergency(answers):
    red_flags = answers.get("red_flags", [])
    return "difficulty_breathing" in red_flags or "severe_bleeding" in red_flags
