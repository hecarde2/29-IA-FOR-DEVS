# Resumen de implementación — HU-012

**Ingesta flexible de datos y optimización opcional de tokens para análisis de reseñas en Excel**

Fecha de finalización: 28/07/2026

---

## Flujo de traducción (corregido)

```
optent_tokens=True:
  Reseña ES → deep_translator (Google Translate) → EN → deepseek-r1:1.5b (Ollama) → extracción estructurada

optent_tokens=False:
  Reseña ES → deepseek-r1:1.5b (Ollama) → extracción estructurada (sin traducir)
```

- `deep_translator` usa Google Translate como backend (sin API key). Solo se activa cuando `optent_tokens=True`.
- `deepseek-r1:1.5b` se ejecuta localmente vía Ollama (`http://127.0.0.1:11434`) y se usa **exclusivamente** para extracción de datos, nunca para traducción.
- La traducción ES→EN reduce la longitud del texto de entrada al LLM (inglés suele ser más conciso), lo que ahorra tokens y reduce costos.

---

## Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/analyze` | Analizar una reseña individual (texto JSON + `optent_tokens`) |
| `POST` | `/api/analyze/upload` | Subir un archivo `.xlsx` y procesar todas las reseñas |
| `POST` | `/api/analyze/folder` | Indicar ruta de carpeta y procesar todos los `.xlsx` dentro |
| `GET` | `/api/analyze/export` | Exportar resultados en JSON o Excel |
| `GET` | `/api/analyze/cost-estimate` | Estimación de costo para N reseñas/día (comparando directo vs optimizado) |
| `GET` | `/` | Estado del servicio |

---

## Archivos modificados

### `backend/app/services/analysis_service.py`
- Reemplazada traducción simulada con `deep_translator.GoogleTranslator` real
- Reemplazada extracción simulada con llamada a `ollama.generate(model="deepseek-r1:1.5b")` con prompt estructurado y formato JSON
- Añadida función `_traducir_es_a_en()` con GoogleTranslator
- Añadida función `_extraer_datos_error()` con Ollama + prompt de extracción estructurada
- Añadido parámetro `optent_tokens` a `analizar_resena()` con lógica de ramificación
- Añadida función `_detectar_columna_reseña()` para auto-detectar la columna de texto en Excel
- Añadida función `procesar_archivo_excel()` para procesar archivos .xlsx desde bytes
- Añadida función `procesar_carpeta_excel()` para procesar todos los .xlsx en una carpeta

### `backend/app/models/schemas.py`
- Añadido campo `optent_tokens: bool = False` a `ReviewRequest`
- Añadido `BatchAnalysisResponse` con `total: int` y `results: list[AnalysisResponse]`

### `backend/app/routers/analyze.py`
- Añadido `optent_tokens: bool = Form(False)` al endpoint `/api/analyze`
- Añadido endpoint `POST /api/analyze/upload` con `UploadFile`
- Añadido endpoint `POST /api/analyze/folder` con `folder_path: str`
- Añadido endpoint `GET /api/analyze/export`
- Añadido endpoint `GET /api/analyze/cost-estimate`

### `backend/app/main.py`
- Añadido `StaticFiles` mount en `/` para servir `frontend/index.html`
- Eliminado comentario obsoleto "Como ahora no hay frontend"
- Ruta `_frontend_dir` construida con Path relativo al proyecto

### `backend/requirements.txt`
Añadidos:
- `deep-translator==1.11.4`
- `ollama==0.6.2`
- `python-multipart==0.0.18`

### `backend/README.md`
- Añadidas secciones 5a–5d con ejemplos curl para los nuevos endpoints
- Actualizada sección 2 (flujo de datos) para reflejar nuevos endpoints

### `backend/app/core/config.py`
- Sin cambios (ya tenía `PRICE_PER_MILLION_TOKENS_USD = 2.50`)

### `backend/app/core/__init__.py`, `backend/app/__init__.py`, `backend/app/models/__init__.py`, `backend/app/routers/__init__.py`, `backend/app/services/__init__.py`
- Sin cambios (archivos vacíos)

---

## Archivos creados

| Archivo | Descripción |
|---|---|
| `frontend/index.html` | Interfaz web HTML para analizar reseñas desde Excel |
| `documentacion/Plan_Implementacion_HU-012.md` | Plan detallado de implementación por fases |
| `documentacion/Resumen_HU-012.md` | Este archivo — resumen de cambios |
| `README.md` (raíz) | Configuración de instrucciones para agentes |
| `AGENTS.md` | Instrucciones del proyecto para futuras sesiones |
| `TODO.md` | Lista de tareas con seguimiento de progreso |

---

## Dependencias nuevas

| Paquete | Versión | Propósito |
|---|---|---|
| `deep-translator` | 1.11.4 | Traducción ES→EN (Google Translate backend) |
| `ollama` | 0.6.2 | Integración con Ollama para llamadas a deepseek-r1:1.5b |
| `python-multipart` | 0.0.18 | Soporte para upload de archivos en FastAPI |

---

## Frontend (`frontend/index.html`)

Página única con:
- Selector de modo (archivo .xlsx / carpeta)
- Drag-and-drop para archivos .xlsx
- Input de ruta de carpeta
- Toggle `optent_tokens`
- Botón de ejecutar análisis
- Tabla de resultados con `error_type`, `component`, `severity`, tokens ES/EN, costo USD
- Panel de métricas agregadas (total reseñas, tokens ES, tokens EN, ahorro económico)
- Botones de export JSON/Excel
- Indicador de estado (cargando / éxito / error)

---

## Notas técnicas

- **Ollama**: debe estar corriendo en `http://127.0.0.1:11434` con el modelo `deepseek-r1:1.5b` descargado
- **deep_translator**: usa Google Translate sin API key; para volúmenes altos (10K/día) considerar rate limiting o API key de DeepL
- **Tokenización**: `tiktoken` con `o200k_base` para medir tokens del modelo target
- **Precio de referencia**: `$2.50 USD por millón de tokens` (costo simbólico, Ollama es gratuito)
- **Detección de columna**: heuristica que busca nombres como `reseña`, `review`, `text`, `comment`, `texto`
- ** Seguridad**: la ruta de carpeta en `/api/analyze/folder` no está restringida a sandbox (pendiente de validación para producción)