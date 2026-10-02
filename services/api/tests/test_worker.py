from app.workers.celery_app import celery_app, noop_heartbeat, roundtrip_ping


def test_roundtrip_ping_task():
    result = roundtrip_ping("hello_vasp")
    assert result["echo"] == "hello_vasp"
    assert result["success"] is True


def test_noop_heartbeat_task():
    result = noop_heartbeat()
    assert result["status"] == "ok"


def test_celery_queues_configured():
    queue_names = [q.name for q in celery_app.conf.task_queues]
    assert "fetch" in queue_names
    assert "trace" in queue_names
    assert "analyze" in queue_names
    assert "report" in queue_names
