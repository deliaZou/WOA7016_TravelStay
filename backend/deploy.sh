#!/bin/bash

# =====================================================================
# 🚀 TravelStay Backend Docker One-Click Deployment Script
# =====================================================================

# Define text colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Container and image configuration
CONTAINER_NAME="travelstay-app"
IMAGE_NAME="travelstay-backend"
PORT_MAPPING="8000:8000"

echo -e "${YELLOW}[1/5] 📥 Pulling the latest code from GitHub...${NC}"
git pull
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull failed! Please check your repository permissions or network connectivty.${NC}"
    exit 1
fi

echo -e "${YELLOW}[2/5] 🛑 Cleaning up the old Docker container...${NC}"
# Check if the container exists; if yes, stop and remove it
if [ "$(sudo docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo -e "Found existing container: ${CONTAINER_NAME}. Stopping and removing..."
    sudo docker stop ${CONTAINER_NAME} > /dev/null
    sudo docker rm ${CONTAINER_NAME} > /dev/null
    echo -e "${GREEN}✓ Old container successfully removed.${NC}"
else
    echo -e "No existing container found. Skipping cleanup step."
fi

echo -e "${YELLOW}[3/5] 🏗️ Building the new Docker image (processing requirements.txt)...${NC}"
sudo docker build -t ${IMAGE_NAME} .
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed! Please check your Dockerfile or code syntax error.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker image built successfully.${NC}"

echo -e "${YELLOW}[4/5] ▶️ Launching the new Docker container...${NC}"
sudo docker run -d -p ${PORT_MAPPING} --name ${CONTAINER_NAME} ${IMAGE_NAME}
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Container startup failed! Port 8000 might already be occupied.${NC}"
    exit 1
fi

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}🚀 [SUCCESS] Deployment completed successfully!${NC}"
echo -e "${GREEN}The backend service is now running on port: ${PORT_MAPPING}${NC}"
echo -e "${GREEN}======================================================${NC}"

echo -e "${YELLOW}[5/5] 📋 Displaying the last 10 lines of logs (Press Ctrl+C to exit):${NC}"
echo "------------------------------------------------------"
sudo docker logs --tail 10 ${CONTAINER_NAME}
echo "------------------------------------------------------"
# Keep tracking logs in real-time
#sudo docker logs -f ${CONTAINER_NAME}