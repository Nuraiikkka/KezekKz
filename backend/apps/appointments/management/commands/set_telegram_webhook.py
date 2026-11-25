import json
import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Tell Telegram where to send bot messages"

    def handle(self, *args, **options):
        base = os.getenv("BACKEND_URL") or os.getenv("RENDER_EXTERNAL_URL")
        if not settings.TELEGRAM_BOT_TOKEN or not base:
            self.stdout.write("Telegram is not configured, skipped")
            return

        url = f"{base}/api/telegram/webhook/{settings.TELEGRAM_WEBHOOK_SECRET}/"
        api = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
        request = urllib.request.Request(
            api, data=json.dumps({"url": url}).encode(), headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request, timeout=10)
            self.stdout.write(self.style.SUCCESS("Telegram webhook is set"))
        except Exception as error:
            self.stdout.write(f"Could not set the webhook: {error}")
