# API development

From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn lenny_api.main:app --reload
```

Open `http://localhost:8000/docs` for the generated API contract.

Before the first run, set `DATABASE_URL` and apply migrations:

```powershell
alembic upgrade head
```

The readiness endpoint returns HTTP 503 when PostgreSQL cannot be reached; liveness remains available for process diagnostics.
