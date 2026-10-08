from django.urls import path

from . import views

urlpatterns = [
    path("clinics/", views.ClinicListView.as_view()),
    path("clinics/<slug:slug>/specialties/", views.SpecialtyListView.as_view()),
    path("clinics/<slug:slug>/doctors/", views.DoctorListView.as_view()),
    path("clinics/<slug:slug>/slots/", views.SlotListView.as_view()),
]
