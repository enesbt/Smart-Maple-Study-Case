"""
Main entrypoint for The Dyrt web scraper case study.

Usage:
    The scraper can be run directly (`python main.py`) or via Docker Compose (`docker compose up`).

If you have any questions in mind you can connect to me directly via info@smart-maple.com
"""


import logging
from src.utils.logger import setup_logging, get_logger
import asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.jobs import run_campground_job


def run_sync_job():
    asyncio.run(run_campground_job())

if __name__ == "__main__":
    setup_logging(log_level=logging.INFO)
    logger = get_logger(__name__)
    logger.info("Scraper Started")
    scheduler = BlockingScheduler()
    scheduler.add_job(run_sync_job, trigger=IntervalTrigger(minutes=10), id='run_campground_job', replace_existing=True)
    logger.info("Scheduler started")  
    run_sync_job() 
    scheduler.start()
