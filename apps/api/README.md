# API development

From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn lenny_api.main:app --reload
```

Open `http://localhost:8000/docs` for the generated API contract.

