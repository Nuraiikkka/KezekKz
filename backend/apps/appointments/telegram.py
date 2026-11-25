import json
import urllib.request

from django.conf import settings


def send_message(chat_id, text):
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(request, timeout=5)
        return True
    except Exception:
        return False


def track_link(appointment):
    return f"{settings.FRONTEND_URL}/track/{appointment.token}"
