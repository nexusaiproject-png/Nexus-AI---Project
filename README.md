# Nexus AI Workspace

Nexus is an AI Workspace / Digital Employee platform. The backend is designed to grow into a permission-aware system that can work with email, calendar, tasks, projects, meetings, files, reminders, and automation.

## Backend foundation

The repository currently contains the minimal FastAPI foundation required for cloud development:

- FastAPI application in `main.py`
- `GET /`
- `GET /hello`
- `GET /health`
- Pytest tests
- Environment template
- Python dependency list

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the FastAPI documentation.

## Test

```bash
pytest -q
```

## Project direction

The architecture will evolve in small, testable steps. Sensitive agent operations must be permission-aware and require confirmation where appropriate. Developer-agent execution must eventually run in an isolated, controlled workspace rather than directly on an untrusted host.
