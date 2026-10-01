"""
Intake questionnaire (8 questions, agreed in TSIS 3).

The definition lives in code (not in the DB) so that routing rules and
questions are versioned together. The frontend renders the form from
GET /api/intake/questions/.
"""

QUESTIONNAIRE_VERSION = 1

SINGLE = "single_choice"
MULTI = "multi_choice"
SCALE = "scale"
TEXT = "text"

QUESTIONS = [
    {
        "key": "reason",
        "text": "What is the main reason for your visit today?",
        "type": SINGLE,
        "required": True,
        "options": [
            {"value": "fever_cold", "label": "Fever / cold"},
            {"value": "injury", "label": "Injury"},
            {"value": "chronic_followup", "label": "Chronic condition follow-up"},
            {"value": "general_checkup", "label": "General checkup"},
            {"value": "other", "label": "Other"},
        ],
    },
    {
        "key": "preferred_specialty",
        "text": "Which specialist would you like to see, if you know?",
        "type": SINGLE,
        "required": True,
        "options": [
            {"value": "general_practitioner", "label": "General practitioner"},
            {"value": "pediatrician", "label": "Pediatrician"},
            {"value": "cardiologist", "label": "Cardiologist"},
            {"value": "dermatologist", "label": "Dermatologist"},
            {"value": "not_sure", "label": "Not sure"},
        ],
    },
    {
        "key": "duration",
        "text": "How long have you had this problem?",
        "type": SINGLE,
        "required": True,
        "options": [
            {"value": "today", "label": "Since today"},
            {"value": "few_days", "label": "A few days"},
            {"value": "more_than_week", "label": "More than a week"},
            {"value": "more_than_month", "label": "More than a month"},
        ],
    },
    {
        "key": "pain_level",
        "text": "On a scale of 1–5, how much discomfort or pain are you feeling right now?",
        "type": SCALE,
        "required": True,
        "min": 1,
        "max": 5,
    },
    {
        "key": "red_flags",
        "text": "Do you currently have any of these symptoms?",
        "type": MULTI,
        "required": True,
        "options": [
            {"value": "high_fever", "label": "High fever"},
            {"value": "difficulty_breathing", "label": "Difficulty breathing"},
            {"value": "chest_pain", "label": "Chest pain"},
            {"value": "severe_bleeding", "label": "Severe bleeding"},
            {"value": "none", "label": "None of these"},
        ],
    },
    {
        "key": "visit_type",
        "text": "Is this your first visit for this problem, or a follow-up?",
        "type": SINGLE,
        "required": True,
        "options": [
            {"value": "first", "label": "First visit"},
            {"value": "follow_up", "label": "Follow-up"},
        ],
    },
    {
        "key": "allergies_or_conditions",
        "text": "Do you have any allergies or chronic conditions we should know about?",
        "type": TEXT,
        "required": False,
        "max_length": 300,
        # Privacy rule from the Charter: we never store health information.
        # The answer is accepted by the API but is NOT persisted.
        "persisted": False,
    },
    {
        "key": "preferred_time",
        "text": "Preferred time for your appointment",
        "type": SINGLE,
        "required": True,
        "options": [
            {"value": "morning", "label": "Morning"},
            {"value": "afternoon", "label": "Afternoon"},
            {"value": "no_preference", "label": "No preference"},
        ],
    },
]

QUESTIONS_BY_KEY = {q["key"]: q for q in QUESTIONS}
NOT_PERSISTED_KEYS = {q["key"] for q in QUESTIONS if q.get("persisted") is False}


def option_values(key):
    return {opt["value"] for opt in QUESTIONS_BY_KEY[key].get("options", [])}
