#!/bin/bash

# Start Backend
echo "Starting Backend..."
# Add current directory to PYTHONPATH so 'backend' module can be found
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if venv exists, if not create it (optional, but good for isolation)
# python3 -m venv venv
# source venv/bin/activate
pip install -r backend/requirements.txt --pre

# Run uvicorn from the root directory
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "Backend running on PID $BACKEND_PID"
echo "Frontend running on PID $FRONTEND_PID"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

wait
