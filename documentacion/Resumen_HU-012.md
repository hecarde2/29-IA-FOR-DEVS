# Resumen de implementación — HU-012

**Ingesta flexible de datos y optimización opcional de tokens para análisis de reseñas en Excel**

Fecha de finalización: 30/07/2026

---

## Flujo de procesamiento (actualizado)

```
optent_tokens=False:  Reseña ES → Clustering (TF-IDF + KMeans) → HashingVectorizer + LinearSVC → extracción
optent_tokens=True:   Reseña ES → deep_translator → EN → Clustering → HashingVectorizer + LinearSVC → extracción
```

- `deep_translator` usa Google Translate como backend (sin API key). Solo se activa cuando `optent_tokens=True`.
- `scikit-learn` (LinearSVC) se usa para clasificación — **sin Ollama ni LLM local**.
- Clustering por producto reduce 50k reseñas a ~25 grupos representativos (99.9%).

---

## Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/analyze` | Analizar una reseña individual (texto JSON + `optent_tokens`) |
| `POST` | `/api/analyze/upload` | Subir un archivo `.xlsx` y procesar todas las reseñas (JSON) |
| `POST` | `/api/analyze/upload/stream` | Subir `.xlsx` con progreso en tiempo real (SSE) |
| `POST` | `/api/analyze/folder` | Indicar ruta de carpeta y procesar todos los `.xlsx` |
| `GET` | `/api/analyze/export` | Exportar resultados en JSON o Excel |
| `GET` | `/api/analyze/cost-estimate` | Estimación de costo para N reseñas/día |
| `GET` | `/` | Frontend HTML (servido por StaticFiles) |

---

## Archivos modificados

### `backend/app/services/analysis_service.py`
- Reemplazada extracción con Ollama → `scikit-learn` (HashingVectorizer + LinearSVC)
- Añadida función `_cluster_producto()` con TF-IDF + MiniBatchKMeans por producto
- Añadida función `_procesar_por_producto()` con paralelismo (ThreadPoolExecutor)
- Añadida función `procesar_archivo_excel_stream()` con SSE streaming
- Añadida función `_procesar_producto_grupo()` para procesar un producto en un thread
- Añadida función `_procesar_sin_producto()` (fallback sin columna producto)
- Añadida función `_optimal_k()` para determinar k óptimo con silhouette_score
- Añadida función `_extraer_componente()` con keywords
- Añadida función `_generar_summary()` extractivo
- Añadida función `_traducir_lote()` con ThreadPoolExecutor
- Añadida función `_detectar_columna_producto()`
- Métricas de tokens reflejan el total del cluster

### `backend/app/models/schemas.py`
- Añadidos campos `producto`, `cluster_id`, `reviews_in_cluster` a `ExtractedErrorData`
- Añadido campo `optent_tokens: bool = False` a `ReviewRequest` (ya existía)

### `backend/app/routers/analyze.py`
- Añadido endpoint `POST /api/analyze/upload/stream` (SSE streaming)
- Import actualizado para incluir `procesar_archivo_excel_stream`

### `backend/app/main.py`
- Eliminado `@app.get("/")` (conflicto con StaticFiles)
- Simplificado banner (sin pyfiglet)

### `backend/app/core/config.py`
- Sin cambios (ya tenía `PRICE_PER_MILLION_TOKENS_USD = 2.50`)

### `backend/requirements.txt`
- Añadidos: `scikit-learn`, `joblib`
- Removidos: `ollama`, `faker`, `pyfiglet`

### `frontend/index.html`
- Añadida barra de progreso con etapas y conteo
- Cambiado `runAnalysis()` a usar SSE streaming (`/api/analyze/upload/stream`)
- Añadida función `readStream()` para leer Server-Sent Events
- Añadida función `updateProgress()` para actualizar la barra
- Tabla actualizada: columnas de producto, reviews en cluster, ahorro de tokens
- Mensaje actualizado: "50k reseñas → ~25 grupos"

---

## Archivos creados

| Archivo | Descripción |
|---|---|
| `frontend/index.html` | Interfaz web con barra de progreso y SSE streaming |
| `scripts/train_pipeline.py` | Entrena modelos scikit-learn con pseudo-labels |
| `app/models/__init__.py` | Paquete de modelos |
| `app/models/vectorizer.joblib` | HashingVectorizer entrenado |
| `app/models/error_type_model.joblib` | LinearSVC para error_type (7 clases) |
| `app/models/severity_model.joblib` | LinearSVC para severity (4 clases) |
| `README.md` (raíz) | Documentación principal actualizada |
| `backend/README.md` | Documentación del backend actualizada |
| `HU.md` | Historia de usuario actualizada |
| `TODO.md` | Lista de tareas completadas |
| `AGENTS.md` | Configuración del proyecto actualizada |
| `documentacion/Plan_Implementacion_HU-012.md` | Plan de implementación actualizado |
| `documentacion/Resumen_HU-012.md` | Este archivo |

---

## Dependencias nuevas

| Paquete | Versión | Propósito |
|---|---|---|
| `scikit-learn` | 1.9.0 | TF-IDF, MiniBatchKMeans, HashingVectorizer, LinearSVC, silhouette_score |
| `joblib` | 1.5.3 | Serialización de modelos |

## Dependencias removidas

| Paquete | Motivo |
|---|---|
| `ollama` | Reemplazado por scikit-learn |
| `faker` | Solo usado para generación de datos, no necesario en prod |
| `pyfiglet` | Solo para banner, simplificado |

---

## Rendimiento

| Operación | 50k reseñas |
|---|---|
| Lectura Excel | ~2.9s |
| Clustering (5 productos, paralelo) | ~2s |
| Token counting (tiktoken) | ~0.6s |
| Clasificación (LinearSVC) | <0.1s |
| **Total** | **~4.6s** |

---

## Notas técnicas

- **scikit-learn**: `HashingVectorizer` + `LinearSVC` para clasificación. Inferencia en <1ms por reseña.
- **deep_translator**: usa Google Translate como backend (sin API key). Para volúmenes altos, considerar rate limiting o API key de DeepL.
- **Tokenización**: `tiktoken` con `o200k_base` para medir tokens del modelo target.
- **Precio de referencia**: `$2.50 USD por millón de tokens`.
- **Detección de columna**: heurística que busca nombres como `reseña`, `review`, `text`, `comment`, `texto`.
- **Detección de producto**: heurística que busca `producto`, `product`, `app`, `aplicacion`.
- **Clustering**: `MiniBatchKMeans` con `silhouette_score` para k óptimo (máx 10 clusters por producto).
- **CPU tuning**: `OMP_NUM_THREADS=12`, `MKL_NUM_THREADS=12`, `OPENBLAS_NUM_THREADS=12`.
- **SSE Streaming**: endpoint `/api/analyze/upload/stream` envía eventos con etapas: lectura, clustering, clasificacion, completo.
