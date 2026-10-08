from django.test import TestCase

from .routing import get_specialty, get_urgency

ALL_CODES = ["general_practitioner", "pediatrician", "cardiologist", "dermatologist"]


def make_answers(**changes):
    answers = {
        "reason": "general_checkup",
        "preferred_specialty": "not_sure",
        "duration": "more_than_week",
        "pain_level": 1,
        "red_flags": ["none"],
        "visit_type": "first",
        "preferred_time": "no_preference",
    }
    answers.update(changes)
    return answers


class RoutingTests(TestCase):
    def test_no_symptoms_is_routine(self):
        urgency, reasons = get_urgency(make_answers())
        self.assertEqual(urgency, "routine")

    def test_chest_pain_is_urgent(self):
        urgency, reasons = get_urgency(make_answers(red_flags=["chest_pain"]))
        self.assertEqual(urgency, "urgent")

    def test_high_fever_is_priority(self):
        urgency, reasons = get_urgency(make_answers(red_flags=["high_fever"]))
        self.assertEqual(urgency, "priority")

    def test_strong_pain_is_priority(self):
        urgency, reasons = get_urgency(make_answers(pain_level=4))
        self.assertEqual(urgency, "priority")

    def test_chest_pain_goes_to_cardiologist(self):
        self.assertEqual(get_specialty(make_answers(red_flags=["chest_pain"]), ALL_CODES), "cardiologist")

    def test_preferred_specialty(self):
        self.assertEqual(get_specialty(make_answers(preferred_specialty="dermatologist"), ALL_CODES), "dermatologist")

    def test_not_sure_goes_to_gp(self):
        self.assertEqual(get_specialty(make_answers(), ALL_CODES), "general_practitioner")

    def test_clinic_without_gp(self):
        self.assertEqual(get_specialty(make_answers(), ["pediatrician"]), "pediatrician")
