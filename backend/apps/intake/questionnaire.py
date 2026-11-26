SYMPTOMS_DEFAULT = ["cough", "sore_throat", "headache", "weakness", "stomach_pain", "rash", "dizziness", "back_pain"]

SYMPTOMS_BY_SPECIALTY = {
    "general_practitioner": SYMPTOMS_DEFAULT,
    "pediatrician": ["cough", "child_fever", "rash", "stomach_pain", "poor_appetite", "poor_sleep"],
    "cardiologist": ["palpitations", "effort_breathless", "high_pressure", "leg_swelling", "dizziness"],
    "dermatologist": ["rash", "skin_itching", "acne", "hair_loss", "moles", "nail_problem"],
    "proctologist": ["rectal_pain", "blood_in_stool", "anal_itching", "lump", "constipation", "discharge"],
    "neurologist": ["headache", "dizziness", "numbness", "back_pain", "poor_sleep", "tremor"],
    "ent": ["ear_pain", "hearing_loss", "runny_nose", "sore_throat", "nasal_congestion", "cough"],
    "ophthalmologist": ["blurred_vision", "eye_pain", "red_eyes", "dry_eyes", "floaters"],
    "gynecologist": ["pelvic_pain", "irregular_cycle", "discharge", "planning_pregnancy", "checkup"],
    "urologist": ["painful_urination", "frequent_urination", "back_pain", "blood_in_urine"],
    "endocrinologist": ["thirst", "weight_change", "fatigue", "thyroid", "sweating"],
    "gastroenterologist": ["stomach_pain", "heartburn", "nausea", "diarrhea", "bloating", "constipation"],
    "orthopedist": ["joint_pain", "back_pain", "injury_pain", "swelling", "limited_movement"],
}

ALL_SYMPTOMS = sorted({code for codes in SYMPTOMS_BY_SPECIALTY.values() for code in codes})


def options(codes):
    return [{"value": code} for code in codes]


def build_questions(clinic=None):
    specialties = []
    if clinic is not None:
        specialties = [{"value": item.code, "label": item.name} for item in clinic.specialties.all().order_by("id")]
    specialties.append({"value": "not_sure", "label": "Not sure"})

    return [
        {
            "key": "reason",
            "text": "What is the main reason for your visit today?",
            "type": "single_choice",
            "required": True,
            "options": [
                {"value": "fever_cold", "label": "Fever / cold"},
                {"value": "injury", "label": "Injury"},
                {"value": "chronic_followup", "label": "Chronic condition follow-up"},
                {"value": "general_checkup", "label": "General checkup"},
                {"value": "other", "label": "Other"},
            ],
            "followup": {"key": "reason_text", "when": ["other"], "required": True},
        },
        {
            "key": "preferred_specialty",
            "text": "Which specialist would you like to see, if you know?",
            "type": "single_choice",
            "required": True,
            "options": specialties,
        },
        {
            "key": "duration",
            "text": "How long have you had this problem?",
            "type": "single_choice",
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
            "text": "On a scale of 1-5, how much discomfort or pain are you feeling right now?",
            "type": "scale",
            "required": True,
        },
        {
            "key": "red_flags",
            "text": "Do you currently have any of these symptoms?",
            "type": "multi_choice",
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
            "key": "symptoms",
            "text": "Which symptoms bother you?",
            "type": "multi_choice",
            "required": False,
            "depends_on": "preferred_specialty",
            "options": options(SYMPTOMS_DEFAULT),
            "options_by": {code: options(codes) for code, codes in SYMPTOMS_BY_SPECIALTY.items()},
            "followup": {"key": "symptoms_text", "when": None, "required": False},
        },
        {
            "key": "visit_type",
            "text": "Is this your first visit for this problem, or a follow-up?",
            "type": "single_choice",
            "required": True,
            "options": [
                {"value": "first", "label": "First visit"},
                {"value": "follow_up", "label": "Follow-up"},
            ],
        },
        {
            "key": "has_conditions",
            "text": "Do you have any allergies or chronic conditions we should know about?",
            "type": "single_choice",
            "required": True,
            "options": [
                {"value": "no", "label": "No"},
                {"value": "yes", "label": "Yes"},
            ],
            "followup": {"key": "conditions_text", "when": ["yes"], "required": True},
        },
        {
            "key": "preferred_time",
            "text": "Preferred time for your appointment",
            "type": "single_choice",
            "required": True,
            "options": [
                {"value": "morning", "label": "Morning"},
                {"value": "afternoon", "label": "Afternoon"},
                {"value": "no_preference", "label": "No preference"},
            ],
        },
    ]
