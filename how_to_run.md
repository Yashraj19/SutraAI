# Terminal 1 - Backend
cd backend && source ../venv/bin/activate && uvicorn main:app --port 8000 --reload

# Terminal 2 - Frontend
cd frontend && npm run dev