# Base image
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libssl1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project for production image
# In CI/CD, this will copy the code as it is at the time of image build.
COPY . .

# Set environment variables
ENV LD_LIBRARY_PATH=/app/piper:$LD_LIBRARY_PATH

# Make Piper executable
RUN chmod +x piper/piper

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app", "--timeout", "600"]
