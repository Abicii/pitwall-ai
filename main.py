import os
import redis
import json
from fastapi import FastAPI
from worker import fetch_f1_data_and_strategy, celery_app
from celery.result import AsyncResult

app = FastAPI(title="PitWall AI")

# Connect FastAPI directly to Redis for the Cache layer
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

@app.post("/api/v1/jobs/strategy", status_code=202)
def request_strategy(year: int = 2023, race: str = "Monza"):
    # 1. Check Redis Cache First!
    cache_key = f"strat:{year}:{race.lower()}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return {
            "source": "redis_cache (0 tokens spent!)",
            "job_id": None, # No job needed, we already have the answer
            "data": json.loads(cached_result)
        }

    # 2. Cache Miss -> Dispatch to Queue
    task = fetch_f1_data_and_strategy.delay(year, race)
    return {
        "source": "queue_dispatched",
        "job_id": task.id,
        "check_status_url": f"/api/v1/jobs/{task.id}"
    }

@app.get("/api/v1/jobs/{job_id}")
def check_job_status(job_id: str):
    task_result = AsyncResult(job_id, app=celery_app)
    
    if task_result.state in ["PENDING", "PROCESSING"]:
        return {"status": "WORKING_ON_IT"}
    elif task_result.state == "SUCCESS":
        data = task_result.result
        
        # 3. Cache the expensive LLM result for 1 hour (3600 seconds)
        cache_key = f"strat:{data['year']}:{data['race'].lower()}"
        redis_client.setex(cache_key, 3600, json.dumps(data))
        
        return {"status": "COMPLETED", "source": "llm_fresh", "data": data}
    else:
        return {"status": "FAILED"}