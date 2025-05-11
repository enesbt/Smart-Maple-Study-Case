from sqlalchemy import create_engine
import os
from sqlalchemy.orm import sessionmaker
from src.utils.logger import get_logger
from sqlalchemy.ext.declarative import declarative_base

logger = get_logger(__name__)

DATABASE_URL = os.environ.get("DB_URL")

logger.info(f"Connecting to database: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()