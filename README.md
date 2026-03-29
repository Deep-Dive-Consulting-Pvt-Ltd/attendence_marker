# Attendance Marker System

Face recognition attendance API built with FastAPI, MongoDB Atlas, and an MVC project structure.

## What Changed

- Migrated data layer from PostgreSQL/pgvector to MongoDB Atlas.
- Refactored backend into MVC-style modules:
  - `api/routers`
  - `controllers`
  - `services`
  - `repositories`
  - `core`
  - `db`
  - `ml`
- Added structured JSON logging and request ID middleware.
- Preserved existing endpoint paths and response contracts.

## Environment Variables

Create `.env` (or export in shell) with:

```bash
MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority"
MONGODB_DATABASE="attendance_db"
APP_HOST="0.0.0.0"
APP_PORT="8000"
DEFAULT_SESSION="2025-26"
CORS_ORIGINS="*"
```

## Install

```bash
cd attendence_marker/attendence_marker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open docs at `http://localhost:8000/docs`.

## Notes for MongoDB Atlas Vector Search

- The app stores a vector index manifest in `system_metadata`.
- Create Atlas Search index named `students_embedding_vector_index` on `students.embedding` (dimensions `512`, similarity `cosine`) in Atlas UI/API.
- Current attendance matching keeps historical in-memory scoring behavior for compatibility and stores embeddings in Mongo.
