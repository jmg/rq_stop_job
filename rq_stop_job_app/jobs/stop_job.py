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