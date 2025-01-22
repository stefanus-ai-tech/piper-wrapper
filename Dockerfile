# Single stage build for simplicity
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libssl1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY piper/piper ./piper/
COPY piper/lib* ./piper/
COPY piper/espeak-ng-data/ ./piper/espeak-ng-data/
COPY piper_models/ ./piper_models/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV LD_LIBRARY_PATH=/app/piper:$LD_LIBRARY_PATH

# Make Piper executable
RUN chmod +x piper/piper

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
