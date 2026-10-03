"""Standalone background worker service for JobWatch AI monitoring and notification processing."""

import asyncio
import logging
import signal
import sys
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.logging import setup_logging
from app.monitoring.scheduler import get_scheduler
from app.notifications.worker import NotificationDeliveryWorker

settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger("jobwatch.worker")


async def run_notification_cycle():
    """Poll and dispatch pending notifications once."""
    db = SessionLocal()
    try:
        worker = NotificationDeliveryWorker(db)
        processed = worker.process_pending_deliveries(limit=25)
        if processed > 0:
            logger.info("Processed %d pending notification deliveries", processed)
    except Exception as exc:
        logger.error("Error in notification worker cycle: %s", exc)

    finally:
        db.close()


async def main():
    """Main worker loop handling signal termination and periodic tasks."""
    logger.info("Starting JobWatch AI Standalone Background Worker (%s)...", settings.APP_ENV)
    
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: stop_event.set())
        except NotImplementedError:
            # Signal handling on Windows event loop fallback
            pass

    scheduler = get_scheduler()
    if settings.MONITORING_ENABLED:
        logger.info("Starting monitoring scheduler in background worker...")
        await scheduler.start()

    logger.info("Worker process initialized. Entering main processing loop.")

    try:
        while not stop_event.is_set():
            if settings.NOTIFICATIONS_ENABLED:
                await run_notification_cycle()

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                pass
    finally:
        logger.info("Shutting down worker process...")
        await scheduler.stop()
        engine.dispose()
        logger.info("Worker process exited cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker interrupted by user or process signal.")
        sys.exit(0)
