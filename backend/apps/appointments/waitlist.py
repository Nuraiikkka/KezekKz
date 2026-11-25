from datetime import timedelta

from django.utils import timezone

from .models import Appointment
from .notify import notify_offer
from .queue import next_queue_number

OFFER_MINUTES = 10


def offer_to_next(slot):
    if slot.start <= timezone.now():
        return None

    candidate = (
        Appointment.objects.filter(
            doctor__clinic=slot.doctor.clinic,
            doctor__specialty__code=slot.doctor.specialty.code,
            status="booked",
            wants_earlier=True,
            offered_slot__isnull=True,
            slot__start__gt=slot.start,
        )
        .order_by("created_at")
        .first()
    )
    if candidate is None:
        return None

    candidate.offered_slot = slot
    candidate.offered_at = timezone.now()
    candidate.save()
    slot.is_booked = True
    slot.save()
    notify_offer(candidate)
    return candidate


def free_slot(slot):
    slot.is_booked = False
    slot.save()
    return offer_to_next(slot)


def release_offer(appointment):
    slot = appointment.offered_slot
    appointment.offered_slot = None
    appointment.offered_at = None
    appointment.save()
    if slot is not None:
        free_slot(slot)


def expire_offers():
    limit = timezone.now() - timedelta(minutes=OFFER_MINUTES)
    for appointment in Appointment.objects.filter(offered_slot__isnull=False, offered_at__lt=limit):
        appointment.wants_earlier = False
        release_offer(appointment)


def accept_offer(appointment):
    new_slot = appointment.offered_slot
    old_slot = appointment.slot

    appointment.slot = new_slot
    appointment.doctor = new_slot.doctor
    appointment.queue_number = next_queue_number(new_slot.doctor, new_slot.start)
    appointment.offered_slot = None
    appointment.offered_at = None
    appointment.wants_earlier = False
    appointment.notified_soon = False
    appointment.save()
    free_slot(old_slot)
    return appointment
