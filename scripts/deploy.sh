#!/bin/bash

# Exit on any error
set -e

# Load environment variables from .env.prod
export $(grep -v '^#' .env.prod | xargs)

# Pull latest changes
git pull origin main

# Build and start the containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check if containers are running
echo "Checking container status..."
sleep 10
docker ps

# Print logs for inspection
echo "Showing recent logs from containers:"
docker-compose -f docker-compose.prod.yml logs --tail=50

echo "Deployment completed successfully!"