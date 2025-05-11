from sqlalchemy import Column, String, Float, JSON, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CampgroundDB(Base):
    __tablename__ = "campgrounds"

    id = Column(String, primary_key=True)
    type = Column(String)
    links = Column(JSON)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    region_name = Column(String)
    administrative_area = Column(String, nullable=True)
    nearest_city_name = Column(String, nullable=True)
    accommodation_type_names = Column(JSON, default=[])
    bookable = Column(Boolean, default=False)
    camper_types = Column(JSON, default=[])
    operator = Column(String, nullable=True)
    photo_url = Column(Text, nullable=True)
    photo_urls = Column(JSON, default=[])
    photos_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, default=0)
    slug = Column(String, nullable=True)
    price_low = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    availability_updated_at = Column(DateTime, nullable=True)
    address = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)