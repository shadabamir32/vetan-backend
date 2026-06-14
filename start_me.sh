#!/bin/bash
# Vetan — Start Script
# Run from the project root: bash start_me.sh

set -e

echo "🚀  Starting Vetan..."

# 0. Setup venv and activate it
if [ ! -d ".venv" ]; then
  echo "🐍  Creating virtual environment..."
  python -m venv .venv
fi

echo "🐍  Activating virtual environment..."
export PATH="$(pwd)/.venv/Scripts:$(pwd)/.venv/bin:$PATH"

# 1. Install Python deps
echo "📦  Installing Python dependencies..."
pip install -r requirements.txt -q

# 2. Run database migrations
echo "🔧  Running database migrations..."
python run_migrations.py

# 3. Seed database
echo "🌱  Seeding database..."
python seed_run.py

# 4. Install frontend deps
echo "⚛️   Installing frontend dependencies..."
cd app
npm install --silent
cd ..

# 5. Start both servers
echo "✅  Starting backend  → http://localhost:8000"
echo "✅  Starting frontend → http://localhost:5173"

uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd app
npx vite &
FRONTEND_PID=$!
cd ..

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
echo "Press Ctrl+C to stop both servers."
wait
