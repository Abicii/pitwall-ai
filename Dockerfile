# 1. The Base Image
FROM python:3.11-slim

# 2. The Working Directory
WORKDIR /app

# 3. Cache Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy Source Code
COPY main.py .

# 5. Execution Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]