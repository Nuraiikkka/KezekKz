from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    address = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.name


class Specialty(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="specialties")
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    visit_minutes = models.IntegerField(default=20)

    class Meta:
        verbose_name_plural = "specialties"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="doctors")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name="doctors")
    full_name = models.CharField(max_length=200)
    room = models.CharField(max_length=20, blank=True)
    delay_minutes = models.IntegerField(default=0)

    def __str__(self):
        return self.full_name


class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.doctor} {self.start}"
