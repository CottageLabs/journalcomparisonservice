from django.db import models
from viewflow.models import Process


class PublisherSelfRegisterProcess(Process):
    email = models.EmailField()
    name = models.CharField(max_length=100)
    publisher_name = models.CharField(max_length=100)
    valid_otp = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=10, default='')


class InsSelfRegisterProcess(Process):
    """Institutional User Self register process"""
    email = models.EmailField()
    name = models.CharField(max_length=100)
    organisation_name = models.CharField(max_length=100, default='')
    valid_otp = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=10, default='')


class PublisherLinkRegisterProcess(Process):
    email = models.EmailField()
    link_id = models.CharField(max_length=60)
    valid_otp = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=10, default='')


class InsUserLinkRegisterProcess(Process):
    email = models.EmailField()
    link_id = models.CharField(max_length=60)
    valid_otp = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=10, default='')
