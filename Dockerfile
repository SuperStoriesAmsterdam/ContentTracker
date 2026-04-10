FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the data directory exists (SQLite database and document uploads live here)
RUN mkdir -p data/documents

EXPOSE 5000

# Gunicorn with 2 workers and a 120-second timeout.
# 120 seconds is necessary because Claude transcript extraction can take 10-30 seconds
# and the request is synchronous in v4.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--preload", "app:app"]
