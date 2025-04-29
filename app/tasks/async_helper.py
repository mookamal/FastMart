import asyncio
from app.tasks.celery_app import celery_app
import asyncio
from functools import wraps


def run_async(coro):  # noqa: E302
    """
    Runs a coroutine inside a valid or new event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        # If the loop is closed, raise to create a new one
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def celery_async_task(bind=True, max_retries=3, default_retry_delay=60*5):
    """
    Decorator to define a Celery task that runs a coroutine with retry support.

    Usage:
        @celery_async_task()
        async def initial_sync_store(self, store_id: UUID):
            async with AsyncSessionLocal() as db:
                return await sync_store_logic(self, store_id, db)
    """
    def decorator(async_func):
        # Ensure we use the Celery task decorator here
        task_decorator = celery_app.task(
            bind=bind,
            max_retries=max_retries,
            default_retry_delay=default_retry_delay,
        )

        @task_decorator
        @wraps(async_func)
        def wrapper(self, *args, **kwargs):
            try:
                # Invoke the coroutine via run_async
                return run_async(async_func(self, *args, **kwargs))
            except Exception as exc:
                # Automatically retry on failure
                raise self.retry(exc=exc)

        return wrapper

    return decorator