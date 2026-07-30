# AGENTS.md — Project Instructions

## Project Overview

FastAPI backend + HTML frontend for analyzing App Store reviews from Excel files.
HU-012: Ingesta flexible de datos y optimización opcional de tokens.

## Architecture

- **Backend**: FastAPI in `backend/app/`
  - `app/main.py` — entry point, creates FastAPI app, includes routers
  - `app/routers/analyze.py` — endpoints under `/api` prefix
    - `POST /api/analyze` — single review analysis
    - `POST /api/analyze/upload` — single `.xlsx` file upload (JSON response)
    - `POST /api/analyze/upload/stream` — file upload with SSE progress streaming
    - `POST /api/analyze/folder` — batch process folder of `.xlsx` files
    - `GET /api/analyze/export` — export results as JSON or Excel
    - `GET /api/analyze/cost-estimate` — economic impact estimate
  - `app/services/analysis_service.py` — business logic (clustering, classification, token counting)
  - `app/models/schemas.py` — Pydantic request/response models
  - `app/models/*.joblib` — trained scikit-learn models (vectorizer, LinearSVC classifiers)
  - `app/core/config.py` — constants (token encoding, price, app metadata)
- **Frontend**: Static HTML in `frontend/` served by FastAPI StaticFiles
  - `frontend/index.html` — progress bar, streaming SSE, results table
- **Scripts**: `backend/scripts/`
  - `generar_excel.py` — data generation
  - `procesar_excel_async.py` — batch client
  - `train_pipeline.py` — train scikit-learn models with pseudo-labels
- **Data**: `backend/data/resenas_productos_50k.xlsx` — sample dataset (50k reviews, 5 products)
- **Docs**: `documentacion/` folder

## Key Dependencies

- `fastapi`, `uvicorn`, `pydantic` — web framework
- `tiktoken` — token counting with `o200k_base`
- `pandas`, `openpyxl` — Excel ingestion
- `scikit-learn` — TF-IDF, MiniBatchKMeans, HashingVectorizer, LinearSVC
- `joblib` — model serialization
- `deep-translator` — Google Translate ES→EN (used when `optent_tokens=True`)
- `python-multipart` — file upload support

## Ollama Setup

**No longer required.** The system now uses scikit-learn (LinearSVC) for classification
instead of deepseek-r1:1.5b via Ollama. This improves performance from ~3-5s per
review to <1ms per review.

## CPU Configuration

Set these environment variables for optimal performance:
```bash
export OMP_NUM_THREADS=12
export MKL_NUM_THREADS=12
export OPENBLAS_NUM_THREADS=12
```

## Running the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Processing Pipeline

```
Archivo .xlsx
     │
     ├── groupby(producto) → N grupos
     │
     ├── Por cada producto (ThreadPool paralelo):
     │   ├─ TfidfVectorizer + MiniBatchKMeans → clusters semánticos
     │   ├─ Seleccionar representante (más cercano al centroide)
     │   └─ Contar tokens de todo el cluster (tiktoken)
     │
     ├── HashingVectorizer (batch) → LinearSVC → error_type + severity
     ├── Keywords → component
     └── Plantilla → summary_en / summary_es
```

## Training Pipeline

To regenerate models (one-time setup):
```bash
cd backend
python scripts/train_pipeline.py
```

This script:
1. Reads `data/resenas_productos_50k.xlsx`
2. Generates pseudo-labels using keyword-based rules
3. Trains `LinearSVC` classifiers for `error_type` (7 classes) and `severity` (4 classes)
4. Saves models to `app/models/`

## Testing

- Run `python scripts/generar_excel.py` to generate test data
- Run `python scripts/procesar_excel_async.py` to send batch requests (backend must be running)
- Test endpoints via Swagger UI at `/docs`

## Performance

| Operation | 50k reviews |
|---|---|
| Read Excel | ~2.9s |
| Clustering (5 products, parallel) | ~2s |
| Token counting (tiktoken) | ~0.6s |
| Classification | <0.1s |
| **Total** | **~4.6s** |

## Output Schema

Each result includes:
- `error_type`: crash, bug, performance, ui, login, payment, other
- `component`: login/auth, perfil, busqueda, pago/factura, navegacion, etc.
- `severity`: low, medium, high, critical
- `summary_en` / `summary_es`: extractive summary (first ~100 chars)
- `producto`: product name from Excel
- `cluster_id`: KMeans cluster ID within product
- `reviews_in_cluster`: number of original reviews represented

## SSE Streaming

The `/api/analyze/upload/stream` endpoint returns Server-Sent Events:
```
event: progress
data: {"stage": "lectura", "message": "...", "progress": 3, "total": 37596, "processed": 0}

event: progress
data: {"stage": "clustering", "message": "Agrupando por producto...", "progress": 8}

event: progress
data: {"stage": "completo", "message": "Completado: 37596 → 25 grupos", "progress": 100, "results": [...], "timings": {...}}
```
