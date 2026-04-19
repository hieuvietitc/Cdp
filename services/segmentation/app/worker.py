from celery import Celery
from cdp_shared.config import settings

app = Celery(
    "cdp_segmentation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
app.conf.task_routes = {"app.tasks.*": {"queue": "cdp_segments"}}
app.conf.task_serializer = "json"
app.conf.timezone = "Asia/Ho_Chi_Minh"
