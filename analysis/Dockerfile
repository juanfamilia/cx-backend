FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including FFmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
COPY uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

# Copy application code
COPY app/ ./app/
COPY analysis/ ./analysis/
COPY shared/ ./shared/

# Expose port
EXPOSE 8001

# Start command for analysis service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
