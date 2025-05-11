from src.connector.dyrt_connector import DyrtConnector
from src.utils.logger import get_logger


async def run_campground_job():
    connector = DyrtConnector()
    result = await connector.get_all_campgrounds()
    logger = get_logger(__name__)
    logger.info(f"Job completed with result: {result}")
    return result

async def run_db_get_campgrounds(limit: int = 10, offset: int = 0):
    connector = DyrtConnector()
    result = await connector.get_campgrounds_db(limit=limit, offset=offset)
    logger = get_logger(__name__)
    logger.info(f"Job completed with result: {result}")
    return result

async def run_db_get_campground_by_id(campground_id: str):
    connector = DyrtConnector()
    result = await connector.get_campground_by_id(campground_id)
    logger = get_logger(__name__)
    logger.info(f"Job completed with result: {result}")
    return result
