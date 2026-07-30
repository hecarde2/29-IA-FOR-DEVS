# App Store Review Analyzer — Backend

API en FastAPI que analiza reseñas de usuarios: cuenta tokens (ES vs EN) con `tiktoken`,
agrupa reseñas por producto mediante clustering semántico (TF-IDF + KMeans), y extrae
datos estructurados del error reportado usando scikit-learn (LinearSVC).

## 1. Estructura de carpetas

```
backend/
├── app/                        # Backend (API)
│   ├── main.py                 # Punto de entrada: crea la app y conecta los routers
│   ├── core/
│   │   └── config.py           # Constantes / configuración
│   ├── models/
│   │   ├── __init__.py         # Paquete de modelos
│   │   ├── schemas.py          # Modelos Pydantic (request/response)
│   │   ├── vectorizer.joblib   # HashingVectorizer entrenado (2^20 features)
│   │   ├── error_type_model.joblib   # LinearSVC para error_type (7 clases)
│   │   └── severity_model.joblib     # LinearSVC para severity (4 clases)
│   ├── routers/
│   │   └── analyze.py          # Endpoints /api/analyze/*
│   └── services/
│       └── analysis_service.py # Lógica de negocio (tokens, clustering, clasificación)
├── scripts/                    # Herramientas externas
│   ├── generar_excel.py        # Genera datos de prueba (Excel)
│   ├── procesar_excel_async.py # Cliente que consume el backend en paralelo
│   └── train_pipeline.py       # Entrena modelos scikit-learn con pseudo-labels
├── data/
│   └── resenas_productos_50k.xlsx
├── requirements.txt
└── README.md
```

## 2. Flujo de datos

```
scripts/generar_excel.py
        │  genera
        ▼
data/resenas_productos_50k.xlsx
        │  lee
        ▼
scripts/procesar_excel_async.py  ──HTTP POST──►  app/main.py (FastAPI)
                                                         │ include_router
                                                         ▼
                                                  app/routers/analyze.py
                                                         │ llama a
                                                         ▼
                                              app/services/analysis_service.py
                                                         │ usa
                                                         ▼
                                              app/models/schemas.py (valida datos)
                                              app/models/*.joblib (modelos ML)
```

### Pipeline de análisis (por producto)

1. **Lectura Excel** — `pandas` + `openpyxl`
2. **Agrupación** — `groupby('producto')` → 5 grupos
3. **Clustering semántico** (por producto):
   - `TfidfVectorizer(max_features=500, ngram_range=(1,2))`
   - `MiniBatchKMeans(k=5, random_state=42)`
   - Selecciona representante: reseña más cercana al centroide
4. **Clasificación** (sobre representantes):
   - `HashingVectorizer(n_features=2^20)` → `LinearSVC` para `error_type`
   - `LinearSVC` para `severity`
   - Keywords → `component`
5. **Tokens** — `tiktoken` (o200k_base) sobre todo el cluster

## 3. Instalación

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Generar modelos (solo la primera vez)

Los modelos ya están incluidos en `app/models/`. Si necesitas regenerarlos:

```bash
cd backend
source venv/bin/activate
python scripts/train_pipeline.py
```

## 5. Levantar el backend

```bash
cd backend
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Frontend: `http://127.0.0.1:8000/` (HTML estático)

## 6. Endpoints

### POST `/api/analyze` — Análisis individual

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "La aplicación se cierra al subir una foto", "optent_tokens": false}'
```

### POST `/api/analyze/upload` — Subir archivo (respuesta JSON)

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/upload \
  -F "file=@resenas_productos_50k.xlsx" \
  -F "optent_tokens=false"
```

### POST `/api/analyze/upload/stream` — Subir archivo (progresso en tiempo real, SSE)

```bash
curl -N -X POST http://127.0.0.1:8000/api/analyze/upload/stream \
  -F "file=@resenas_productos_50k.xlsx" \
  -F "optent_tokens=false"
```

Devuelve eventos SSE con `stage` (lectura, clustering, clasificacion, completo) y progreso porcentual.

### POST `/api/analyze/folder` — Escanear carpeta

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/folder \
  -F "folder_path=/ruta/a/carpeta" \
  -F "optent_tokens=false"
```

### GET `/api/analyze/cost-estimate` — Estimación de costos

```bash
curl "http://127.0.0.1:8000/api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true"
```

### GET `/api/analyze/export` — Exportar resultados

```bash
curl "http://127.0.0.1:8000/api/analyze/export?format=json"
```

## 7. Esquema de respuesta

```json
{
  "total": 25,
  "results": [
    {
      "metrics": {
        "original_tokens": 142190,
        "translated_tokens": 142190,
        "tokens_saved_per_request": 142175
      },
      "extracted_data": {
        "error_type": "crash",
        "component": "perfil",
        "severity": "critical",
        "summary_en": "La aplicación se cierra inesperadamente...",
        "summary_es": "La aplicación se cierra inesperadamente...",
        "producto": "Audífonos Bluetooth Wireless",
        "cluster_id": 1,
        "reviews_in_cluster": 1465
      }
    }
  ]
}
```

## 8. Datos de prueba

```bash
python scripts/generar_excel.py       # Genera data/resenas_productos_50k.xlsx
python scripts/procesar_excel_async.py  # Cliente batch (requiere backend corriendo)
```

## 9. Notas técnicas

- **Sin Ollama/LLM local**: todo el procesamiento usa scikit-learn y keywords.
- **Paralelismo**: clustering por producto usa `ThreadPoolExecutor` (5 workers).
- **CPU tuning**: `OMP_NUM_THREADS=12`, `MKL_NUM_THREADS=12`, `OPENBLAS_NUM_THREADS=12`.
- **CORS**: abierto (`allow_origins=["*"]`).
- **Traducción**: `deep_translator` (Google Translate) solo cuando `optent_tokens=True`.
- **Streaming**: el endpoint `/upload/stream` usa SSE para progresso en tiempo real.
