from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from src.models import CampgroundDB, Campground
from src.utils.logger import get_logger


logger = get_logger(__name__)

class CampgroundRepository:
    
    def __init__(self, db: Session):
        self.db = db
        
    def save_campground(self, campground: Campground):

        try:
            links_json = {"self": str(campground.links.self)} if campground.links else {}
            photo_urls_list = [str(url) for url in campground.photo_urls] if campground.photo_urls else []
            accommodation_types = list(campground.accommodation_type_names) if campground.accommodation_type_names else []
            camper_types_list = list(campground.camper_types) if campground.camper_types else []
            raw_json = campground.raw_data if hasattr(campground, 'raw_data') and campground.raw_data is not None else {}
        
            values = {
                'id': campground.id,
                'type': campground.type,
                'links': links_json,
                'name': campground.name,
                'latitude': campground.latitude,
                'longitude': campground.longitude,
                'region_name': campground.region_name,
                'administrative_area': campground.administrative_area,
                'nearest_city_name': campground.nearest_city_name,
                'accommodation_type_names': accommodation_types,
                'bookable': campground.bookable,
                'camper_types': camper_types_list,
                'operator': campground.operator,
                'photo_url': str(campground.photo_url) if campground.photo_url else None,
                'photo_urls': photo_urls_list,
                'photos_count': campground.photos_count,
                'rating': campground.rating,
                'reviews_count': campground.reviews_count,
                'slug': campground.slug,
                'price_low': campground.price_low,
                'price_high': campground.price_high,
                'availability_updated_at': campground.availability_updated_at,
                'address': campground.address if hasattr(campground, 'address') else None,
                'raw_data': raw_json
            }
            
            existing = self.db.query(CampgroundDB).filter(CampgroundDB.id == campground.id).first()
            if existing:
                stmt = insert(CampgroundDB).values(**values)
                
                update_values = {k: v for k, v in values.items() if k != 'id'}
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_=update_values
                )
                self.db.execute(stmt)
            else:
                db_camp = CampgroundDB(**values)
                self.db.add(db_camp)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upserting campground {campground.id}: {str(e)}", exc_info=True)
            raise e

    def get_all(self, limit: int = 10, offset: int = 0):
        try:
            logger.info("Fetching all campgrounds with pagination")
            return self.db.query(CampgroundDB).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching campgrounds: {str(e)}", exc_info=True)
            raise e
        
    def get_by_id(self, campground_id: str):
        try:
            logger.info(f"Fetching campground by ID: {campground_id}")
            return self.db.query(CampgroundDB).filter(CampgroundDB.id == campground_id).first()
        except Exception as e:
            logger.error(f"Error fetching campground by ID {campground_id}: {str(e)}", exc_info=True)
            raise e

    def count_all(self):
        try:
            return self.db.query(CampgroundDB).count()
        except Exception as e:
            logger.error(f"Camp count error: {str(e)}", exc_info=True)
            raise e
            