# Python 3.10 slim base
FROM python:3.10-slim

# Install system dependencies required for OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Run FastAPI server
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
