from typing import Optional
from celery import Celery
from weskit import Database

database: Optional[Database] = None
celery_app: Optional[Celery] = None
