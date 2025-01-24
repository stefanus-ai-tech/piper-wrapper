#!/bin/bash

# Check if the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)."
  exit 1
fi

echo "Cleaning up Docker..."

# Stop all running containers
echo "Stopping all containers..."
docker ps -q | xargs -r docker stop

# Remove all containers
echo "Removing all containers..."
docker ps -aq | xargs -r docker rm -f

# Remove all images
echo "Removing all images..."
docker images -q | xargs -r docker rmi -f

# Remove all volumes
echo "Removing all volumes..."
docker volume ls -q | xargs -r docker volume rm

# Prune the system
echo "Pruning unused Docker data..."
docker system prune -a --volumes -f

echo "Docker cleanup complete!"

