# TODO — HU-012

> **Estado: COMPLETADO** — Todas las fases implementadas (30/07/2026)

---

## Fase 1: Integración scikit-learn (reemplaza Ollama)
- [x] Remplazar `_extraer_datos_error()` de Ollama → scikit-learn (TF-IDF + LinearSVC)
- [x] Generar pseudo-labels con keywords para entrenamiento
- [x] Entrenar `LinearSVC` para `error_type` (7 clases) y `severity` (4 clases)
- [x] Guardar modelos con `joblib` en `app/models/`
- [x] Añadir `scikit-learn` y `joblib` a `requirements.txt`
- [x] Remover `ollama` y `pyfiglet` de `requirements.txt`

## Fase 2: Endpoint de upload de archivo (Modo A)
- [x] Nuevo endpoint `POST /api/analyze/upload` con `UploadFile`
- [x] Nuevo endpoint `POST /api/analyze/upload/stream` con SSE (progresso en tiempo real)
- [x] Leer `.xlsx` con `pandas` + `openpyxl`
- [x] Detección automática de columna de reseñas y producto
- [x] Procesar en batch y retornar lista de `AnalysisResponse`
- [x] Añadir `python-multipart==0.0.18` a `requirements.txt`

## Fase 3: Endpoint de escaneo de carpeta (Modo B)
- [x] Nuevo endpoint `POST /api/analyze/folder`
- [x] Recibir `folder_path` + `optent_tokens`
- [x] Usar `pathlib` para listar todos los `.xlsx` en la carpeta
- [x] Validar que la ruta exista y sea un directorio
- [x] Consolidar resultados de todos los archivos

## Fase 4: Parámetro `optent_tokens`
- [x] Actualizar `ReviewRequest` schema con campo `optent_tokens: bool = False`
- [x] Lógica de ramificación en `analysis_service.py`
- [x] Actualizar endpoint `/api/analyze` para aceptar el nuevo campo

## Fase 5: Export JSON/Excel
- [x] Nuevo endpoint `GET /api/analyze/export`
- [x] Soporte `?format=json` y `?format=excel`
- [x] Retornar JSON con schema limpio

## Fase 6: Análisis de impacto económico
- [x] Nuevo endpoint `GET /api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true|false`
- [x] Calcular tokens ES y EN estimados
- [x] Calcular costo directo vs optimizado
- [x] Retornar ahorro diario/mensual/anual a `$2.50/M tokens`

## Fase 7: Agrupación semántica por producto (Clustering)
- [x] `groupby('producto')` → 5 grupos
- [x] `TfidfVectorizer` + `MiniBatchKMeans` por producto
- [x] k óptimo con `silhouette_score` (máx 10 clusters)
- [x] Seleccionar representante (más cercano al centroide)
- [x] Contar tokens de todo el cluster (no solo el representante)
- [x] Añadir `producto`, `cluster_id`, `reviews_in_cluster` al schema

## Fase 8: Progreso en tiempo real (SSE)
- [x] Endpoint `POST /api/analyze/upload/stream` con `StreamingResponse`
- [x] Eventos SSE: lectura, clustering, clasificacion, completo
- [x] Barra de progreso en frontend con `fetch()` + `ReadableStream`
- [x] Mostrar etapa actual, count procesado/total

## Fase 9: Frontend HTML
- [x] Crear `frontend/index.html`
- [x] Selector de modo (Modo A / Modo B)
- [x] Input de archivo `.xlsx` (Modo A) con drag-and-drop
- [x] Input de ruta de carpeta (Modo B)
- [x] Toggle `optent_tokens`
- [x] Botón "Ejecutar análisis"
- [x] Barra de progreso con etapas y conteo
- [x] Tabla de resultados: producto, reseña, error_type, severity, reviews en cluster, tokens, ahorro
- [x] Panel de métricas agregadas
- [x] Botón de export JSON/Excel

## Fase 10: Paralelismo y optimización de CPU
- [x] `ThreadPoolExecutor` para clustering por producto (5 workers)
- [x] `OMP_NUM_THREADS=12`, `MKL_NUM_THREADS=12`, `OPENBLAS_NUM_THREADS=12`
- [x] Batch processing: vectorizer.transform() + clf.predict() sobre todos los datos
- [x] HashingVectorizer (stateless, sin vocabulario)
- [x] Benchmark de cada etapa

## Fase 11: Actualizar requirements.txt
- [x] Añadir `scikit-learn`, `joblib`
- [x] Remover `ollama`, `faker`, `pyfiglet`
- [x] Verificar compatibilidad con Python 3.12+

## Fase 12: Documentación
- [x] Actualizar `README.md` (raíz)
- [x] Actualizar `backend/README.md`
- [x] Actualizar `HU.md`
- [x] Actualizar `AGENTS.md`
- [x] Actualizar `TODO.md`
