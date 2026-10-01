"""
Urgency & specialist routing rules (MVP, based on red-flag symptoms).

IMPORTANT: the output is a NON-BINDING suggestion. The system never makes
clinical decisions — reception/medical staff always confirm the urgency
(see Charter risk plan). Rules are not clinically validated yet; they are
to be reviewed with the pilot clinic doctor (Week 6 action).

Everything here is a pure function so it is easy to unit-test and to change
after the clinical review.
"""

from dataclasses import dataclass, field

ROUTINE = "routine"
PRIORITY = "priority"
URGENT = "urgent"

URGENCY_LEVELS = [ROUTINE, PRIORITY, URGENT]
# Lower rank = served first in the queue.
URGENCY_RANK = {URGENT: 0, PRIORITY: 1, ROUTINE: 2}

URGENT_RED_FLAGS = {"difficulty_breathing", "chest_pain", "severe_bleeding"}
EMERGENCY_RED_FLAGS = {"difficulty_breathing", "severe_bleeding"}

DEFAULT_SPECIALTY = "general_practitioner"


@dataclass
class RoutingResult:
    urgency: str
    score: int
    specialty_code: str
    reasons: list = field(default_factory=list)
    # True when the patient should call an ambulance (103) instead of booking.
    emergency_advice: bool = False
    # True when the booking flow should offer the earliest same-day slot.
    offer_earliest_slot: bool = False


def score_urgency(answers):
    """Return (urgency_level, score, reasons)."""
    score = 0
    reasons = []

    red_flags = set(answers.get("red_flags") or []) - {"none"}
    pain = int(answers.get("pain_level") or 1)
    duration = answers.get("duration")

    urgent_flags = red_flags & URGENT_RED_FLAGS
    if urgent_flags:
        score += 10
        reasons.append("Red-flag symptom reported: " + ", ".join(sorted(urgent_flags)).replace("_", " "))

    if "high_fever" in red_flags:
        score += 4
        reasons.append("High fever reported")

    if pain >= 5:
        score += 6
        reasons.append("Severe pain (5/5)")
    elif pain == 4:
        score += 4
        reasons.append("Strong pain (4/5)")
    elif pain == 3:
        score += 1

    if duration == "today" and pain >= 3:
        score += 2
        reasons.append("Sudden onset today with noticeable pain")

    if answers.get("reason") == "injury" and pain >= 3:
        score += 2
        reasons.append("Injury with noticeable pain")

    if score >= 10:
        level = URGENT
    elif score >= 4:
        level = PRIORITY
    else:
        level = ROUTINE
        if not reasons:
            reasons.append("No red-flag symptoms reported")

    return level, score, reasons


def suggest_specialty(answers, available_codes):
    """
    Pick a specialty code from `available_codes` (the clinic's specialties).
    Returns (code, reason).
    """
    available = set(available_codes)
    red_flags = set(answers.get("red_flags") or [])
    preferred = answers.get("preferred_specialty")

    if "chest_pain" in red_flags and "cardiologist" in available:
        return "cardiologist", "Chest pain — cardiologist suggested"

    if preferred and preferred != "not_sure" and preferred in available:
        return preferred, "Patient's preferred specialist"

    if DEFAULT_SPECIALTY in available:
        return DEFAULT_SPECIALTY, "General practitioner is the default first contact"

    # Clinic has no GP — fall back to any specialty so the patient can still book.
    fallback = sorted(available)[0] if available else DEFAULT_SPECIALTY
    return fallback, "Default specialty of this clinic"


def route(answers, available_codes):
    urgency, score, reasons = score_urgency(answers)
    specialty, specialty_reason = suggest_specialty(answers, available_codes)
    red_flags = set(answers.get("red_flags") or [])
    return RoutingResult(
        urgency=urgency,
        score=score,
        specialty_code=specialty,
        reasons=reasons + [specialty_reason],
        emergency_advice=bool(red_flags & EMERGENCY_RED_FLAGS),
        offer_earliest_slot=urgency == URGENT,
    )
