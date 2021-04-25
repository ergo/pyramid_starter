import logging
import requests


log = logging.getLogger(__name__)

from testscaffold.celery import celery_app


@celery_app.task
def test_task(subreddit, dt, d, td):
    print("task started", subreddit, dt, d, td)
    result = requests.get("https://www.reddit.com/r/{}.json".format(subreddit))
    if result.status_code == requests.codes.ok:
        data = result.json()
        print(data)
    else:
        print(result)


@celery_app.task
def celery_beat_heartbeat():
    log.info("heartbeating celery")
    celery_app.pyramid["request"].registry.statsd_client.increment("heartbeat", 1, tags=["type:celery_beat"])
