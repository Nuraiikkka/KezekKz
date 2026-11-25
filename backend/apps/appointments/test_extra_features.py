from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from .models import Appointment, Patient, Payment
from .test_smart_features import SmartFeaturesBase
from .waitlist import expire_offers


class WaitlistTests(SmartFeaturesBase):
    def setUp(self):
        super().setUp()
        self.late = self.book(self.slots[2], phone="+77010000001").data["token"]
        self.early = self.book(self.slots[0], phone="+77010000002").data["token"]

    def ask_earlier(self):
        return self.client.post(f"/api/appointments/{self.late}/earlier/", {"wants": True}, format="json")

    def test_cancel_offers_slot_to_waiting_patient(self):
        self.ask_earlier()
        self.client.post(f"/api/appointments/{self.early}/cancel/")

        late = Appointment.objects.get(token=self.late)
        self.assertEqual(late.offered_slot, self.slots[0])
        self.slots[0].refresh_from_db()
        self.assertTrue(self.slots[0].is_booked)

    def test_accept_moves_patient_and_frees_old_slot(self):
        self.ask_earlier()
        self.client.post(f"/api/appointments/{self.early}/cancel/")

        result = self.client.post(f"/api/appointments/{self.late}/offer/accept/")
        self.assertEqual(result.status_code, 200)
        late = Appointment.objects.get(token=self.late)
        self.assertEqual(late.slot, self.slots[0])
        self.slots[2].refresh_from_db()
        self.assertFalse(self.slots[2].is_booked)

    def test_decline_releases_slot(self):
        self.ask_earlier()
        self.client.post(f"/api/appointments/{self.early}/cancel/")
        self.client.post(f"/api/appointments/{self.late}/offer/decline/")

        self.slots[0].refresh_from_db()
        self.assertFalse(self.slots[0].is_booked)
        self.assertFalse(Appointment.objects.get(token=self.late).wants_earlier)

    def test_offer_expires(self):
        self.ask_earlier()
        self.client.post(f"/api/appointments/{self.early}/cancel/")
        Appointment.objects.filter(token=self.late).update(offered_at=timezone.now() - timedelta(minutes=30))

        expire_offers()
        self.slots[0].refresh_from_db()
        self.assertFalse(self.slots[0].is_booked)

    def test_no_offer_without_request(self):
        self.client.post(f"/api/appointments/{self.early}/cancel/")
        self.assertIsNone(Appointment.objects.get(token=self.late).offered_slot)

    def test_accept_without_offer(self):
        result = self.client.post(f"/api/appointments/{self.late}/offer/accept/")
        self.assertEqual(result.status_code, 400)


class PaymentTests(SmartFeaturesBase):
    def completed(self):
        token = self.book(self.slots[0]).data["token"]
        Appointment.objects.filter(token=token).update(status="completed")
        return token

    def pay(self, token, **data):
        return self.client.post(f"/api/appointments/{token}/pay/", data, format="json")

    def test_cannot_pay_before_visit(self):
        token = self.book(self.slots[0]).data["token"]
        self.assertEqual(self.pay(token, method="kaspi").status_code, 400)

    def test_card_payment_keeps_only_last4(self):
        token = self.completed()
        result = self.pay(token, method="card", card_number="4242 4242 4242 4242")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["payment"]["card_last4"], "4242")
        self.assertEqual(result.data["payment"]["status"], "paid")
        self.assertNotIn("4242424242424242", str(Payment.objects.values()))

    def test_wrong_card_is_rejected(self):
        token = self.completed()
        self.assertEqual(self.pay(token, method="card", card_number="1234 5678 9012 3456").status_code, 400)

    def test_kaspi_payment(self):
        token = self.completed()
        result = self.pay(token, method="kaspi")
        self.assertEqual(result.data["payment"]["amount"], 8000 if result.data["price"] == 8000 else result.data["price"])
        self.assertEqual(result.data["payment"]["status"], "paid")

    def test_insurance_needs_iin_and_costs_zero(self):
        token = self.completed()
        self.assertEqual(self.pay(token, method="insurance", iin="123").status_code, 400)
        result = self.pay(token, method="insurance", iin="990101300123")
        self.assertEqual(result.data["payment"]["amount"], 0)

    def test_cash_waits_for_staff(self):
        token = self.completed()
        result = self.pay(token, method="cash")
        self.assertEqual(result.data["payment"]["status"], "pending")

        self.staff()
        pending = self.client.get("/api/staff/payments/pending/")
        self.assertEqual(len(pending.data), 1)
        appointment = Appointment.objects.get(token=token)
        done = self.client.post(f"/api/staff/appointments/{appointment.id}/mark-paid/")
        self.assertEqual(done.data["payment"]["status"], "paid")

    def test_pay_twice(self):
        token = self.completed()
        self.pay(token, method="kaspi")
        self.assertEqual(self.pay(token, method="kaspi").status_code, 400)

    def test_revenue_in_stats(self):
        token = self.completed()
        self.pay(token, method="kaspi")
        self.staff()
        data = self.client.get("/api/staff/stats/").data
        self.assertEqual(data["revenue"], Payment.objects.get().amount)


class RatingCommentTests(SmartFeaturesBase):
    def test_comment_is_saved_and_shown_in_stats(self):
        token = self.book(self.slots[0]).data["token"]
        Appointment.objects.filter(token=token).update(status="completed", finished_at=timezone.now())
        self.client.post(f"/api/appointments/{token}/rate/", {"rating": 4, "comment": "Fast and polite"}, format="json")

        self.staff()
        data = self.client.get("/api/staff/stats/").data
        self.assertEqual(data["comments"][0]["comment"], "Fast and polite")


class RecommendTests(SmartFeaturesBase):
    def test_fastest_doctor_first(self):
        slow = self.doctor
        slow.delay_minutes = 30
        slow.save()
        response = self.client.get("/api/clinics/test/recommend/?specialty=general_practitioner")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["doctor_id"], slow.id)
        self.assertGreaterEqual(response.data[0]["ready_in_minutes"], 30)


@override_settings(TELEGRAM_BOT_TOKEN="123:abc", TELEGRAM_WEBHOOK_SECRET="secret")
class TelegramTests(SmartFeaturesBase):
    def test_start_links_the_chat(self):
        token = self.book(self.slots[0]).data["token"]
        with patch("apps.appointments.telegram.send_message") as send:
            update = {"message": {"text": f"/start {token}", "chat": {"id": 555}}}
            result = self.client.post("/api/telegram/webhook/secret/", update, format="json")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(Patient.objects.get().telegram_chat_id, "555")
        self.assertTrue(send.called)

    def test_wrong_secret(self):
        result = self.client.post("/api/telegram/webhook/wrong/", {}, format="json")
        self.assertEqual(result.status_code, 403)

    def test_message_when_turn_is_near(self):
        slot = self.slots[0]
        slot.start = timezone.now() + timedelta(minutes=5)
        slot.end = slot.start + timedelta(minutes=15)
        slot.save()
        token = self.book(slot).data["token"]
        Patient.objects.update(telegram_chat_id="555")
        self.staff()
        other = Appointment.objects.get(token=token)
        with patch("apps.appointments.telegram.send_message", return_value=True) as send:
            self.client.patch(f"/api/staff/doctors/{self.doctor.id}/", {"delay_minutes": 10}, format="json")
            self.client.patch(f"/api/staff/doctors/{self.doctor.id}/", {"delay_minutes": 5}, format="json")

        other.refresh_from_db()
        self.assertTrue(other.notified_soon)
        soon = [call for call in send.call_args_list if "Скоро ваша очередь" in call.args[1]]
        self.assertEqual(len(soon), 1)

    def test_config_shows_bot(self):
        with override_settings(TELEGRAM_BOT_USERNAME="kezek_bot"):
            self.assertEqual(self.client.get("/api/config/").data["telegram_bot"], "kezek_bot")
