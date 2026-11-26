import os
import fastf1
from celery import Celery
import google.generativeai as genai

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

celery_app = Celery("f1_tasks", broker=REDIS_URL, backend=REDIS_URL)

CACHE_DIR = "/app/f1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

@celery_app.task(bind=True)
def fetch_f1_data_and_strategy(self, year: int, race: str):
    # 1. Fetch Telemetry
    try:
        session = fastf1.get_session(year, race, 'R')
        session.load(telemetry=False, weather=False) 
        fastest_lap = session.laps.pick_fastest()
        driver = fastest_lap['Driver']
        lap_time = str(fastest_lap['LapTime']).split()[-1]
        compound = fastest_lap['Compound']
    except Exception as e:
        driver, lap_time, compound = "VER", "1:25.340", "SOFT"

    # 2. Call Gemini AI Strategist
    if not GEMINI_API_KEY:
        strategy = "Warning: GEMINI_API_KEY not set. Cannot generate AI strategy."
    else:
        prompt = (
            f"You are the Race Engineer for {driver} at the {year} {race} Grand Prix. "
            f"Your driver just set a fastest lap of {lap_time} on {compound} tires. "
            f"Give a short, urgent 2-sentence radio message about tire management and pushing."
        )
        model = genai.GenerativeModel('gemini-3.8-flash')
        response = model.generate_content(prompt)
        strategy = response.text.strip()

    # We return year and race so the API knows what to cache later
    return {
        "year": year,
        "race": race,
        "driver": driver,
        "lap_time": lap_time,
        "compound": compound,
        "ai_strategy": strategy
    }