from rq.job import Job
from rq.worker import Worker, SIGKILL


class PubSubWorker(Worker):

    def handle_stop_message(self, message):

        if message.get('type') == 'message' and message.get('data') == b'stop' and self.horse_pid:
            try:
                self.kill_horse(SIGKILL)
            except Exception as e:
                self.log.exception("Failed to kill the horse thread")

    def execute_job(self, job, queue):

        pubsub = self.connection.pubsub()
        channel = 'rq:job:pubsub:{}'.format(job.id)

        pubsub.subscribe(**{channel: self.handle_stop_message})

        #listen for stop events in a thread
        pubsub_thread = pubsub.run_in_thread(sleep_time=0.1)

        val = super(PubSubWorker, self).execute_job(job, queue)

        #after the job is done stop the pubsub thread
        pubsub_thread.stop()

        return val


class StopJob(Job):

    def stop(self, delete=True):

        if self.is_started:
            self.connection.publish(channel='rq:job:pubsub:{}'.format(self.id), message="stop")

        if delete:
            self.delete()