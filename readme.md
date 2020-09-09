## RQ stoppable job for Django-RQ

RQ doesn't provide a built-in feature to stop (kill) jobs once they are executing.

As discussed on https://github.com/rq/rq/issues/684 this is very useful if run heavy computational tasks that might need to be killed.


## Usage

### Run the Django-RQ worker

You can spawn any number of these workers

```
python manage.py rqworker job_queue
```

### Start a job

Start a job that does some dummy calculation and waits for 10 seconds to end

```
python manage.py start_job
```

### Stop (kill) all running jobs

Kill all running jobs work-horses

```
python manage.py stop_job
```

### Stop (kill) a running job by id:

Kill a running job work-horses by the RQ id

```
python manage.py stop_job <job_id>
```

## How it works

The implementation is fairly simple. The **PubSubWorker class** creates a pubsub channel to receive stop messages from jobs.

When calling ```job.stop()``` in a **StopJob** object then a message is published using the pubsub channel for the job id. The message is received by the worker and the work-horse is killed.

The RQ Worker process doesn't need to be killed so after killing the work-horse it's ready to execute the next job right away.

**rq_stop_job_app/jobs/stop_job.py**

```python
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
```

**rq_stop_job/settings.py**

You need to tell Django-RQ to use the StopJob and the PubSubWorker classes in setting.py

```python
RQ = {
    'JOB_CLASS': 'rq_stop_job_app.jobs.stop_job.StopJob',
    'WORKER_CLASS': 'rq_stop_job_app.jobs.stop_job.PubSubWorker',
}
```

Or by running the RQ worker with ```--job-class=rq_stop_job_app.jobs.stop_job.StopJob --worker-class=rq_stop_job_app.jobs.stop_job.PubSubWorker```

```
python manage.py rqworker job_queue --job-class=rq_stop_job_app.jobs.stop_job.StopJob --worker-class=rq_stop_job_app.jobs.stop_job.PubSubWorker
```

Then if you want to ```stop()``` a job just call

```python
import redis
from app.jobs.stop_job import StopJob

conn = redis.StrictRedis()
job = StopJob.fetch(job_id, connection=conn)
job.stop()
```

## Conclusion

I've this implementation running in a django production app and seems to be working without issues.

Anyway I think it requires more testing and advices from a RQ core commiter.

It should also work seamlessly in a non-django RQ app since the StopJob class is just a RQ Job sub class.

While I believe this should be a core implementation in RQ please feel free to share your thoughts. If everything is fine I'll try to make a PR to the RQ repo.