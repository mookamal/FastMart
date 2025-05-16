from app.db.base import AsyncSessionLocal
from app.tasks.async_helper import celery_async_task
from app.services.analytics.daily_sales_service import DailySalesAnalyticsService
from uuid import UUID


@celery_async_task()
async def calculate_all_analytics_for_store(self, store_id: UUID):
    await DailySalesAnalyticsService.process_all_store_analytics(store_id=store_id)
