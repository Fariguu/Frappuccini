# Project Monorepo (FastAPI + Vite)

This project is a monorepo managed with Turborepo.

## Project Structure
- `apps/frontend`: Vite project (React + TypeScript).
- `apps/backend`: Python project (FastAPI).

## Requirements
- Node.js (npm)
- Python 3.7+
- Turborepo (`npm install -g turbo`, though it's also in devDependencies)

## Setup

### 1. Install Node Dependencies
Run this in the root directory:
```bash
npm install
```

### 2. Setup Python Backend
Create a virtual environment and install dependencies:
```bash
cd apps/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Project
You can run both projects in parallel using the global `dev` script in the root:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.
The backend will be available at `http://localhost:8000`.
The frontend is configured to proxy `/api` calls to the backend.

## Turbo CLI
You can also run tasks for specific apps:
```bash
# Run only frontend
npx turbo run dev --filter=frontend

# Run only backend
npx turbo run dev --filter=backend
```
