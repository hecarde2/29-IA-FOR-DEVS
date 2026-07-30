# Plan Implementación — HU-012

**Ingesta flexible de datos y optimización opcional de tokens para análisis de reseñas en Excel**

---

## Flujo de procesamiento (actualizado)

```
optent_tokens=False:  Reseña ES → Clustering (TF-IDF + KMeans) → HashingVectorizer + LinearSVC → extracción
optent_tokens=True:   Reseña ES → deep_translator → EN → Clustering → HashingVectorizer + LinearSVC → extracción
```

- `deep_translator` maneja ES→EN (Google Translate backend). Solo se usa cuando `optent_tokens=True`.
- `scikit-learn` (LinearSVC) se usa para clasificación — **sin Ollama ni LLM local**.
- Clustering por producto reduce 50k reseñas a ~25 grupos representativos (99.9%).

---

## Requisitos previos

- Python 3.12+
- `pip install -r backend/requirements.txt`
- (Opcional) Ollama **no es necesario**

---

## Fase 1 — Integración scikit-learn (reemplaza Ollama)

**Objetivo:** Reemplazar Ollama/deepseek-r1:1.5b con scikit-learn para clasificación instantánea.

### Cambios en backend

- **`backend/scripts/train_pipeline.py`** (nuevo):
  - Lee `data/resenas_productos_50k.xlsx`
  - Genera pseudo-labels con keywords para `error_type` (7 clases) y `severity` (4 clases)
  - Entrena `LinearSVC` con `HashingVectorizer`
  - Guarda modelos con `joblib` en `app/models/`

- **`backend/app/models/`**:
  - `vectorizer.joblib` — `HashingVectorizer(n_features=2^20, ngram_range=(1,2))`
  - `error_type_model.joblib` — `LinearSVC` (7 clases: crash, bug, performance, ui, login, payment, other)
  - `severity_model.joblib` — `LinearSVC` (4 clases: low, medium, high, critical)

- **`backend/requirements.txt`**:
  - Añadir `scikit-learn`, `joblib`
  - Remover `ollama`, `faker`, `pyfiglet`

---

## Fase 2 — Endpoint de upload de archivo (Modo A)

**Objetivo:** Permitir cargar un `.xlsx` individual.

### Cambios en backend

- Nuevo endpoint: `POST /api/analyze/upload`
  - Recibe `UploadFile` (multipart/form-data)
  - Lee el `.xlsx` con `pandas` + `openpyxl`
  - Detecta automáticamente la columna de reseñas y producto
  - Agrupa por producto → clustering → clasificación
  - Retorna `BatchAnalysisResponse`

- Nuevo endpoint: `POST /api/analyze/upload/stream`
  - Variante SSE con progreso en tiempo real
  - Eventos: `lectura`, `clustering`, `clasificacion`, `completo`

---

## Fase 3 — Endpoint de escaneo de carpeta (Modo B)

**Objetivo:** Indicar una ruta de carpeta y procesar todos los `.xlsx` dentro.

### Cambios en backend

- Endpoint: `POST /api/analyze/folder`
  - Recibe `{ "folder_path": str, "optent_tokens": bool }`
  - Usa `pathlib.Path` para listar todos los `.xlsx`
  - Procesa cada archivo consolidando resultados

---

## Fase 4 — Parámetro `optent_tokens`

**Objetivo:** Controlar si se aplica traducción previa o no.

| `optent_tokens` | Flujo |
|---|---|
| `True` | ES → `deep_translator` → EN → clasificación |
| `False` | ES → clasificación directa |

### Impacto

- Con `optent_tokens=True`: texto traducido a EN, tokens medidos sobre ambos idiomas
- Con `optent_tokens=False`: texto original EN, tokens iguales ES/EN
- Ambos caminos se comparan en la métrica de costo económico

---

## Fase 5 — Export JSON/Excel

**Objetivo:** Exportar resultados procesados en formato limpio.

### Endpoint

- `GET /api/analyze/export?format=json|excel`
  - `format=json`: devuelve JSON con schema `{"error_type", "component", "severity", "summary_en", "summary_es", "producto", "cluster_id", "reviews_in_cluster"}`
  - `format=excel`: descarga archivo `.xlsx`

---

## Fase 6 — Análisis de impacto económico

**Objetivo:** Calcular volumen de tokens y diferencia de costo para N reseñas/día.

### Lógica

```
costo_directo = (tokens_es_total / 1_000_000) * 2.50
costo_optimizado = (tokens_en_total / 1_000_000) * 2.50
ahorro_diario = costo_directo - costo_optimizado
```

### Endpoint

- `GET /api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true|false`

---

## Fase 7 — Agrupación semántica por producto (Clustering)

**Objetivo:** Reducir 50k reseñas a ~25 grupos representativos preservando información.

### Pipeline por producto

1. `groupby('producto')` → 5 grupos
2. Por cada producto:
   - `TfidfVectorizer(max_features=500, ngram_range=(1,2))`
   - `MiniBatchKMeans(k=5, random_state=42)`
   - k óptimo determinado automáticamente (máx 10)
   - Seleccionar representante: reseña más cercana al centroide
3. Clasificar solo los representantes con `HashingVectorizer + LinearSVC`
4. Contar tokens de TODO el cluster (no solo el representante)

### Resultado esperado

- 50k reseñas → ~25 grupos (99.9% de reducción)
- Métricas de tokens reflejan el total del cluster

---

## Fase 8 — Progreso en tiempo real (SSE)

**Objetivo:** Mostrar progreso del análisis en el frontend.

### Endpoint SSE

- `POST /api/analyze/upload/stream`
- `StreamingResponse` con media type `text/event-stream`
- Eventos:
  ```
  event: progress
  data: {"stage": "lectura", "message": "...", "progress": 3, "total": 37596, "processed": 0}

  event: progress
  data: {"stage": "clustering", "message": "Agrupando por producto...", "progress": 8}

  event: progress
  data: {"stage": "completo", "message": "37596 → 25 grupos", "progress": 100, "results": [...], "timings": {...}}
  ```

---

## Fase 9 — Frontend HTML

**Objetivo:** Interfaz web para interactuar con el backend.

### Archivo

- `frontend/index.html` — página única servida por FastAPI como `StaticFiles`

### Elementos de UI

1. **Selector de modo**: Modo A (archivo) / Modo B (carpeta)
2. **Input de archivo** con drag-and-drop
3. **Input de ruta de carpeta**
4. **Toggle `optent_tokens`**
5. **Botón "Ejecutar análisis"**
6. **Barra de progreso** con etapa actual y count procesado/total
7. **Tabla de resultados**: producto, reseña representativa, error_type, severity, reviews en cluster, tokens, ahorro
8. **Panel de métricas agregadas**
9. **Botones de export** (JSON / Excel)
10. **Indicador de estado** (cargando / completo / error)

---

## Fase 10 — Paralelismo y optimización de CPU

**Objetivo:** Aprovechar al máximo los núcleos de CPU.

### Estrategias

- `ThreadPoolExecutor(max_workers=5)` para clustering por producto (paralelo)
- `OMP_NUM_THREADS=12`, `MKL_NUM_THREADS=12`, `OPENBLAS_NUM_THREADS=12`
- `HashingVectorizer` (stateless, sin vocabulario)
- `MiniBatchKMeans` (más rápido que KMeans para grandes datasets)
- Batch processing: `vectorizer.transform()` + `clf.predict()` sobre todos los datos a la vez

---

## Fase 11 — Actualización de `requirements.txt`

### Dependencias actuales

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
tiktoken==0.8.0
pandas==2.2.3
openpyxl==3.1.5
httpx==0.28.1
tqdm==4.67.1
deep-translator==1.11.4
python-multipart==0.0.18
scikit-learn==1.9.0
joblib==1.5.3
```

---

## Fase 12 — Documentación

### Archivos actualizados

| Archivo | Contenido |
|---|---|
| `README.md` (raíz) | Descripción general, endpoints, flujo, rendimiento |
| `backend/README.md` | Estructura, instalación, endpoints, schema, notas técnicas |
| `HU.md` | Historia de usuario con criterios de aceptación |
| `TODO.md` | Lista de tareas completadas |
| `AGENTS.md` | Configuración del proyecto para agentes |
| `documentacion/Plan_Implementacion_HU-012.md` | Este archivo |
| `documentacion/Resumen_HU-012.md` | Resumen de cambios |

---

## Orden de ejecución recomendado

| Fase | Descripción | Estado |
|---|---|---|
| 1 | Integración scikit-learn (reemplaza Ollama) | ✅ Completado |
| 2 | Endpoint de upload de archivo (Modo A) | ✅ Completado |
| 3 | Endpoint de escaneo de carpeta (Modo B) | ✅ Completado |
| 4 | Parámetro `optent_tokens` | ✅ Completado |
| 5 | Export JSON/Excel | ✅ Completado |
| 6 | Análisis de impacto económico | ✅ Completado |
| 7 | Agrupación semántica por producto | ✅ Completado |
| 8 | Progreso en tiempo real (SSE) | ✅ Completado |
| 9 | Frontend HTML | ✅ Completado |
| 10 | Paralelismo y optimización de CPU | ✅ Completado |
| 11 | Actualización de requirements.txt | ✅ Completado |
| 12 | Documentación | ✅ Completado |

---

## Notas técnicas

- **scikit-learn**: `HashingVectorizer` + `LinearSVC` para clasificación. Inferencia en <1ms por reseña.
- **deep_translator**: usa Google Translate como backend (sin API key). Para volúmenes altos, considerar rate limiting o API key de DeepL.
- **Tokenización**: `tiktoken` con `o200k_base` para medir tokens del modelo target.
- **Precio de referencia**: `$2.50 USD por millón de tokens`.
- **Detección de columna**: heurística que busca nombres como `reseña`, `review`, `text`, `comment`, `texto`.
- **Detección de producto**: heurística que busca `producto`, `product`, `app`, `aplicacion`.
- **Clustering**: `MiniBatchKMeans` con `silhouette_score` para k óptimo (máx 10 clusters por producto).
