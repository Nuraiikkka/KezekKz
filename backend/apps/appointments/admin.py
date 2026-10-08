from django.contrib import admin

from .models import Appointment, Patient

admin.site.register(Patient)
admin.site.register(Appointment)
