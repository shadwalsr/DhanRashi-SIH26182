from celery import Celery
from kombu import Queue

from app.core.config import settings

celery_app = Celery(
    "vasp_trace_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="trace",
    task_queues=(
        Queue("fetch", routing_key="fetch.#"),
        Queue("trace", routing_key="trace.#"),
        Queue("analyze", routing_key="analyze.#"),
        Queue("report", routing_key="report.#"),
    ),
    task_routes={
        "app.workers.tasks.fetch_*": {"queue": "fetch"},
        "app.workers.tasks.trace_*": {"queue": "trace"},
        "app.workers.tasks.analyze_*": {"queue": "analyze"},
        "app.workers.tasks.report_*": {"queue": "report"},
    },
    beat_schedule={
        "heartbeat-every-minute": {
            "task": "app.workers.tasks.noop_heartbeat",
            "schedule": 60.0,
        },
    },
)


@celery_app.task(name="app.workers.tasks.noop_heartbeat")
def noop_heartbeat() -> dict:
    """No-op periodic task proving beat round-trip."""
    return {"status": "ok", "message": "beat heartbeat pulse"}


@celery_app.task(name="app.workers.tasks.roundtrip_ping")
def roundtrip_ping(message: str = "pong") -> dict:
    """No-op test task proving roundtrip execution across worker queues."""
    return {"echo": message, "success": True}
