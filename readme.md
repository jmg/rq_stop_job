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

The implementation is fairly simple. The **StopJob class** saves the RQ work-horse pid every time a new job is performed in the job metadata (this gets saved in the key-value storage).

When calling ```job.stop()``` the work-horse process is killed using the pid saved in the job metadata.

The RQ Worker process doesn't need to be killed so after killing the work-horse it's ready to execute the next job right away.

**rq_stop_job_app/jobs/stop_job.py**

```python
import os
import signal
from rq.job import Job


class StopJob(Job):
    """
        A job that can be stopped (Killed) using the workhorse PID.
        It saves the workhorse PID in storage every time a workhorse is forked by RQ.
    """
    def perform(self):

        self.meta["workhorse_pid"] = os.getpid()
        #save the workhorse PID in the job metadata
        self.save_meta()

        return super(StopJob, self).perform()

    def stop(self, delete=True):

        if self.is_started:
            try:
                os.kill(self.meta["workhorse_pid"], signal.SIGKILL)
            except Exception, e:
                print e

        if delete:
            self.delete()
```

**rq_stop_job/settings.py**

You need to tell Django-RQ you use the StopJob class in setting.py

```python
RQ = {
    'JOB_CLASS': 'rq_stop_job_app.jobs.stop_job.StopJob',
}
```

Or by running the RQ worker with ```--job-class=rq_stop_job_app.jobs.stop_job.StopJob```

```
python manage.py rqworker job_queue --job-class=rq_stop_job_app.jobs.stop_job.StopJob

```

## Conclusion

I've this implementation running in a django production app and seems to be working without issues.

Anyway I think it requires more testing and advices from a RQ core commiter.

It should also work seamlessly in a non-django RQ app since the StopJob class is just a RQ Job sub class.

While I believe this should be a core implementation in RQ please feel free to share your thoughts. If everything is fine I'll try to make a PR to the RQ repo.