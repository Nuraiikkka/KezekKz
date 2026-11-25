from django.urls import path

from . import views

urlpatterns = [
    path("appointments/", views.AppointmentCreateView.as_view()),
    path("appointments/<uuid:token>/", views.AppointmentDetailView.as_view()),
    path("appointments/<uuid:token>/cancel/", views.AppointmentCancelView.as_view()),
    path("appointments/<uuid:token>/rate/", views.AppointmentRateView.as_view()),
    path("appointments/<uuid:token>/confirm/", views.AppointmentConfirmView.as_view()),
    path("appointments/<uuid:token>/arrive/", views.AppointmentArriveView.as_view()),
    path("clinics/<slug:slug>/board/", views.BoardView.as_view()),
    path("staff/stats/", views.StaffStatsView.as_view()),
    path("appointments/<uuid:token>/earlier/", views.AppointmentEarlierView.as_view()),
    path("appointments/<uuid:token>/offer/accept/", views.AppointmentOfferView.as_view()),
    path("appointments/<uuid:token>/offer/decline/", views.AppointmentDeclineView.as_view()),
    path("appointments/<uuid:token>/pay/", views.AppointmentPayView.as_view()),
    path("staff/appointments/<int:pk>/mark-paid/", views.StaffMarkPaidView.as_view()),
    path("staff/payments/pending/", views.StaffPendingPaymentsView.as_view()),
    path("clinics/<slug:slug>/recommend/", views.RecommendView.as_view()),
    path("config/", views.ConfigView.as_view()),
    path("telegram/webhook/<str:secret>/", views.TelegramWebhookView.as_view()),
    path("staff/queue/", views.StaffQueueView.as_view()),
    path("staff/appointments/<int:pk>/", views.StaffAppointmentUpdateView.as_view()),
]
