#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# -------------------------------------------------------------------
#                      Configuration Section
# -------------------------------------------------------------------

PROJECT_DIR="/home/server/Documents/piper-wrapper"  # <--- UPDATED with absolute path
DOCKER_COMPOSE_FILE="docker-compose.yml"       # <--- Assuming your docker-compose.yml is in the project root

# --- Configuration for Static File Update ---
TEMP_STATIC_DIR="./temp_static"  # Temporary directory to collect static files
CONTAINER_NAME="piper-wrapper-app-1" # <--- IMPORTANT:  You might need to adjust this. See below.
STATIC_SOURCE_PATH="/app/static"   # Path to static files INSIDE the 'app' container
HOST_STATIC_DEST_PATH="./static"    # Path to your host's './static' directory

# -------------------------------------------------------------------
#                      Deployment Script Start
# -------------------------------------------------------------------

echo "-----------------------------------------------------"
echo "             Starting Deployment Script              "
echo "-----------------------------------------------------"
echo "Project Directory: ${PROJECT_DIR}"
echo "Docker Compose File: ${DOCKER_COMPOSE_FILE}"
echo ""

# --- Step 1: Navigate to project directory ---
echo "Step 1: Navigating to project directory..."
cd "${PROJECT_DIR}" || { echo "Error: Could not change directory to ${PROJECT_DIR}"; exit 1; }
echo "Current directory: $(pwd)"
echo ""

# --- Step 2: Stop existing Docker containers ---
echo "Step 2: Stopping existing Docker containers (docker-compose down)..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" down
echo "Docker Compose Down completed."
echo ""

# --- Step 2.5: Update Static Files on Host ---
echo "Step 2.5: Updating static files in '${HOST_STATIC_DEST_PATH}' directory..."

# --- ADD STATIC FILE UPDATE ---
echo "  - Creating temporary directory: ${TEMP_STATIC_DIR}"
mkdir -p "${TEMP_STATIC_DIR}"

echo "  - Copying static files from container '${CONTAINER_NAME}:${STATIC_SOURCE_PATH}' to '${TEMP_STATIC_DIR}'..."
docker cp "${CONTAINER_NAME}:${STATIC_SOURCE_PATH}" "${TEMP_STATIC_DIR}"

echo "  - Removing existing files in '${HOST_STATIC_DEST_PATH}'..."
rm -rf "${HOST_STATIC_DEST_PATH}"/*  # <--- CAREFUL! Double-check paths.

echo "  - Copying new static files from '${TEMP_STATIC_DIR}/static' to '${HOST_STATIC_DEST_PATH}'..."
if [ -d "${TEMP_STATIC_DIR}/static" ]; then # Check if 'static' directory was actually copied
  cp -r "${TEMP_STATIC_DIR}/static"/* "${HOST_STATIC_DEST_PATH}"
  echo "  - Static files updated in '${HOST_STATIC_DEST_PATH}'."
else
  echo "  - WARNING: No 'static' directory found in copied data from container. Static files might NOT be updated."
  echo "    Check if '${STATIC_SOURCE_PATH}' is the correct path inside your 'app' container."
fi

echo "  - Cleaning up temporary directory: ${TEMP_STATIC_DIR}"
rm -rf "${TEMP_STATIC_DIR}"
# --- END STATIC FILE UPDATE ---

echo "Static file update process completed."
echo ""


# --- Step 3: Build Docker images with no cache ---
echo "Step 3: Building Docker images (docker-compose build --no-cache)..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache
echo "Docker Compose Build completed."
echo ""

# --- Step 4: Start Docker containers in detached mode ---
echo "Step 4: Starting Docker containers in detached mode (docker-compose up -d)..."
docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d
echo "Docker Compose Up (detached) completed."
echo ""

echo "-----------------------------------------------------"
echo "              Deployment Script Finished              "
echo "-----------------------------------------------------"
echo "Application should be updated and running."
echo "Check http://localhost:8080 in your browser."
echo ""
echo "--- IMPORTANT NEXT STEPS FOR CI/CD ---"
echo "For a proper CI/CD pipeline:"
echo "1. Pre-build Docker images in a CI environment (like GitHub Actions)."
echo "2. Push these images to a Container Registry (like Docker Hub)."
echo "3. Modify docker-compose.yml to use 'image:' instead of 'build:' and specify image tags."
echo "4. Update this deploy.sh to 'docker-compose pull' the pre-built images instead of 'docker-compose build'."
echo "-----------------------------------------------------"

exit 0
