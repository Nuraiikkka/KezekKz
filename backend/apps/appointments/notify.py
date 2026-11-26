from django.utils import timezone

from . import telegram
from .models import Appointment
from .queue import get_queue, get_queue_info


def notify_queue(doctor, day=None):
    day = day or timezone.localdate()
    for appointment in get_queue(doctor, day):
        chat_id = appointment.patient.telegram_chat_id
        if not chat_id or appointment.notified_soon or appointment.status != "booked":
            continue

        position = get_queue_info(appointment)["position"]
        if position is not None and position <= 2:
            text = (
                f"Скоро ваша очередь (№{appointment.queue_number}, кабинет {appointment.doctor.room}). "
                f"Подойдите к клинике.\n{telegram.track_link(appointment)}"
            )
            if telegram.send_message(chat_id, text):
                appointment.notified_soon = True
                appointment.save()


def notify_delay(doctor):
    if doctor.delay_minutes <= 0:
        return
    for appointment in get_queue(doctor, timezone.localdate()):
        chat_id = appointment.patient.telegram_chat_id
        if chat_id:
            text = f"Врач {doctor.full_name} задерживается на {doctor.delay_minutes} мин. Ожидание обновлено.\n{telegram.track_link(appointment)}"
            telegram.send_message(chat_id, text)


def notify_offer(appointment):
    chat_id = appointment.patient.telegram_chat_id
    if chat_id and appointment.offered_slot:
        start = timezone.localtime(appointment.offered_slot.start).strftime("%d.%m %H:%M")
        text = f"Освободилось более раннее время: {start}. Откройте запись и подтвердите.\n{telegram.track_link(appointment)}"
        telegram.send_message(chat_id, text)


def notify_receipt(appointment):
    chat_id = appointment.patient.telegram_chat_id
    if chat_id and hasattr(appointment, "payment"):
        payment = appointment.payment
        text = f"Спасибо за визит! Чек {payment.receipt_number}: {payment.amount} KZT."
        telegram.send_message(chat_id, text)


def notify_bill(appointment):
    chat_id = appointment.patient.telegram_chat_id
    if chat_id and appointment.final_price is not None:
        text = f"Приём завершён. К оплате: {appointment.final_price} KZT. Оплатите на странице визита: {telegram.track_link(appointment)}"
        telegram.send_message(chat_id, text)
