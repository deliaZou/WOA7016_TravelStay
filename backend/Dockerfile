# 1. official light Python image
FROM python:3.10-slim

# 2. WORKDIR in container
WORKDIR /app

# 3. copy local repliance to container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 4. expose FastAPI  8000 port
EXPOSE 8000

# 5. active, default setting by config.py: RUNNING_ENV
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]