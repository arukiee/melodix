FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build and audio dependencies (gcc, libpq-dev, ffmpeg, libsndfile1)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
