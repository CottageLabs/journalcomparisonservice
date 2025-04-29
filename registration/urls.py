from django.urls import path
from . import views, ins_views

urlpatterns =[
    path('select_user_type/', views.select_user_type, name='select_user'),
    path('ins_self_register_tc/', ins_views.terms_conditions, name='ins_self_reg_tc'),
    path('ins_self_register_uap/', ins_views.accept_uap, name='ins_self_reg_uap'),
    path('self_register_tc/', views.terms_conditions, name='self_reg_tc'),
    path('self_register_uap/', views.accept_uap, name='self_reg_uap'),
    path('ins_self_register/', ins_views.ins_self_register_workflow, name='ins_self_register'),
    path('pub_self_register/', views.publisher_self_register, name='publisher_self_register'),
    path('pub_email_otp/', views.email_otp, name='publisher_email_otp'),
    path('pub_info/', views.publisher_info, name='publisher_info'),
    path('publisher/<str:id>/', views.publisher_registration_with_id),
    path('ins_user/<str:id>/', views.ins_user_registration_with_id)
]