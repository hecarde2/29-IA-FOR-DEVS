# App Store Review Analyzer

API en FastAPI que analiza reseñas de usuarios de App Store desde archivos Excel.

## Características

- **Ingesta flexible**: archivo `.xlsx` individual o carpeta completa
- **Agrupación inteligente por producto**: reduce 50k reseñas a ~25 grupos representativos (99.9%)
- **Clasificación ML**: scikit-learn (TF-IDF + LinearSVC) para error_type y severity
- **Optimización de tokens**: métricas de ahorro ES→EN con `tiktoken`
- **Progreso en tiempo real**: SSE streaming con barra de progreso en el frontend
- **Traducción opcional**: deep-translator (Google Translate) cuando `optent_tokens=True`

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/analyze` | Analizar una reseña individual |
| `POST` | `/api/analyze/upload` | Subir `.xlsx` y analizar (respuesta JSON) |
| `POST` | `/api/analyze/upload/stream` | Subir `.xlsx` con progreso en tiempo real (SSE) |
| `POST` | `/api/analyze/folder` | Escanear carpeta con múltiples `.xlsx` |
| `GET` | `/api/analyze/export` | Exportar resultados en JSON o Excel |
| `GET` | `/api/analyze/cost-estimate` | Estimación de impacto económico |

## Flujo de procesamiento

```
Archivo .xlsx
     │
     ├── groupby(producto) → 5 grupos
     │
     ├── Por cada producto:
     │   ├─ TF-IDF (500 features, ngram 1-2)
     │   ├─ MiniBatchKMeans (k=5, auto)
     │   ├─ Seleccionar representante (más cercano al centroide)
     │   └─ Contar tokens de todo el cluster (tiktoken)
     │
     ├── HashingVectorizer (2^20 features)
     ├── LinearSVC → error_type (7 clases)
     ├── LinearSVC → severity (4 clases)
     ├── Keywords → component
     └── Plantilla → summary_en / summary_es
```

## Rendimiento

| Operación | 50k reseñas |
|---|---|
| Lectura Excel | ~2.9s |
| Clustering por producto (5× paralelo) | ~2s |
| Token counting (tiktoken) | ~0.6s |
| Clasificación (LinearSVC) | <0.1s |
| **Total** | **~4.6s** |

## Requisitos

- Python 3.12+
- `pip install -r backend/requirements.txt`
- (Opcional) Ollama no es necesario — todo con scikit-learn local

## Cómo correr

```bash
cd backend
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:8000/`

Más información en [backend/README.md](backend/README.md).
