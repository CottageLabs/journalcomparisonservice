"""pstf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import include
from django.views import generic
from material.frontend import urls as frontend_urls

import accounts.views
import data.views
import data.publisher_views
import login.views
import dashboard.views
from pstf import constants

urlpatterns = [
    path('', login.views.login_view, name=constants.LOGIN_URL),
    #  path('qrcode/', accounts.views.show_qr_code, name='pstf-qrcode'),
    path('api/', include('api.urls')),
    path('logout/', login.views.pstf_logout, name='pstf-logout'),
    path('login/', include('login.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('register/', include('registration.urls')),
    path('admin/', admin.site.urls),
    path('feedback/', dashboard.views.feedback, name='feedback'),
    path('docs/', include('docs.urls')),
    path('search/', data.views.search),
    path('autocomplete/<str:type>/<str:query>', data.views.autocomplete),
    path('autocomplete/<str:type>/', data.views.autocomplete),
    path('pubinfo/<int:id>', data.views.publisher_lookup),
    path('issns/<int:year>/', data.views.issns),
    re_path(r'session_security/', include('session_security.urls')),
    re_path(r'^$', generic.RedirectView.as_view(url='/workflow/', permanent=False)),
    re_path(r'', include(frontend_urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
