#!/bin/bash
set -e

# ---------------------------
# Configuration
# ---------------------------
PROJECT_DIR="/home/server/Documents/piper-wrapper"  # Your project directory
DOCKER_COMPOSE_FILE="docker-compose.yml"            # Your compose file name
SERVICE_NAME="app"                                  # Your app service name
STATIC_SOURCE="/app/static"                         # Container static path
HOST_STATIC_DIR="./static"                          # Host static directory
TIMEOUT_SECONDS=30                                  # Max wait for container
# ---------------------------

echo "=== Starting Deployment ==="
echo "Project: ${PROJECT_DIR}"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "----------------------------"

cd "${PROJECT_DIR}" || { echo "! Failed to enter project directory"; exit 1; }

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" down

# Rebuild with clean build cache
echo "Rebuilding containers..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache

# Start new containers
echo "Starting containers in detached mode..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d

# Get app container ID
echo "Finding application container..."
CONTAINER_ID=$(docker-compose -f "${DOCKER_COMPOSE_FILE}" ps -q "${SERVICE_NAME}")

# Wait for container to be running
echo "Waiting for container to start (max ${TIMEOUT_SECONDS}s)..."
timeout=${TIMEOUT_SECONDS}
while [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_ID}" 2>/dev/null)" != "true" ]; do
  if [ "$timeout" -le 0 ]; then
    echo "! Container failed to start"
    exit 1
  fi
  sleep 1
  ((timeout--))
done

# Verify static directory exists in container
echo "Checking for static files in container..."
if ! docker exec "${CONTAINER_ID}" test -d "${STATIC_SOURCE}"; then
  echo "! Static directory missing in container: ${STATIC_SOURCE}"
  exit 1
fi

# Create backup of current static files
echo "Creating backup of static files..."
backup_dir="./static_backup_$(date +%s)"
mkdir -p "${backup_dir}"
cp -r "${HOST_STATIC_DIR}/." "${backup_dir}/" 2>/dev/null || true

# Copy fresh static files from container
echo "Updating static files..."
mkdir -p "${HOST_STATIC_DIR}"
docker cp "${CONTAINER_ID}:${STATIC_SOURCE}/." "${HOST_STATIC_DIR}/"

echo "----------------------------"
echo "Deployment completed successfully!"
echo "Static files updated: ${HOST_STATIC_DIR}"
echo "Backup created: ${backup_dir}"
echo "Check application at http://localhost:8080"
