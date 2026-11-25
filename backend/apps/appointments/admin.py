from django.contrib import admin

from .models import Appointment, Patient, Payment

admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Payment)
