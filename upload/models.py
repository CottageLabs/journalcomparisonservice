import datetime
import logging
import humanize
from django.core.files.storage import default_storage

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from pstf import constants
from accounts.models import PSTFUser, PublisherAccount

frameworks = [(constants.FRAMEWORK_IP, constants.INFORMATION_POWER),
              (constants.FRAMEWORK_FOAA, constants.FAIR_OPEN_ACCESS_ALLIANCE)]

logger = logging.getLogger(__name__)


def publisher_directory(instance, filename: str) -> str:
    """
    Returns the path to save uploads to.
    :param instance:
    :param filename:
    :return:
    """
    return '{0}/{1}'.format(instance.user.publisher.directory_name, filename)


def last_year() -> int:
    return datetime.date.today().year - 1


class UploadFile(models.Model):
    original_file_name = models.CharField(max_length=100)
    upload_file = models.FileField(max_length=500, upload_to=publisher_directory)
    framework = models.CharField(max_length=4, choices=frameworks)
    publisher = models.ForeignKey(PublisherAccount, models.SET_NULL, blank=True, null=True)
    user_name = models.CharField(max_length=300, blank=True, null=True)
    user = models.ForeignKey(PSTFUser, models.SET_NULL, blank=True, null=True)
    uploaded = models.DateTimeField(auto_now_add=True)
    data_year = models.IntegerField(default=last_year)
    journals = models.IntegerField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)

    @property
    def s3_url(self):
        return self.upload_file.url

    @property
    def name(self):
        return self.upload_file.name

    @property
    def human_size(self):
        return humanize.naturalsize(self.size or 0)

    @receiver(pre_delete, sender=PublisherAccount)
    def custom_delete(sender, instance, **kwargs):
        upload_files = UploadFile.objects.filter(publisher=instance)
        for upload_file in upload_files:
            try:
                default_storage.delete(upload_file.name)
                upload_file.delete()
                logger.info("Successfully deleted upload file " + upload_file.name + " for publisher " +
                            instance.publisher_name)
            except Exception as exp:
                logger.exception("Error deleting upload file " + upload_file.name + " for publisher " +
                                 instance.publisher_name)
                raise exp
