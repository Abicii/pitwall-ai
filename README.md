# PitWall AI 🏎️📻

> **Note**: This is a **learning project** built to explore asynchronous backend architectures, distributed task queues, caching strategies, and LLM integrations. The Formula 1 "pit wall" theme is a fun narrative wrapper to make exploring these concepts engaging and hands-on!

---

## 💡 What It Does (The Story)

Imagine you are on the pit wall during an F1 race. Your driver sets a flying lap, and you need a quick tactical radio message (e.g., *"Box this lap for softs"* or *"Save tires in sector 2"*).

PitWall AI simulates that workflow:
1. **Pulls real F1 telemetry** for a given race session using [FastF1](https://github.com/theOehrly/Fast-F1).
2. **Generates a punchy race engineer radio call** using Google Gemini.
3. **Caches results in Redis** so repeated queries are instant and don't waste AI tokens or slow down telemetry fetching.

---

## 🛠️ Concepts Explored

This project was built to practice:
- **FastAPI**: Handling API requests and returning immediate job tokens for long-running tasks.
- **Celery + Redis Queue**: Offloading slow telemetry processing and external API calls to background workers.
- **Cache-Aside Pattern**: Checking Redis first before dispatching heavy background jobs.
- **Prompt Engineering**: Instructing LLMs (Gemini) to generate concise, contextual tactical responses.
- **Docker Compose**: Containerizing and networking an API service, background worker, and Redis broker.

---

## 🔄 Architecture Flow

```
User Request
    │
    ▼
FastAPI (API Gateway)
    │
    ├──► 1. Check Redis Cache ──[Hit]──► Return cached result immediately
    │
    └──► 2. [Miss] Push task to Redis Queue ──► Return Job ID to client
                                                      │
                                                      ▼
                                            Celery Worker
                                              ├── Fetch FastF1 telemetry
                                              ├── Call Gemini LLM
                                              └── Store result in Redis (TTL: 1h)
```

---

## 🚀 Quickstart

### 1. Clone & Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit [.env](file:///.env) with your details:
- `GEMINI_API_KEY`: Your Google AI Studio API key.
- `F1_USERNAME` / `F1_PASSWORD`: (Optional) Formula 1 Live Timing account.

### 2. Run with Docker Compose

```bash
docker compose up --build
```

This starts:
- **API**: `http://localhost:8000`
- **Worker**: Celery background consumer
- **Redis**: Port `6379`

---

## 📡 API Usage

### 1. Request Strategy Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/strategy?year=2023&race=Monza"
```

- **Cache Hit**: Returns the strategy & radio call immediately.
- **Cache Miss**: Returns a `job_id` and queues the task.

```json
{
  "job_id": "7a94b0d1-1234-4a25-9c5e-abcdef123456",
  "status": "PROCESSING",
  "source": "worker_queue"
}
```

### 2. Poll for Job Status

```bash
curl "http://localhost:8000/api/v1/jobs/YOUR_JOB_ID"
```

Once `status` is `COMPLETED`, you will receive the session summary and the AI-generated radio message. Subsequent requests for the same year and race will return instantly from cache!

---

## 📂 Project Structure

- [main.py](file:///main.py) — FastAPI endpoints, Redis cache checks, and job status polling.
- [worker.py](file:///worker.py) — Celery worker task integrating FastF1 and Google Gemini.
- [docker-compose.yml](file:///docker-compose.yml) — Container setup for Redis, API, and worker.
- [Dockerfile](file:///Dockerfile) — Python environment and system dependencies.
- [SPECIFICATION.md](file:///SPECIFICATION.md) — Detailed technical notes and initial architecture design.
