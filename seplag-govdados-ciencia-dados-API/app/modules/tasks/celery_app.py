# Configuração do Celery
from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    'Extract_text',
    broker=REDIS_URL,
    backend=REDIS_URL
)

from . import extraction_tasks
from . import structure_tasks
from . import validation_tasks
from . import report_tasks