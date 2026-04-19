"""
APScheduler-based batch ingestion runner.
Runs loyalty sync at 01:00 and sales sync at 02:00 daily (Asia/Ho_Chi_Minh).
"""
import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from app.connectors.loyalty_pg import LoyaltyConnector
from app.connectors.sales_pg import SalesConnector
from app.loaders.profile_loader import ProfileLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")


@scheduler.scheduled_job("cron", hour=1, minute=0, id="loyalty_sync")
def loyalty_sync():
    logger.info("Starting loyalty sync")
    connector = LoyaltyConnector()
    loader = ProfileLoader()
    count = 0
    for batch in connector.fetch_members():
        loader.upsert_loyalty_batch(batch)
        count += len(batch)
    logger.info("Loyalty sync complete: %d members", count)


@scheduler.scheduled_job("cron", hour=2, minute=0, id="sales_sync")
def sales_sync():
    logger.info("Starting sales/bookings sync")
    connector = SalesConnector()
    loader = ProfileLoader()
    count = 0
    for batch in connector.fetch_bookings():
        loader.upsert_booking_events(batch)
        count += len(batch)
    logger.info("Sales sync complete: %d bookings", count)


if __name__ == "__main__":
    logger.info("Ingestion scheduler starting")
    scheduler.start()
