# Smart Maple Case


This project is a scraper system that collects all campground data from The Dyrt across the United States and saves it to a local database.
---

## 🔧 Installation

### Requirements

- Docker
- Docker Compose

###  Step-by-step setup:

```bash
# 1. Clone the repository
git clone https://github.com/enesbt/Smart-Maple-Study-Case.git

# 2. Navigate to project folder
cd case_study

# 3. Start the Docker services
docker compose up --build
```

## 🚀 Usage

### Running the Scraper
The scraper is configured to run automatically every 4 hours after the project is started.
Additionally, it can be manually triggered via the API using the following request:

```bash
curl -X POST "http://localhost:8000/trigger-scraper-job"
```
Alternatively, the scraper can also be triggered from the Swagger API documentation at http://localhost:8000/docs.

Once the scraper job is triggered, a batch_id will be returned. This batch_id can be used to check the status of the scraping job.

## 🔌API Endpoints
### GET `/campgrounds`
Searches The Dyrt API in real-time for campgrounds using filters.

### POST `/trigger-scraper-job`
Manually triggers the scraper job.

### GET `/job-status/{batch_id}`
Returns the scraper job status by `batch_id`.

### GET `/db-campgrounds`
Lists campgrounds from the local database (supports `limit` and `offset`).

### GET `/db-campgrounds/{campground_id}`
Returns details of a specific campground (local database)

## 🧑‍💻 Docker Services
### Scraper Service
  - Running main.py, data is fetched from Dyrt API and stored in the database.
### API Service
  - The FastAPI-based API service is used to trigger the scraper process and query the data from the database. (app.py)
### PostgreSQL Service
  - The PostgreSQL service is the relational database where campground data is stored.

These services can be easily managed with Docker Compose and start automatically when the project is initialized.

🧠 Scrape Mechanism
- The U.S. map is divided into 1x1 degree bounding boxes, and for each bbox, a request is sent to The Dyrt API (https://thedyrt.com/api/v6/locations/search-results).
- Requests are made concurrently, using asyncio.Semaphore(5) to allow up to 5 simultaneous calls.
- Each API response is validated using pydantic and stored in the database via a SQLAlchemy model.
- If a campground already exists, it is updated using its id.
- If a request fails, a retry mechanism via the tenacity library is triggered.
- All operations are logged using a robust logging system. Saved /case_study/logs.
- A try-except structure is used to catch errors gracefully and ensure system stability.
- When a scrape job is triggered via API, a unique batch_id is generated (uuid4()) and the task is started in the background using a thread.
- This allows new scrape jobs to be triggered even while a current one is running.
- Data fetching and storage are both performed async.
