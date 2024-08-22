from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = "dialog"
urlpatterns = [
    path("", views.ChatbotView.as_view(), name="index"),
]