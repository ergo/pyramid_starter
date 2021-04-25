import logging
import requests

from pyramid.threadlocal import get_current_request
from testscaffold.services.resource_tree_service import tree_service

log = logging.getLogger(__name__)

from testscaffold.celery import celery_app
from testscaffold.models.db import Entry

@celery_app.task
def test_task(subreddit, dt, d, td):
    request = get_current_request()
    print("task started", subreddit, dt, d, td)
    result = requests.get("https://www.reddit.com/r/{}.json".format(subreddit))
    if result.status_code == requests.codes.ok:
        data = result.json()
        print(data)
    else:
        print(result)
    # test celery db commits
    request.tm.begin()
    resource = Entry()
    resource.resource_name = "Res from celery task"
    resource.persist(flush=True, db_session=request.dbsession)
    # this accounts for the newly inserted row so the total_children
    # will be max+1 position for new row
    total_children = tree_service.count_children(resource.parent_id, db_session=request.dbsession)
    tree_service.set_position(
        resource_id=resource.resource_id, to_position=total_children, db_session=request.dbsession,
    )
    request.tm.commit()


@celery_app.task
def celery_beat_heartbeat():
    log.info("heartbeating celery")
    celery_app.pyramid["request"].registry.statsd_client.increment("heartbeat", 1, tags=["type:celery_beat"])
