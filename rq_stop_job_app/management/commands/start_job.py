from django.core.management.base import BaseCommand, CommandError
from rq_stop_job_app.jobs import job_queue


class Command(BaseCommand):

    def handle(self, *args, **options):

        job = job_queue.delay(1, 1)
        print("Started {}".format(job.id))