from typing import Dict, Any
from src.utils.logger import get_logger
from src.models import Campground
from src.repositories.campground_repository import CampgroundRepository
from src.database import engine, SessionLocal
from src.models.model import Base
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from geopy.geocoders import Nominatim
import time

logger = get_logger(__name__)

BASE_URL = "https://thedyrt.com/api/v6/locations/search-results"

class DyrtConnector:

    def __init__(self):
        self.base_url = BASE_URL
        logger.info(f"API Connector initialized with base URL: {self.base_url}")
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.repo = CampgroundRepository(self.db)
        logger.info("Database connection and repository initialized")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
            logger.info("Database connection closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def fetch_page(self, client: httpx.AsyncClient, page: 1, bbox: str, size: int = 500) -> Dict[str, Any]:
        params = {
            "filter[search][drive_time]": "any",
            "filter[search][air_quality]": "any",
            "filter[search][electric_amperage]": "any",
            "filter[search][max_vehicle_length]": "any",
            "filter[search][price]": "any",
            "filter[search][rating]": "any",
            "filter[search][bbox]": bbox,
            "sort": "recommended",
            "page[number]": page,
            "page[size]": size
        }
        logger.info(f"Fetching bbox {bbox}")
        response = await client.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_all_campgrounds(self):
        bboxes = self.generate_bboxes()
        semaphore = asyncio.Semaphore(5)  
        initial_count = self.repo.count_all()
        total_saved = 0
        total_errors = 0
        async with httpx.AsyncClient() as client:
            try:
                async def limited_fetch(bbox):
                    async with semaphore:
                        try:
                            data = await self.fetch_page(client, 1, bbox)
                            saved, errors = await self.validate_api_response_and_save_db(data)
                            return saved, errors
                        except Exception as e:
                            logger.error(f"Page {1} error: {e}")
                            return 0, 1

                tasks = [limited_fetch(bbox) for bbox in bboxes]
                results = await asyncio.gather(*tasks)

                for saved, errors in results:
                    total_saved += saved
                    total_errors += errors

                db_count_campground = self.repo.count_all()
                new_added = max(db_count_campground - initial_count, 0)
                updated = max(total_saved - new_added, 0)

                result_summary = {
                    "total_saved": total_saved,
                    "total_errors": total_errors,
                    "db_old_count_campground": initial_count,
                    "db_count_campground": db_count_campground,
                    "new_added": new_added,
                    "updated": updated,
                    "status": "success"
                }

                logger.info(f"✅ Total {total_saved} campground saved, {total_errors} errors occurred.")
                if db_count_campground == initial_count:
                    logger.info("🟡 No changes detected in the database. All records are up to date.")
                elif db_count_campground > initial_count:
                    logger.info(f"🆕 {new_added} new campgrounds added, ♻️ {updated} campgrounds updated.")
                else:
                    logger.warning(f"⚠️ Total campground count has decreased! Initial: {initial_count}, Final DB count campground: {db_count_campground}")

            except Exception as e:
                logger.error(f"Failed to fetch: {e}")
            
        return result_summary
    
    def generate_bboxes(self, min_lat=24, max_lat=50, min_lng=-125, max_lng=-67):
        return [
            f"{lng},{lat},{lng + 1},{lat + 1}"
            for lat in range(min_lat, max_lat)
            for lng in range(min_lng, max_lng)
        ]

    async def validate_api_response_and_save_db(self, data):
        saved_count = 0
        error_count = 0

        if not data or 'data' not in data:
            logger.error("API response is empty or invalid")
            return
        
        logger.info(f"API count {len(data['data'])} items")
        
        for item in data['data']:
            try:
                camp_id = item.get('id')
                camp_type = item.get('type')
                camp_links = item.get('links', {})
                camp_attrs = item.get('attributes', {})


                # Address field 
                # latitude = camp_attrs.get('latitude')
                # longitude = camp_attrs.get('longitude')

                address = None
                # if latitude and longitude:
                #     address = await self.get_address_from_coordinates_async(latitude, longitude)
                #     logger.info(f"Address: {address}")

                campground_data = {
                    'id': camp_id,
                    'type': camp_type,  
                    'links': camp_links,
                    **camp_attrs, 
                    'address': address,
                    'raw_data': item 
                }
                
                campground = Campground(**campground_data)
                self.repo.save_campground(campground)
                saved_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Camping process error - ID: {item.get('id', 'unknown')}, Error: {str(e)}", exc_info=True)

        logger.info(f"Total {saved_count} camping saved, {error_count} errors occurred.")
        return saved_count, error_count

    async def get_address_from_coordinates_async(self, lat, lon):
        geolocator = Nominatim(user_agent="campground_app")
        loop = asyncio.get_event_loop()
        try:
            location = await loop.run_in_executor(None, geolocator.reverse, (lat, lon))
            time.sleep(1)
            return location.address if location else None
        except Exception as e:
            logger.error(f"Geopy hata: {e}")
            return None

    async def get_campground_by_id(self, campground_id: str):
        try:
            campground = self.repo.get_by_id(campground_id)
            return campground
        except Exception as e:
            logger.error(f"Error fetching campgrounds from DB: {str(e)}")
            return []

    async def get_campgrounds_db(self, limit: int = 10, offset: int = 0):
        try:
            campgrounds = self.repo.get_all(limit=limit, offset=offset)
            return campgrounds
        except Exception as e:
            logger.error(f"Error fetching campgrounds from DB: {str(e)}")
            return []

    async def get_campgrounds_count(self):
        try:
            count = self.repo.count_all()
            return count
        except Exception as e:
            logger.error(f"Error fetching campgrounds from DB: {str(e)}")
            return 0