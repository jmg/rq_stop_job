import os
import signal
from rq.job import Job
from rq.worker import Worker, SIGKILL


class PubSubWorker(Worker):

    def __init__(self, *args, **kwargs):

        self.pubsub = None
        super().__init__(*args, **kwargs)

    def handle_stop_message(self, message):

        if message.get('type') == 'message' and message.get('data') == b'stop' and self.horse_pid:
            try:
                self.kill_horse(SIGKILL)
            except Exception as e:
                self.log.exception("Failed to kill the horse thread")

    def execute_job(self, job, queue):

        if self.pubsub is None:
            self.pubsub = self.connection.pubsub()

        channel = 'rq:job:pubsub:{}'.format(job.id)

        self.pubsub.subscribe(**{channel: self.handle_stop_message})
        self.pubsub.run_in_thread(sleep_time=0.1)

        return super().execute_job(job, queue)


class StopJob(Job):

    def stop(self, delete=True):

        if self.is_started:
            self.connection.publish(channel='rq:job:pubsub:{}'.format(self.id), message="stop")

        if delete:
            self.delete()