from django.urls import path

from . import views

urlpatterns = [
    path("appointments/", views.AppointmentCreateView.as_view()),
    path("appointments/<uuid:token>/", views.AppointmentDetailView.as_view()),
    path("appointments/<uuid:token>/cancel/", views.AppointmentCancelView.as_view()),
    path("staff/queue/", views.StaffQueueView.as_view()),
    path("staff/appointments/<int:pk>/", views.StaffAppointmentUpdateView.as_view()),
]
