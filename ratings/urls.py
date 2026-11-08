from django.urls import path

from . import views

app_name = "ratings"

urlpatterns = [
    path("avaliar/", views.rate, name="rate"),
]
