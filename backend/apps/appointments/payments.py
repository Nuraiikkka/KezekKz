from django.utils import timezone

from .models import Payment


def luhn_ok(number):
    total = 0
    for index, char in enumerate(reversed(number)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def make_receipt_number(appointment):
    return f"KZ-{timezone.localdate():%y%m%d}-{appointment.id:05d}"


def create_payment(appointment, method, card_number="", iin=""):
    price = appointment.doctor.specialty.price
    data = {"appointment": appointment, "method": method, "amount": price, "receipt_number": make_receipt_number(appointment)}

    if method == "card":
        data["card_last4"] = card_number[-4:]
        data["status"] = "paid"
        data["paid_at"] = timezone.now()
    elif method == "kaspi":
        data["status"] = "paid"
        data["paid_at"] = timezone.now()
    elif method == "insurance":
        data["amount"] = 0
        data["status"] = "paid"
        data["paid_at"] = timezone.now()
    else:
        data["status"] = "pending"

    return Payment.objects.create(**data)
