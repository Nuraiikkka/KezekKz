from django.urls import path

from . import views

urlpatterns = [
    path("intake/questions/", views.QuestionListView.as_view()),
    path("intake/", views.IntakeCreateView.as_view()),
]
