from django.contrib import admin

from .models import Clinic, Doctor, Specialty, TimeSlot

admin.site.register(Clinic)
admin.site.register(Specialty)
admin.site.register(Doctor)
admin.site.register(TimeSlot)
