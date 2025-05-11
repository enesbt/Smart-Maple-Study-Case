from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from src.utils.logger import setup_logging, get_logger
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
import httpx
from threading import Thread
from src.jobs import run_campground_job, run_db_get_campgrounds, run_db_get_campground_by_id
from fastapi.responses import JSONResponse
import asyncio
import uuid

setup_logging()
logger = get_logger(__name__)
job_status = {} 
URL = "https://thedyrt.com/api/v6/locations/search-results"

app = FastAPI(
    title="The Dyrt API Wrapper",
    description="""
# Campground Data Collection and Search API

## Endpoints
- `/campgrounds` - Search The Dyrt API for campgrounds with filters
- `/db-campgrounds` - Get campgrounds from local database
- `/db-campgrounds/{campground_id}` - Get specific campground by ID
- `/trigger-scraper-job` - Start scraper job to collect data
- `/job-status/{batch_id}` - Check status of a running job

## How it works
1. Use `/trigger-scraper-job` to start data collection
2. Check job status with `/job-status/{batch_id}`
3. Once complete, query data with `/db-campgrounds`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))  
async def fetch_dyrt_data(params: dict) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, params=params)
        if response.status_code != 200:
            raise httpx.HTTPStatusError("Non-200 response", request=response.request, response=response)
        return response.json()

@app.get("/campgrounds", tags=["Dyrt API"], response_model=Dict[str, Any], summary="Search The Dyrt API", description="Search for campgrounds with various filters.")
async def get_campgrounds(
    drive_time: str = Query("any", description="Drive time filter"),
    air_quality: str = Query("any", description="Air quality filter"),
    electric_amperage: str = Query("any", description="Electric amperage filter"),
    max_vehicle_length: str = Query("any", description="Max vehicle length filter"),
    price: str = Query("any", description="Price filter"),
    rating: str = Query("any", description="Rating filter"),
    bbox: str = Query("", description="Bounding box filter"),
    sort: str = Query("recommended", description="Sorting (recommended, name-raw, -rating,-reviews-count, vb.)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Page size")
):

    params = {
        "filter[search][drive_time]": drive_time,
        "filter[search][air_quality]": air_quality,
        "filter[search][electric_amperage]": electric_amperage,
        "filter[search][max_vehicle_length]": max_vehicle_length,
        "filter[search][price]": price,
        "filter[search][rating]": rating,
        "filter[search][bbox]": bbox,
        "sort": sort,
        "page[number]": page,
        "page[size]": size
    }
    logger.info(f"API request sending: {URL} - Parameters: {params}")

    try:
        data = await fetch_dyrt_data(params)
        logger.info(f"API response successful - {len(data.get('data', []))} camps found")
        return data

    except RetryError as retry_error:
        logger.error(f"Retry failed after multiple attempts: {str(retry_error)}")
        raise HTTPException(status_code=502, detail="The Dyrt API is temporarily unavailable after retries")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/db-campgrounds", response_model=Dict[str, Any], tags=["Database"] ,summary="Get campgrounds from local database", description="Get campgrounds from the local database with pagination.")
async def get_campgrounds(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    try:
        campgrounds = await run_db_get_campgrounds(limit=limit, offset=offset)
        if not campgrounds:
            return JSONResponse(content={"message": "No campgrounds found"}, status_code=404)
        
        return JSONResponse(content={
            "campgrounds": [
                {
                    'id': c.id,
                    'type': c.type,
                    'name': c.name,
                    'latitude': c.latitude,
                    'longitude': c.longitude,
                    'region_name': c.region_name,
                    'administrative_area': c.administrative_area,
                    'nearest_city_name': c.nearest_city_name,
                    'accommodation_type_names': c.accommodation_type_names,
                    'bookable': c.bookable,
                    'camper_types': c.camper_types,
                    'operator': c.operator,
                    'photo_url': str(c.photo_url) if c.photo_url else None,
                    'photo_urls': [str(url) for url in c.photo_urls] if c.photo_urls else [],
                    'photos_count': c.photos_count,
                    'rating': c.rating,
                    'reviews_count': c.reviews_count,
                    'slug': c.slug,
                    'price_low': c.price_low,
                    'price_high': c.price_high,
                    'availability_updated_at': str(c.availability_updated_at) if c.availability_updated_at else None,
                    'address': c.address,
                    'raw_data': c.raw_data
                } for c in campgrounds
            ],
            "total_count": len(campgrounds)
        }, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/db-campgrounds/{campground_id}", tags=["Database"], response_model=Dict[str, Any], summary="Get specific campground by ID", description="Get a specific campground from the local database by its ID.")
async def get_campgrounds_by_id(campground_id: str):
    try:
        campground = await run_db_get_campground_by_id(campground_id)
        if not campground:
            return JSONResponse(content={"message": "No campground found"}, status_code=404)
        
        return JSONResponse(content={
            "campground": [
                {
                    'id': campground.id,
                    'type': campground.type,
                    'name': campground.name,
                    'latitude': campground.latitude,
                    'longitude': campground.longitude,
                    'region_name': campground.region_name,
                    'administrative_area': campground.administrative_area,
                    'nearest_city_name': campground.nearest_city_name,
                    'accommodation_type_names': campground.accommodation_type_names,
                    'bookable': campground.bookable,
                    'camper_types': campground.camper_types,
                    'operator': campground.operator,
                    'photo_url': str(campground.photo_url) if campground.photo_url else None,
                    'photo_urls': [str(url) for url in campground.photo_urls] if campground.photo_urls else [],
                    'photos_count': campground.photos_count,
                    'rating': campground.rating,
                    'reviews_count': campground.reviews_count,
                    'slug': campground.slug,
                    'price_low': campground.price_low,
                    'price_high': campground.price_high,
                    'availability_updated_at': str(campground.availability_updated_at) if campground.availability_updated_at else None,
                    'address': campground.address,
                    'raw_data': campground.raw_data
                }
            ]
        }, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

def run_async_job(batch_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_campground_job())
        job_status[batch_id]["status"] = "completed"
        job_status[batch_id]["result"] = result
    except Exception as e:
        job_status[batch_id]["status"] = "failed"
        job_status[batch_id]["result"] = str(e)
    finally:
        loop.close()

@app.get("/job-status/{batch_id}",  tags=["Scraper"], response_model=Dict[str, Any], summary="Get job status", description="Get the status of a running job by its batch ID.")
def get_job_status(batch_id: str):
    job = job_status.get(batch_id)
    if job:
        return JSONResponse(content={"batch_id": batch_id, "status": job["status"], "result": job["result"]}, status_code=200)
    else:
        return JSONResponse(content={"error": "Batch ID not found"}, status_code=404)

@app.post("/trigger-scraper-job",  tags=["Scraper"], response_model=Dict[str, Any], summary="Trigger scraper job", description="Trigger a new scraper job to collect data.")
def trigger_job():
    batch_id = str(uuid.uuid4())
    job_status[batch_id] = {"status": "pending", "result": None}
    thread = Thread(target=run_async_job, args=(batch_id,))
    thread.start()
    return JSONResponse(content={"status": "Job triggered", "batch_id": batch_id}, status_code=200)