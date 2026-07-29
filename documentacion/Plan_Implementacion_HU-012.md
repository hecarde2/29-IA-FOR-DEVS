# Plan Implementación — HU-012

**Ingesta flexible de datos y optimización opcional de tokens para análisis de reseñas en Excel**

---

## Flujo de traducción (corregido)

```
optent_tokens=True:
  Reseña ES → deep_translator → EN → deepseek-r1:1.5b (Ollama) → extracción

optent_tokens=False:
  Reseña ES → deepseek-r1:1.5b (Ollama) → extracción (sin traducir)
```

- `deep_translator` maneja ES→EN (Google Translate backend).
- `deepseek-r1:1.5b` vía Ollama se usa SOLO para extracción estructurada, nunca para traducción.

---

## Requisitos previos

- Ollama corriendo con modelo `deepseek-r1:1.5b` descargado
- Python 3.12+
- `pip install -r backend/requirements.txt`

---

## Fase 1 — Integración LLM real (Ollama + deep_translator)

**Objetivo:** Reemplazar los placeholders simulados con integraciones reales.

### Cambios en backend

- **`app/services/analysis_service.py`**:
  - `_traducir_es_a_en()`: reemplazar string hardcodeado con llamada real a `deep_translator.GoogleTranslator(source='es', target='en')`
  - `_extraer_datos_error()`: reemplazar dict hardcodeado con llamada a Ollama (`deepseek-r1:1.5b`) vía `ollama.generate()` con prompt estructurado para extracción de errores
  - `analizar_resena()`: aceptar parámetro `optent_tokens`; si `True` traduce antes de extraer, si `False` envía ES directo al LLM

- **`backend/requirements.txt`**:
  - Añadir `deep-translator==1.11.4`
  - Añadir `ollama==0.6.2`

### Endpoint actualizado

- `POST /api/analyze` — añadir campo `optent_tokens: bool` al body del request

### Schema actualizado (`app/models/schemas.py`)

- Añadir `optent_tokens: bool = False` a `ReviewRequest`

---

## Fase 2 — Endpoint de upload de archivo (Modo A)

**Objetivo:** Permitir cargar un `.xlsx` individual.

### Cambios en backend

- Nuevo endpoint: `POST /api/analyze/upload`
  - Recibe `UploadFile` (multipart/form-data)
  - Lee el `.xlsx` con `pandas` + `openpyxl`
  - Detecta automáticamente la columna de reseñas (heurística: busca columnas con nombre `review`, `reseña`, `text`, `comment`, `texto`)
  - Procesa cada fila y retorna lista de `AnalysisResponse`

- **`backend/requirements.txt`**:
  - Añadir `python-multipart==0.0.18`

### Schema nuevo

- `BatchAnalysisRequest`: `{ "file": UploadFile, "optent_tokens": bool }`
- `BatchAnalysisResponse`: `{ "total": int, "results": list[AnalysisResponse] }`

---

## Fase 3 — Endpoint de escaneo de carpeta (Modo B)

**Objetivo:** Indicar una ruta de carpeta y procesar todos los `.xlsx` dentro.

### Cambios en backend

- Nuevo endpoint: `POST /api/analyze/folder`
  - Recibe `{ "folder_path": str, "optent_tokens": bool }`
  - Usa `pathlib.Path` para listar todos los `.xlsx` en la carpeta
  - Procesa cada archivo consolidando resultados
  - Retorna `BatchAnalysisResponse`

### Notas de seguridad

- Validar que `folder_path` esté dentro de un directorio permitido (lista blanca) para evitar acceso fuera de sandbox

---

## Fase 4 — Parámetro `optent_tokens`

**Objetivo:** Controlar si se aplica traducción previa o no.

### Lógica

| `optent_tokens` | Flujo |
|---|---|
| `True` | ES → `deep_translator` → EN → Ollama (extracción) |
| `False` | ES → Ollama (extracción directa) |

### Impacto

- Con `optent_tokens=True`: más tokens de entrada (texto EN suele ser más largo que ES), pero el LLM procesa un idioma más "estandarizado"
- Con `optent_tokens=False`: menos tokens, pero potencialmente menos preciso en extracción si el LLM maneja mejor inglés
- Ambos caminos se comparan en la métrica de costo económico (Fase 6)

---

## Fase 5 — Export JSON/Excel

**Objetivo:** Exportar resultados procesados en formato limpio.

### Nuevo endpoint

- `GET /api/analyze/export?format=json|excel&batch_id=<id>`
  - `format=json`: devuelve JSON con schema `{"error_type": str, "component": str, "severity": str, "summary_en": str, "summary_es": str}`
  - `format=excel`: devuelve archivo `.xlsx` con columnas: `error_type`, `component`, `severity`, `summary_en`, `summary_es`, `tokens`, `cost_usd`
  - Retorna archivo descargable (`Content-Disposition: attachment`)

---

## Fase 6 — Análisis de impacto económico

**Objetivo:** Calcular volumen de tokens y diferencia de costo para 10,000 reseñas/día.

### Lógica

```
costo_directo = (tokens_es_total / 1_000_000) * 2.50
costo_optimizado = (tokens_en_total / 1_000_000) * 2.50
ahorro_diario = costo_directo - costo_optimizado
ahorro_mensual = ahorro_diario * 30
ahorro_anual = ahorro_mensual * 12
```

### Nuevo endpoint o campo en respuesta

- `GET /api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true|false`
  - Retorna: `{ "reviews_per_day": 10000, "estimated_tokens_es": int, "estimated_tokens_en": int, "costo_directo_usd": float, "costo_optimizado_usd": float, "ahorro_diario_usd": float, "ahorro_mensual_usd": float, "ahorro_anual_usd": float }`

---

## Fase 7 — Frontend HTML

**Objetivo:** Interfaz web para interactuar con el backend sin necesidad de Postman/cURL.

### Archivo

- `frontend/index.html` — página única servida por FastAPI como `StaticFiles`

### Elementos de UI

1. **Selector de modo** (radio buttons):
   - Modo A: Subir archivo `.xlsx`
   - Modo B: Ruta de carpeta

2. **Input de archivo** (`<input type="file" accept=".xlsx">`) — visible solo en Modo A

3. **Input de carpeta** (`<input type="text" placeholder="/ruta/carpeta">`) — visible solo en Modo B

4. **Toggle `optent_tokens`** (checkbox): "Optimizar tokens (traducir ES→EN antes del análisis)"

5. **Botón "Ejecutar análisis"**

6. **Tabla de resultados**:
   - Columnas: `reseña`, `error_type`, `component`, `severity`, `tokens_es`, `tokens_en`, `costo_usd`

7. **Panel de métricas agregadas**:
   - Total reseñas procesadas
   - Tokens ES totales / EN totales
   - Ahorro económico

8. **Botón de export** (JSON / Excel)

9. **Indicador de estado** (cargando / completo / error)

---

## Fase 8 — Actualización de `requirements.txt`

### Adiciones

```
deep-translator==1.11.4
ollama==0.6.2
python-multipart==0.0.18
```

### Confirmar existentes

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
tiktoken==0.8.0
pandas==2.2.3
openpyxl==3.1.5
faker==33.1.0
httpx==0.28.1
tqdm==4.67.1
```

---

## Fase 9 — Documentación

### Archivos a crear/actualizar en `documentacion/`

| Archivo | Contenido |
|---|---|
| `Guia_Instalacion.md` | Prerrequisitos (Ollama + deepseek-r1:1.5b), setup de venv, comandos de run |
| `API_Reference.md` | Todos los endpoints, schemas de request/response, ejemplos curl |
| `Arquitectura.md` | Diagrama de flujo de datos, componentes, decisión de diseño (`optent_tokens`) |
| `Plan_Implementacion_HU-012.md` | Este archivo |

### Actualizar PDF existente

- Regenerar `Documentacion_Backend_IA-PROYECT.pdf` con la información actualizada (herramienta: `python -m fpdf` o similar, o actualización manual)

---

## Orden de ejecución recomendado

| Fase | Descripción | Estado |
|---|---|---|
| 1 | Integración LLM real (Ollama + deep_translator) | ✅ Completado |
| 2 | Endpoint de upload de archivo (Modo A) | ✅ Completado |
| 3 | Endpoint de escaneo de carpeta (Modo B) | ✅ Completado |
| 4 | Parámetro `optent_tokens` | ✅ Completado |
| 5 | Export JSON/Excel | ✅ Completado |
| 6 | Análisis de impacto económico | ✅ Completado |
| 7 | Frontend HTML | ✅ Completado |
| 8 | Actualizar requirements.txt | ✅ Completado |
| 9 | Documentación | 🔄 En curso |

---

## Notas técnicas

- **Ollama API**: se usa `olama.generate()` del paquete `ollama` de Python (no la API HTTP directa, que es más limpia)
- **deep_translator**: usa Google Translate como backend, sin API key, con rate-limiting implícito. Para volúmenes altos (10K/día) considerar batching o una API key de DeepL
- **Ollama modelo**: `deepseek-r1:1.5b` está descargado y disponible localmente
- **Tokenización**: `tiktoken` con `o200k_base` se mantiene para medir tokens reales del modelo target