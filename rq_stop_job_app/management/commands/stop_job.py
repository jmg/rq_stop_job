from django.core.management.base import BaseCommand, CommandError
import redis
from rq_stop_job_app.jobs.stop_job import StopJob
from rq.registry import StartedJobRegistry
from rq import Queue, Worker


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument('job_id', nargs='*', type=str)

    def stop_job(self, job_id, conn):

        job = StopJob.fetch(job_id, connection=conn)
        print "Stopping {}".format(job.id)
        job.stop()

    def handle(self, *args, **options):

        conn = redis.StrictRedis()

        if options["job_id"]:

            self.stop_job(options["job_id"][0], conn)
        else:
            started_jobs = StartedJobRegistry("job_queue", connection=conn)

            for job_id in started_jobs.get_job_ids():
                self.stop_job(job_id, conn)