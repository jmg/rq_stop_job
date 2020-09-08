import redis
import time
from django_rq import job


redis_conn = redis.StrictRedis()


@job('job_queue', connection=redis_conn)
def job_queue(a, b):

    time.sleep(10)
    return a + b