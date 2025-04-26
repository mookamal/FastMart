from app.tasks.celery_app import celery_app

@celery_app.task
def example_task():
    """
    Example task that can be scheduled or called asynchronously.
    """
    return "Task completed successfully"

# Add more tasks here as needed 