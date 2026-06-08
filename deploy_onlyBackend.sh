#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ==========================================
# 1. Pull latest code from GitHub
# ==========================================
echo -e "${YELLOW}[1/4] Pulling latest code from Git...${NC}"
git pull
if [ $? -ne 0 ]; then
    echo -e "${RED}Git pull failed!${NC}"
    exit 1
fi

# ==========================================
# 2. Build and restart Backend Container
# ==========================================
echo -e "${YELLOW}[2/4] Restarting Backend (FastAPI)...${NC}"
# Stop and remove old container if exists
if [ "$(sudo docker ps -aq -f name=travelstay-app)" ]; then
    sudo docker stop travelstay-app > /dev/null
    sudo docker rm travelstay-app > /dev/null
fi

# Move to backend folder to build image
cd backend
sudo docker build -t travelstay-backend .
if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi
cd ..

# Run new backend container
sudo docker run -d -p 8000:8000 --name travelstay-app travelstay-backend
echo -e "${GREEN}✓ Backend is running on port 8000.${NC}"



# ==========================================
# 4. Status Check
# ==========================================
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}🚀 ALL SERVICES DEPLOYED SUCCESSFULLY!${NC}"
echo -e "${GREEN}FastAPI: http://localhost:8000${NC}"
echo -e "${GREEN}Grafana: http://localhost:3000${NC}"
echo -e "${GREEN}=======================================${NC}"

#echo -e "${YELLOW}[4/4] Showing recent logs of FastAPI...${NC}"
#sudo docker logs --tail 10 travelstay-app