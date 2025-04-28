from app.tasks.celery_app import celery_app
import logging
import asyncio
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
async def return_hello():
    await asyncio.sleep(1)
    return 'hello' 

@celery_app.task
def example_task():
    """
    Example task that can be scheduled or called asynchronously.
    """
    async_to_sync(return_hello)()
    return "Task completed successfully ____________________________________|||___________________________________"

# Add more tasks here as needed 