#!/bin/bash

# Pune Disaster Intelligence Platform - Quick Start Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Pune Disaster Intelligence Platform...${NC}"

# 1. Start Backend
echo -e "${GREEN}📡 Launching Backend Server...${NC}"
cd "disaster-intelligence-platform/backend"
source venv/bin/activate
# Run uvicorn in background and redirect output to logs
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# 2. Start Frontend
echo -e "${GREEN}💻 Launching Frontend Dashboard...${NC}"
cd "app"
# Run npm dev in background
npm run dev -- --host > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "\n${BLUE}✅ All services initiated!${NC}"
echo -e "--------------------------------------------------"
echo -e "🔗 ${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "🔗 ${GREEN}Backend: ${NC} http://localhost:8000"
echo -e "🔗 ${GREEN}API Docs:${NC} http://localhost:8000/docs"
echo -e "--------------------------------------------------"
echo -e "📝 Logs are being written to ${BLUE}backend.log${NC} and ${BLUE}frontend.log${NC}"
echo -e "💡 To stop all services, run: ${BLUE}kill $BACKEND_PID $FRONTEND_PID${NC}"

# Keep script alive until interrupted
wait
