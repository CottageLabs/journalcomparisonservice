import os
import traceback
from datetime import datetime
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from django.conf import settings

from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from pstf.constants import ADMIN_EMAIL
from pstf.utils import send_email

logger = logging.getLogger(__name__)


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def create_data_export_package():
    """  Create weekly data dump for all data"""
    logger.info("New weekly package started")
    try:
        from dashboard.export_views import ExportData
        from data.utils import get_all_ip_data, get_all_foaa_data

        export_data = ExportData().create_weekly_pkg_dir_path()
        export_data.copy_files_to_tmp()

        ip_data_list = get_all_ip_data()
        foaa_data_list = get_all_foaa_data()

        if ip_data_list and len(ip_data_list) > 0:
            export_data.write_data_to_csv(ip_data_list)
        if foaa_data_list and len(foaa_data_list) > 0:
            export_data.write_data_to_csv(foaa_data_list)

            export_data.create_download_package()
        logger.info("New weekly package Finished")

    except Exception:
        logging.exception("Error while creating weekly data export package")

        if settings.REPORT_SCHEDULED_JOB_FAILURES:
            send_email(None, 'PSTF PROD Weekly data exports failed', ADMIN_EMAIL,
                       traceback.format_exc(), use_html=False)


def clean_data_packages():
    """
    Delete all the files in the tmp directory which are older than the days configured in settings
    """
    try:
        from django.conf import settings
        from datetime import datetime
        from dashboard.export_views import ExportData
        from pstf import constants

        for file in os.listdir(constants.TEMP_DIR):
            # Do not delete weekly dump file
            # Delete only zip files
            if file.endswith(".zip") and not file.startswith(ExportData.WEEKLY_DATA_DIR_NAME):
                file_path = os.path.join(constants.TEMP_DIR, file)
                time_in_millis = os.path.getmtime(file_path)
                file_creation_date = datetime.fromtimestamp(time_in_millis)
                today = datetime.now()
                file_age = (today - file_creation_date).days
                if file_age > settings.DATA_DUMP_FILES_MAX_AGE:
                    os.remove(file_path)
                    logger.info("Deleted file : " + file)

    except Exception:
        logging.exception("Error while cleaning data packages")

        if settings.REPORT_SCHEDULED_JOB_FAILURES:
            send_email(None, 'PSTF PROD Cleaning data packages failed', ADMIN_EMAIL,
                       traceback.format_exc(), use_html=False)


class Command(BaseCommand):
    help = "Runs scheduled data dump."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(create_data_export_package, trigger='cron', day_of_week='sun', hour=00, minute=00,
                          next_run_time=datetime.now(),
                          id="create_data_export_package",
                          max_instances=1,
                          replace_existing=True,
                          )
        scheduler.add_job(clean_data_packages, trigger='cron', hour=22, minute=00, next_run_time=datetime.now(),
                          id="clean_data_packages",
                          max_instances=1,
                          replace_existing=True,
                          )

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
