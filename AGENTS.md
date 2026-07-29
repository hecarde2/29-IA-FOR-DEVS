# AGENTS.md — Project Instructions

## Project Overview

FastAPI backend + HTML frontend for analyzing App Store reviews from Excel files.
HU-012: Ingesta flexible de datos y optimización opcional de tokens.

## Architecture

- **Backend**: FastAPI in `backend/app/`
  - `app/main.py` — entry point, creates FastAPI app, includes routers
  - `app/routers/analyze.py` — endpoints under `/api` prefix
  - `app/services/analysis_service.py` — business logic (translation, extraction, token counting)
  - `app/models/schemas.py` — Pydantic request/response models
  - `app/core/config.py` — constants (token encoding, price, app metadata)
- **Frontend**: Static HTML in `frontend/` served by FastAPI StaticFiles
- **Scripts**: `backend/scripts/generar_excel.py` (data gen), `backend/scripts/procesar_excel_async.py` (batch client)
- **Data**: `backend/data/resenas_productos_50k.xlsx` — sample dataset
- **Docs**: `documentacion/` folder

## Key Dependencies

- `fastapi`, `uvicorn`, `pydantic` — web framework
- `tiktoken` — token counting with `o200k_base`
- `pandas`, `openpyxl` — Excel ingestion
- `ollama` — Ollama API for deepseek-r1:1.5b extraction
- `deep-translator` — Google Translate ES→EN (used when `optent_tokens=True`)
- `python-multipart` — file upload support
- `faker`, `httpx`, `tqdm` — data gen / async client / progress

## Ollama Setup

Model: `deepseek-r1:1.5b` (downloaded locally).
Ollama must be running at `http://127.0.0.1:11434`.

## Running the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Key Endpoints

- `POST /api/analyze` — single review analysis (with `optent_tokens`)
- `POST /api/analyze/upload` — single `.xlsx` file upload
- `POST /api/analyze/folder` — batch process folder of `.xlsx` files
- `GET /api/analyze/export` — export results as JSON or Excel
- `GET /api/analyze/cost-estimate` — economic impact estimate

## Translation Flow

```
optent_tokens=True:  ES → deep_translator → EN → deepseek-r1:1.5b → extraction
optent_tokens=False: ES → deepseek-r1:1.5b → extraction (no translation)
```

## Testing

- Run `python scripts/generar_excel.py` to generate test data
- Run `python scripts/procesar_excel_async.py` to send batch requests (backend must be running)
- Test endpoints via Swagger UI at `/docs`

## TODO

Full implementation plan in `TODO.md`