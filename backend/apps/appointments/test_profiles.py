from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from .models import Appointment, MedicalRecord, Patient
from .test_smart_features import SmartFeaturesBase


class ProfileTests(SmartFeaturesBase):
    def book_with_pin(self, phone="+77011234567", pin="4321"):
        token = self.book(self.slots[0], phone=phone).data["token"]
        result = self.client.post("/api/patient/pin/", {"token": token, "pin": pin}, format="json")
        return token, result

    def test_pin_is_set_from_a_booking(self):
        token, result = self.book_with_pin()
        self.assertEqual(result.status_code, 201)
        self.assertTrue(result.data["token"])
        self.assertEqual(len(result.data["visits"]), 1)
        self.assertNotIn("4321", Patient.objects.get().pin_hash)

    def test_pin_cannot_be_changed_by_a_second_booking(self):
        token, _ = self.book_with_pin()
        again = self.client.post("/api/patient/pin/", {"token": token, "pin": "1111"}, format="json")
        self.assertEqual(again.status_code, 400)

    def test_bad_pin(self):
        token = self.book(self.slots[0]).data["token"]
        for pin in ["12", "abcd", "1234567"]:
            result = self.client.post("/api/patient/pin/", {"token": token, "pin": pin}, format="json")
            self.assertEqual(result.status_code, 400)

    def test_login(self):
        self.book_with_pin()
        good = self.client.post("/api/patient/login/", {"phone": "8 701 123 45 67", "pin": "4321"}, format="json")
        self.assertEqual(good.status_code, 200)
        bad = self.client.post("/api/patient/login/", {"phone": "+77011234567", "pin": "0000"}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_me_needs_login_and_shows_only_own_visits(self):
        _, mine = self.book_with_pin(phone="+77011234567")
        self.book(self.slots[1], phone="+77019999999")

        self.assertEqual(self.client.get("/api/patient/me/").status_code, 401)
        result = self.client.get("/api/patient/me/", HTTP_X_PATIENT_TOKEN=mine.data["token"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data["visits"]), 1)
        self.assertEqual(result.data["profile"]["phone"], "+77011234567")

    def test_patient_edits_the_profile(self):
        _, session = self.book_with_pin()
        header = {"HTTP_X_PATIENT_TOKEN": session.data["token"]}
        result = self.client.patch(
            "/api/patient/me/", {"conditions": "Penicillin allergy", "birth_date": "1995-05-20"}, format="json", **header
        )
        self.assertEqual(result.data["profile"]["conditions"], "Penicillin allergy")
        self.assertEqual(result.data["profile"]["phone"], "+77011234567")

    def test_conditions_from_the_questionnaire_go_to_the_profile(self):
        intake = self.make_intake(has_conditions="yes", conditions_text="Asthma")
        self.book(self.slots[0], intake_id=intake)
        self.assertEqual(Patient.objects.get().conditions, "Asthma")

    def test_last_visit_is_the_last_completed_one(self):
        token, session = self.book_with_pin()
        Appointment.objects.filter(token=token).update(status="completed")
        result = self.client.get("/api/patient/me/", HTTP_X_PATIENT_TOKEN=session.data["token"])
        self.assertIsNotNone(result.data["last_visit"])


class StaffCardTests(SmartFeaturesBase):
    def test_staff_sees_the_whole_card_and_adds_records(self):
        token = self.book(self.slots[0]).data["token"]
        patient = Patient.objects.get()
        self.staff()

        found = self.client.get("/api/staff/patients/?q=Aru")
        self.assertEqual(len(found.data), 1)

        added = self.client.post(
            f"/api/staff/patients/{patient.id}/records/",
            {"kind": "analysis", "title": "Blood test", "text": "Hemoglobin 140"},
            format="json",
        )
        self.assertEqual(added.status_code, 201)
        card = self.client.get(f"/api/staff/patients/{patient.id}/")
        self.assertEqual(card.data["records"][0]["title"], "Blood test")
        self.assertEqual(card.data["records"][0]["author"], "nurse")
        self.assertEqual(card.data["visits"][0]["token"], token)
        self.assertIn("intake_summary", card.data["visits"][0])

    def test_patient_sees_the_records(self):
        token = self.book(self.slots[0]).data["token"]
        session = self.client.post("/api/patient/pin/", {"token": token, "pin": "4321"}, format="json")
        patient = Patient.objects.get()
        MedicalRecord.objects.create(patient=patient, title="Prescription", kind="prescription", text="Vitamin D")

        result = self.client.get("/api/patient/me/", HTTP_X_PATIENT_TOKEN=session.data["token"])
        self.assertEqual(result.data["records"][0]["title"], "Prescription")

    def test_card_is_closed_for_patients(self):
        self.book(self.slots[0])
        patient = Patient.objects.get()
        self.assertEqual(self.client.get(f"/api/staff/patients/{patient.id}/").status_code, 401)
        self.assertEqual(self.client.get("/api/staff/patients/").status_code, 401)

    def test_record_of_another_patient_visit_is_rejected(self):
        first = self.book(self.slots[0], phone="+77010000001").data["token"]
        self.book(self.slots[1], phone="+77010000002")
        other = Patient.objects.get(phone="+77010000002")
        self.staff()
        result = self.client.post(
            f"/api/staff/patients/{other.id}/records/",
            {"title": "x", "appointment": Appointment.objects.get(token=first).id},
            format="json",
        )
        self.assertEqual(result.status_code, 400)


class PaymentAtCheckInTests(SmartFeaturesBase):
    def checked_in(self):
        token = self.book(self.slots[0]).data["token"]
        appointment = Appointment.objects.get(token=token)
        Appointment.objects.filter(token=token).update(status="completed", final_price=appointment.doctor.specialty.price)
        return token, Appointment.objects.get(token=token)

    def test_patient_can_pay_after_check_in(self):
        token, _ = self.checked_in()
        result = self.client.post(f"/api/appointments/{token}/pay/", {"method": "apple_pay"}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["payment"]["method"], "apple_pay")
        self.assertEqual(result.data["payment"]["status"], "paid")

    def test_cannot_pay_before_check_in(self):
        token = self.book(self.slots[0]).data["token"]
        result = self.client.post(f"/api/appointments/{token}/pay/", {"method": "google_pay"}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_staff_takes_cash_at_the_cashier(self):
        _, appointment = self.checked_in()
        self.staff()
        result = self.client.post(f"/api/staff/appointments/{appointment.id}/pay/", {"method": "cash"}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["payment"]["status"], "paid")

    def test_staff_takes_card_from_the_terminal(self):
        _, appointment = self.checked_in()
        self.staff()
        result = self.client.post(f"/api/staff/appointments/{appointment.id}/pay/", {"method": "card"}, format="json")
        self.assertEqual(result.data["payment"]["method"], "card")

    def test_staff_cannot_charge_a_patient_who_did_not_come(self):
        token = self.book(self.slots[0]).data["token"]
        appointment = Appointment.objects.get(token=token)
        self.staff()
        result = self.client.post(f"/api/staff/appointments/{appointment.id}/pay/", {"method": "cash"}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_staff_pay_is_closed_for_patients(self):
        _, appointment = self.checked_in()
        result = self.client.post(f"/api/staff/appointments/{appointment.id}/pay/", {"method": "cash"}, format="json")
        self.assertEqual(result.status_code, 401)


class CorsTests(SmartFeaturesBase):
    def test_browser_may_send_the_patient_token_header(self):
        response = self.client.options(
            "/api/patient/me/",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-patient-token",
        )
        self.assertIn("x-patient-token", response["Access-Control-Allow-Headers"])


class RegistrationTests(SmartFeaturesBase):
    def register(self, **data):
        body = {"full_name": "New Person", "phone": "8 701 555 00 01", "pin": "2468"}
        body.update(data)
        return self.client.post("/api/patient/register/", body, format="json")

    def test_register_without_a_booking(self):
        result = self.register()
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["profile"]["phone"], "+77015550001")
        self.assertEqual(result.data["visits"], [])

        login = self.client.post("/api/patient/login/", {"phone": "+77015550001", "pin": "2468"}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_second_registration_with_the_same_phone_is_rejected(self):
        self.register()
        self.assertEqual(self.register(pin="1357").status_code, 400)

    def test_register_picks_up_old_bookings(self):
        self.book(self.slots[0], phone="+77015550001")
        result = self.register()
        self.assertEqual(len(result.data["visits"]), 1)

    def test_register_checks_the_pin_and_phone(self):
        self.assertEqual(self.register(pin="12").status_code, 400)
        self.assertEqual(self.register(phone="123").status_code, 400)


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_BOT_USERNAME="kezek_bot", TELEGRAM_WEBHOOK_SECRET="secret")
class TelegramLoginTests(SmartFeaturesBase):
    def webhook(self, message):
        return self.client.post("/api/telegram/webhook/secret/", {"message": message}, format="json")

    def start(self):
        return self.client.post("/api/patient/telegram/start/").data

    def test_full_login_through_telegram(self):
        started = self.start()
        self.assertIn(f"login_{started['nonce']}", started["link"])
        self.assertEqual(
            self.client.post("/api/patient/telegram/check/", {"nonce": started["nonce"]}, format="json").data, {"waiting": True}
        )

        with patch("apps.appointments.telegram.send_message") as send:
            self.webhook({"text": f"/start login_{started['nonce']}", "chat": {"id": 900}, "from": {"id": 900}})
            keyboard = send.call_args.args[2]
            self.assertTrue(keyboard["keyboard"][0][0]["request_contact"])

            self.webhook(
                {
                    "chat": {"id": 900},
                    "from": {"id": 900},
                    "contact": {"phone_number": "77015550002", "first_name": "Aru", "user_id": 900},
                }
            )

        result = self.client.post("/api/patient/telegram/check/", {"nonce": started["nonce"]}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["profile"]["phone"], "+77015550002")
        self.assertTrue(result.data["token"])
        self.assertEqual(Patient.objects.get(phone="+77015550002").telegram_chat_id, "900")

    def test_someone_elses_contact_is_rejected(self):
        started = self.start()
        with patch("apps.appointments.telegram.send_message"):
            self.webhook({"text": f"/start login_{started['nonce']}", "chat": {"id": 901}, "from": {"id": 901}})
            self.webhook(
                {"chat": {"id": 901}, "from": {"id": 901}, "contact": {"phone_number": "77015550003", "user_id": 12345}}
            )
        self.assertFalse(Patient.objects.filter(phone="+77015550003").exists())

    def test_old_booking_history_is_open_after_the_telegram_login(self):
        self.book(self.slots[0], phone="+77015550004")
        started = self.start()
        with patch("apps.appointments.telegram.send_message"):
            self.webhook({"text": f"/start login_{started['nonce']}", "chat": {"id": 902}, "from": {"id": 902}})
            self.webhook(
                {"chat": {"id": 902}, "from": {"id": 902}, "contact": {"phone_number": "+77015550004", "user_id": 902}}
            )
        result = self.client.post("/api/patient/telegram/check/", {"nonce": started["nonce"]}, format="json")
        self.assertEqual(len(result.data["visits"]), 1)

    def test_login_is_closed_when_the_bot_is_not_set_up(self):
        with override_settings(TELEGRAM_BOT_USERNAME=""):
            self.assertEqual(self.client.post("/api/patient/telegram/start/").status_code, 400)

    def test_unknown_nonce(self):
        result = self.client.post("/api/patient/telegram/check/", {"nonce": "nope"}, format="json")
        self.assertEqual(result.status_code, 400)


class ForgotPinTests(SmartFeaturesBase):
    def setUp(self):
        super().setUp()
        token = self.book(self.slots[0]).data["token"]
        self.session = self.client.post("/api/patient/pin/", {"token": token, "pin": "4321"}, format="json").data
        self.patient = Patient.objects.get()

    def test_logged_in_patient_changes_the_pin(self):
        header = {"HTTP_X_PATIENT_TOKEN": self.session["token"]}
        result = self.client.post("/api/patient/me/pin/", {"pin": "9999"}, format="json", **header)
        self.assertEqual(result.status_code, 200)
        old = self.client.post("/api/patient/login/", {"phone": "+77011234567", "pin": "4321"}, format="json")
        new = self.client.post("/api/patient/login/", {"phone": "+77011234567", "pin": "9999"}, format="json")
        self.assertEqual(old.status_code, 400)
        self.assertEqual(new.status_code, 200)

    def test_pin_change_needs_login_and_a_good_pin(self):
        self.assertEqual(self.client.post("/api/patient/me/pin/", {"pin": "9999"}, format="json").status_code, 401)
        header = {"HTTP_X_PATIENT_TOKEN": self.session["token"]}
        self.assertEqual(self.client.post("/api/patient/me/pin/", {"pin": "1"}, format="json", **header).status_code, 400)

    def test_staff_resets_the_pin_and_the_old_session_stops_working(self):
        self.staff()
        result = self.client.post(f"/api/staff/patients/{self.patient.id}/reset-pin/")
        self.assertEqual(result.status_code, 200)
        self.client.credentials()

        old = self.client.get("/api/patient/me/", HTTP_X_PATIENT_TOKEN=self.session["token"])
        self.assertEqual(old.status_code, 401)
        login = self.client.post("/api/patient/login/", {"phone": "+77011234567", "pin": "4321"}, format="json")
        self.assertEqual(login.status_code, 400)

        again = self.client.post(
            "/api/patient/register/", {"full_name": "Aru", "phone": "+77011234567", "pin": "5555"}, format="json"
        )
        self.assertEqual(again.status_code, 201)

    def test_reset_is_closed_for_patients(self):
        result = self.client.post(f"/api/staff/patients/{self.patient.id}/reset-pin/")
        self.assertEqual(result.status_code, 401)


class LastVisitTests(SmartFeaturesBase):
    def test_visit_counts_from_the_moment_the_patient_came(self):
        token = self.book(self.slots[0]).data["token"]
        session = self.client.post("/api/patient/pin/", {"token": token, "pin": "4321"}, format="json")
        header = {"HTTP_X_PATIENT_TOKEN": session.data["token"]}
        self.assertIsNone(self.client.get("/api/patient/me/", **header).data["last_visit"])

        Appointment.objects.filter(token=token).update(status="checked_in")
        self.assertIsNotNone(self.client.get("/api/patient/me/", **header).data["last_visit"])

    def test_cancelled_visit_is_not_a_visit(self):
        token = self.book(self.slots[0]).data["token"]
        session = self.client.post("/api/patient/pin/", {"token": token, "pin": "4321"}, format="json")
        Appointment.objects.filter(token=token).update(status="cancelled")
        result = self.client.get("/api/patient/me/", HTTP_X_PATIENT_TOKEN=session.data["token"])
        self.assertIsNone(result.data["last_visit"])


class DoctorSetsPriceTests(SmartFeaturesBase):
    def setUp(self):
        super().setUp()
        self.token = self.book(self.slots[0]).data["token"]
        self.appointment = Appointment.objects.get(token=self.token)

    def test_no_payment_before_the_doctor_sets_the_price(self):
        Appointment.objects.filter(token=self.token).update(status="completed")
        result = self.client.post(f"/api/appointments/{self.token}/pay/", {"method": "kaspi"}, format="json")
        self.assertEqual(result.status_code, 400)
        self.assertFalse(self.client.get(f"/api/appointments/{self.token}/").data["billed"])

    def test_checked_in_patient_cannot_pay_yet(self):
        Appointment.objects.filter(token=self.token).update(status="checked_in")
        result = self.client.post(f"/api/appointments/{self.token}/pay/", {"method": "kaspi"}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_doctor_sets_price_after_the_visit_and_patient_pays_it(self):
        self.staff()
        result = self.client.patch(
            f"/api/staff/appointments/{self.appointment.id}/", {"status": "completed", "final_price": 12500}, format="json"
        )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data["billed"])
        self.assertEqual(result.data["price"], 12500)

        self.client.credentials()
        paid = self.client.post(f"/api/appointments/{self.token}/pay/", {"method": "kaspi"}, format="json")
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data["payment"]["amount"], 12500)

    def test_price_cannot_be_set_before_the_visit_is_completed(self):
        self.staff()
        result = self.client.patch(f"/api/staff/appointments/{self.appointment.id}/", {"final_price": 9000}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_price_cannot_be_negative(self):
        self.staff()
        result = self.client.patch(
            f"/api/staff/appointments/{self.appointment.id}/", {"status": "completed", "final_price": -1}, format="json"
        )
        self.assertEqual(result.status_code, 400)
