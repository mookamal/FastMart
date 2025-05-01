from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery instance
celery_app = Celery(
    'analitc_project',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['app.tasks.tasks', 'app.tasks.shopify_sync']  # Include shopify_sync tasks
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'schedule-periodic-store-syncs': {
        'task': 'app.tasks.shopify_sync.schedule_periodic_syncs',
        'schedule': crontab(minute=2),
    },
}

# Optional: Configure task routing and queues
celery_app.conf.task_routes = {
    # Example:
    # 'app.tasks.tasks.*': {'queue': 'default'},
}

if __name__ == '__main__':
    celery_app.start()