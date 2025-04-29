from django.urls import path

from pstf import constants
from . import views

urlpatterns =[
    path('email-otp', views.email_otp_view, name=constants.EMAIL_OTP_URL),
    path('verify-otp', views.verify_otp_view, name=constants.VERIFY_OTP_URL),
    path('verify-2nd-otp', views.verify_2nd_otp_view, name=constants.VERIFY_2ND_OTP_URL)
]
