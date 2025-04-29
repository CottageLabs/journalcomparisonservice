from django.urls import path
from . import views

urlpatterns = [
    path('about_us/uap', views.uap),
]
