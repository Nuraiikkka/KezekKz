from datetime import datetime, timedelta

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clinics.models import Clinic, Doctor, TimeSlot

from .models import PAYABLE_STATUSES, Appointment, Patient, Payment, TelegramLogin
from . import telegram
from .notify import notify_bill, notify_queue, notify_receipt
from .payments import create_payment
from .queue import get_queue, get_visit_minutes, next_queue_number
from .serializers import (
    AppointmentSerializer,
    BookingSerializer,
    EarlierSerializer,
    MoveSerializer,
    PaySerializer,
    RatingSerializer,
    StaffAppointmentSerializer,
    StaffPaySerializer,
    StaffUpdateSerializer,
)
from .waitlist import accept_offer, expire_offers, free_slot, release_offer


class AppointmentCreateView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "booking"

    @extend_schema(request=BookingSerializer, responses=AppointmentSerializer)
    def post(self, request):
        serializer = BookingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(AppointmentSerializer(appointment).data, status=201)


class AppointmentDetailView(generics.RetrieveAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    lookup_field = "token"

    def get(self, request, *args, **kwargs):
        expire_offers()
        return super().get(request, *args, **kwargs)


class AppointmentCancelView(APIView):
    @extend_schema(request=None, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can be cancelled."]}, status=400)

        appointment.status = "cancelled"
        appointment.wants_earlier = False
        appointment.save()
        if appointment.offered_slot is not None:
            release_offer(appointment)
        free_slot(appointment.slot)
        notify_queue(appointment.doctor, timezone.localtime(appointment.slot.start).date())
        return Response(AppointmentSerializer(appointment).data)


class AppointmentMoveView(APIView):
    @extend_schema(request=MoveSerializer, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can be moved."]}, status=400)

        serializer = MoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_slot = TimeSlot.objects.filter(id=serializer.validated_data["slot_id"]).first()
        if new_slot is None:
            return Response({"slot_id": ["Slot not found."]}, status=400)
        if new_slot.id == appointment.slot_id:
            return Response({"slot_id": ["This is your current time."]}, status=400)
        if new_slot.is_booked or new_slot.start < timezone.now():
            return Response({"slot_id": ["This slot is not free anymore."]}, status=400)
        if new_slot.doctor.clinic_id != appointment.doctor.clinic_id or new_slot.doctor.specialty.code != appointment.doctor.specialty.code:
            return Response({"slot_id": ["This slot is for another specialist."]}, status=400)

        old_slot = appointment.slot
        old_doctor = appointment.doctor
        new_slot.is_booked = True
        new_slot.save()
        if appointment.offered_slot is not None:
            release_offer(appointment)

        appointment.doctor = new_slot.doctor
        appointment.slot = new_slot
        appointment.queue_number = next_queue_number(new_slot.doctor, new_slot.start)
        appointment.wants_earlier = False
        appointment.notified_soon = False
        appointment.save()
        free_slot(old_slot)

        notify_queue(old_doctor, timezone.localtime(old_slot.start).date())
        notify_queue(appointment.doctor, timezone.localtime(new_slot.start).date())
        return Response(AppointmentSerializer(appointment).data)


class AppointmentRateView(APIView):
    @extend_schema(request=RatingSerializer, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "completed":
            return Response({"status": ["You can rate a visit after it is completed."]}, status=400)

        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.rating = serializer.validated_data["rating"]
        appointment.rating_comment = serializer.validated_data.get("comment", "")
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


class AppointmentConfirmView(APIView):
    @extend_schema(request=None, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can be confirmed."]}, status=400)

        appointment.patient_confirmed = True
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


class AppointmentArriveView(APIView):
    @extend_schema(request=None, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can be checked in."]}, status=400)
        if appointment.slot.start - timezone.now() > timedelta(minutes=60):
            return Response({"status": ["You can check in 60 minutes before your time."]}, status=400)

        appointment.status = "checked_in"
        appointment.patient_confirmed = True
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


SENSITIVE_SPECIALTIES = ["proctologist", "gynecologist", "urologist"]


class BoardView(APIView):
    @extend_schema(responses=dict)
    def get(self, request, slug):
        clinic = get_object_or_404(Clinic, slug=slug)
        today = timezone.localdate()

        rows = []
        for doctor in Doctor.objects.filter(clinic=clinic).select_related("specialty"):
            queue = list(get_queue(doctor, today))
            serving = [item.queue_number for item in queue if item.status == "in_progress"]
            waiting = [item.queue_number for item in queue if item.status != "in_progress"]
            sensitive = doctor.specialty.code in SENSITIVE_SPECIALTIES
            rows.append(
                {
                    "doctor": "" if sensitive else doctor.full_name,
                    "specialty": "" if sensitive else doctor.specialty.name,
                    "specialty_code": "" if sensitive else doctor.specialty.code,
                    "sensitive": sensitive,
                    "room": doctor.room,
                    "delay_minutes": doctor.delay_minutes,
                    "now_serving": serving[0] if serving else None,
                    "next": waiting[:4],
                    "waiting": len(waiting),
                }
            )
        return Response(rows)


class StaffStatsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=dict)
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)
        appointments = Appointment.objects.filter(slot__start__gte=since, slot__start__lte=timezone.now() + timedelta(days=1))

        total = appointments.count()
        completed = appointments.filter(status="completed")
        no_shows = appointments.filter(status="no_show").count()
        cancelled = appointments.filter(status="cancelled").count()
        finished = completed.count() + no_shows
        rating = appointments.filter(rating__isnull=False).aggregate(avg=Avg("rating"), count=Count("id"))

        delays = []
        for item in completed.filter(started_at__isnull=False).select_related("slot"):
            delays.append(max(0, (item.started_at - item.slot.start).total_seconds() / 60))

        by_doctor = []
        for doctor in Doctor.objects.all().select_related("specialty"):
            done = completed.filter(doctor=doctor)
            visit_minutes, real = get_visit_minutes(doctor)
            avg_rating = done.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
            by_doctor.append(
                {
                    "doctor": doctor.full_name,
                    "specialty": doctor.specialty.name,
                    "completed": done.count(),
                    "visit_minutes": visit_minutes,
                    "real_data": real,
                    "rating": round(avg_rating, 1) if avg_rating else None,
                }
            )

        hours = {}
        for item in appointments.exclude(status="cancelled").select_related("slot"):
            hour = timezone.localtime(item.slot.start).hour
            hours[hour] = hours.get(hour, 0) + 1

        paid = Payment.objects.filter(appointment__in=appointments, status="paid")
        methods = {}
        for item in paid:
            methods[item.method] = methods.get(item.method, 0) + item.amount
        comments = [
            {"rating": item.rating, "comment": item.rating_comment, "doctor": item.doctor.full_name}
            for item in appointments.exclude(rating_comment="").order_by("-finished_at")[:5]
        ]

        return Response(
            {
                "days": days,
                "revenue": sum(methods.values()),
                "by_method": [{"method": key, "amount": value} for key, value in methods.items()],
                "comments": comments,
                "total": total,
                "completed": completed.count(),
                "cancelled": cancelled,
                "no_show": no_shows,
                "no_show_rate": round(no_shows * 100 / finished) if finished else 0,
                "avg_rating": round(rating["avg"], 1) if rating["avg"] else None,
                "rating_count": rating["count"],
                "avg_delay_minutes": round(sum(delays) / len(delays)) if delays else 0,
                "by_doctor": by_doctor,
                "by_hour": [{"hour": hour, "count": hours[hour]} for hour in sorted(hours)],
            }
        )


class AppointmentEarlierView(APIView):
    @extend_schema(request=EarlierSerializer, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can ask for an earlier time."]}, status=400)

        serializer = EarlierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.wants_earlier = serializer.validated_data["wants"]
        appointment.save()
        if appointment.offered_slot is not None and not appointment.wants_earlier:
            release_offer(appointment)
        return Response(AppointmentSerializer(appointment).data)


class AppointmentOfferView(APIView):
    accept = True

    @extend_schema(request=None, responses=AppointmentSerializer)
    def post(self, request, token):
        expire_offers()
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.offered_slot is None:
            return Response({"offer": ["There is no offer or it has expired."]}, status=400)

        if self.accept:
            appointment = accept_offer(appointment)
            notify_queue(appointment.doctor, timezone.localtime(appointment.slot.start).date())
        else:
            appointment.wants_earlier = False
            release_offer(appointment)
        return Response(AppointmentSerializer(appointment).data)


class AppointmentDeclineView(AppointmentOfferView):
    accept = False


class AppointmentPayView(APIView):
    @extend_schema(request=PaySerializer, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status not in PAYABLE_STATUSES or appointment.final_price is None:
            return Response({"status": ["You can pay after the doctor finishes the visit and sets the price."]}, status=400)
        if Payment.objects.filter(appointment=appointment).exists():
            return Response({"payment": ["This visit is already paid or waiting for payment."]}, status=400)

        serializer = PaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        create_payment(appointment, data["method"], data.get("card_number", ""), data.get("iin", ""))
        appointment.refresh_from_db()
        notify_receipt(appointment)
        return Response(AppointmentSerializer(appointment).data)


class StaffPayView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=StaffPaySerializer, responses=StaffAppointmentSerializer)
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, id=pk)
        if appointment.status not in PAYABLE_STATUSES or appointment.final_price is None:
            return Response({"status": ["Finish the visit and set the price first."]}, status=400)
        if Payment.objects.filter(appointment=appointment).exists():
            return Response({"payment": ["This visit already has a payment."]}, status=400)

        serializer = StaffPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        create_payment(appointment, data["method"], iin=data.get("iin", ""), cashier=True)
        appointment.refresh_from_db()
        notify_receipt(appointment)
        return Response(StaffAppointmentSerializer(appointment).data)


class StaffMarkPaidView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=None, responses=StaffAppointmentSerializer)
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, id=pk)
        payment = get_object_or_404(Payment, appointment=appointment)
        payment.status = "paid"
        payment.paid_at = timezone.now()
        payment.save()
        notify_receipt(appointment)
        return Response(StaffAppointmentSerializer(appointment).data)


class StaffPendingPaymentsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=StaffAppointmentSerializer(many=True))
    def get(self, request):
        appointments = Appointment.objects.filter(payment__status="pending").select_related("payment")
        return Response(StaffAppointmentSerializer(appointments, many=True).data)


class RecommendView(APIView):
    @extend_schema(responses=dict)
    def get(self, request, slug):
        expire_offers()
        clinic = get_object_or_404(Clinic, slug=slug)
        now = timezone.now()

        rows = []
        for doctor in Doctor.objects.filter(clinic=clinic, specialty__code=request.query_params.get("specialty")):
            slot = doctor.slots.filter(is_booked=False, start__gt=now).first()
            if slot is None:
                continue
            visit_minutes, real = get_visit_minutes(doctor)
            ready = max(0, int((slot.start - now).total_seconds() // 60)) + doctor.delay_minutes
            rows.append(
                {
                    "doctor_id": doctor.id,
                    "doctor": doctor.full_name,
                    "room": doctor.room,
                    "delay_minutes": doctor.delay_minutes,
                    "visit_minutes": visit_minutes,
                    "real_data": real,
                    "slot_id": slot.id,
                    "slot_start": slot.start,
                    "ready_in_minutes": ready,
                }
            )
        rows.sort(key=lambda row: row["ready_in_minutes"])
        return Response(rows)


class ConfigView(APIView):
    @extend_schema(responses=dict)
    def get(self, request):
        return Response({"telegram_bot": settings.TELEGRAM_BOT_USERNAME or None})


class TelegramWebhookView(APIView):
    @extend_schema(request=dict, responses=dict)
    def post(self, request, secret):
        if secret != settings.TELEGRAM_WEBHOOK_SECRET:
            return Response(status=403)

        message = request.data.get("message") or {}
        text = message.get("text", "")
        chat_id = str((message.get("chat") or {}).get("id", ""))
        contact = message.get("contact")

        if contact and chat_id:
            self.finish_login(message, chat_id, contact)
        elif text.startswith("/start login_") and chat_id:
            self.ask_for_contact(chat_id, text.split("login_", 1)[1].strip())
        elif text.startswith("/start") and chat_id:
            parts = text.split()
            appointment = None
            if len(parts) > 1:
                try:
                    appointment = Appointment.objects.filter(token=parts[1]).first()
                except Exception:
                    appointment = None

            if appointment is not None:
                appointment.patient.telegram_chat_id = chat_id
                appointment.patient.save()
                reply = f"Готово! Буду писать вам про очередь. Номер {appointment.queue_number}, кабинет {appointment.doctor.room}."
            else:
                reply = f"Здравствуйте! Это бот KezekKz. Чтобы войти в профиль или получать сообщения об очереди, откройте сайт {settings.FRONTEND_URL} и нажмите «Войти через Telegram» или «Подключить Telegram»."
            telegram.send_message(chat_id, reply)
        return Response({"ok": True})

    def ask_for_contact(self, chat_id, nonce):
        login = TelegramLogin.objects.filter(nonce=nonce).first()
        if login is None:
            telegram.send_message(chat_id, "Ссылка устарела. Вернитесь на сайт и начните вход заново.")
            return
        login.chat_id = chat_id
        login.save()
        keyboard = {
            "keyboard": [[{"text": "Поделиться номером", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        telegram.send_message(chat_id, "Чтобы войти в профиль, поделитесь своим номером телефона кнопкой ниже.", keyboard)

    def finish_login(self, message, chat_id, contact):
        sender = (message.get("from") or {}).get("id")
        if contact.get("user_id") != sender:
            telegram.send_message(chat_id, "Нужно поделиться своим номером, а не чужим.")
            return

        digits = "".join(char for char in str(contact.get("phone_number", "")) if char.isdigit())
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        phone = "+" + digits
        login = (
            TelegramLogin.objects.filter(chat_id=chat_id, patient__isnull=True)
            .filter(created_at__gte=timezone.now() - timedelta(minutes=10))
            .order_by("-created_at")
            .first()
        )
        if login is None or len(phone) != 12 or not phone.startswith("+7"):
            telegram.send_message(chat_id, "Не получилось войти. Вернитесь на сайт и начните заново.")
            return

        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Patient"
        patient, created = Patient.objects.get_or_create(phone=phone, defaults={"full_name": name})
        patient.telegram_chat_id = chat_id
        patient.save()
        login.patient = patient
        login.save()
        telegram.send_message(chat_id, "Готово! Вернитесь на сайт, вход выполнен.", {"remove_keyboard": True})


class StaffQueueView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=StaffAppointmentSerializer(many=True))
    def get(self, request):
        doctor = get_object_or_404(Doctor, id=request.query_params.get("doctor"))

        date = request.query_params.get("date")
        if date:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            day = timezone.localdate()

        appointments = get_queue(doctor, day)
        return Response(StaffAppointmentSerializer(appointments, many=True).data)


class StaffAppointmentUpdateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=StaffUpdateSerializer, responses=StaffAppointmentSerializer)
    def patch(self, request, pk):
        appointment = get_object_or_404(Appointment, id=pk)
        serializer = StaffUpdateSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get("status", appointment.status)
        new_price = serializer.validated_data.get("final_price")
        if new_price is not None and new_status != "completed":
            return Response({"final_price": ["Set the price after the visit is completed."]}, status=400)
        if new_price is not None and Payment.objects.filter(appointment=appointment).exists():
            return Response({"final_price": ["This visit is already paid."]}, status=400)
        appointment = serializer.save()

        now = timezone.now()
        status = request.data.get("status")
        if status == "in_progress" and appointment.started_at is None:
            appointment.started_at = now
        if status == "completed":
            if appointment.started_at is None:
                appointment.started_at = now
            appointment.finished_at = now
        appointment.save()

        if "urgency" in request.data:
            appointment.urgency_confirmed = True
            appointment.save()

        if appointment.status in ["cancelled", "no_show"]:
            free_slot(appointment.slot)

        if "final_price" in request.data and appointment.final_price is not None:
            notify_bill(appointment)

        notify_queue(appointment.doctor, timezone.localtime(appointment.slot.start).date())

        return Response(StaffAppointmentSerializer(appointment).data)
