# Arquitectura

## Visión general

El backend se construye sobre **FastAPI** y se estructura en capas separadas:

```
┌─────────────┐
│   Frontend   │  ← HTML estático servido por FastAPI
│  (index.html) │
└──────┬───────┘
       │ HTTP
       ▼
┌─────────────────┐
│  FastAPI (main)  │  ← Punto de entrada, CORS, rutas estáticas
└────┬────────────┘
     │ include_router
     ▼
┌─────────────────┐
│  Routers         │  ← APIRouter con endpoints
│  (analyze.py)    │
└────┬────────────┘
     │ delega a
     ▼
┌─────────────────────┐
│  Servicios           │  ← Lógica de negocio
│  (analysis_service.py)│
└────┬────────────────┘
     │ usa
     ├─────▶ deep_translator (ES→EN)
     ├─────▶ Ollama / deepseek-r1:1.5b (extracción)
     └─────▶ tiktoken (conteo de tokens)
```

## Estructura de carpetas

```
backend/
├── app/
│   ├── main.py                    ← Punto de entrada, crea la app FastAPI
│   ├── core/
│   │   ├── __init__.py            ← (vacío)
│   │   └── config.py              ← Constantes, banner GEOXOR, config global
│   ├── models/
│   │   ├── __init__.py            ← (vacío)
│   │   └── schemas.py             ← Modelos Pydantic (request/response)
│   ├── routers/
│   │   ├── __init__.py            ← (vacío)
│   │   └── analyze.py             ← Endpoints de análisis
│   └── services/
│       ├── __init__.py            ← (vacío)
│       └── analysis_service.py    ← Lógica de negocio
├── data/
│   └── resenas_productos_50k.xlsx ← Dataset de ejemplo
├── docs/                          ← Documentación en español
├── scripts/
│   ├── generar_excel.py           ← Genera datos de prueba
│   └── procesar_excel_async.py    ← Cliente batch para el API
├── requirements.txt               ← Dependencias
└── README.md                      ← Documentación del backend
```

## Modelos Pydantic

### `ReviewRequest`

```json
{
  "text": "string (reseña en español)",
  "optent_tokens": false
}
```

- `text`: el texto de la reseña a analizar.
- `optent_tokens`: si es `true`, el texto se traduce antes de enviarlo al LLM; si es `false`, se envía directamente en español.

### `AnalysisResponse`

```json
{
  "metrics": {
    "original_tokens": 28,
    "translated_tokens": 31,
    "tokens_saved_per_request": -3
  },
  "extracted_data": {
    "error_type": "crash | bug | performance | ui | login | payment | other",
    "component": "string (componente afectado)",
    "severity": "low | medium | high | critical",
    "summary_en": "string (resumen en inglés)",
    "summary_es": "string (resumen en español)"
  }
}
```

### `BatchAnalysisResponse`

```json
{
  "total": 50000,
  "results": [AnalysisResponse, ...]
}
```

## Flujo de análisis

### Con `optent_tokens = true`

```
1. Cliente envía reseña en español
2. deep_translator traduce ES → EN  (Google Translate backend)
3. tiktoken cuenta tokens del texto EN
4. deepseek-r1:1.5b (vía Ollama) extrae datos estructurados del texto EN
5. Se devuelve AnalysisResponse con métricas y datos extraídos
```

### Con `optent_tokens = false`

```
1. Cliente envía reseña en español
2. tiktoken cuenta tokens del texto ES
3. deepseek-r1:1.5b (vía Ollama) extrae datos estructurados del texto ES
4. Se devuelve AnalysisResponse con métricas y datos extraídos
```

## Detección de columna de reseñas

La función `_detectar_columna_reseña()` busca automáticamente la columna que contiene el texto de la reseña. Busca en este orden de prioridad:

1. `reseña`, `review`, `text`, `comment`, `texto`, `review_text`, `resena`
2. Cualquier columna que contenga `review`, `rese`, `text` o `comment` en su nombre
3. La primera columna del archivo (fallback)

## Pricing de referencia

El costo se calcula con la fórmula:

```
costo = (tokens / 1_000_000) * 2.50 USD
```

Ollama ejecuta localmente, por lo que no hay costo real de API. El cálculo es una estimación comparativa que refleja lo que costaría si se usara un proveedor de LLM en la nube.

## Seguridad

El endpoint `/api/analyze/folder` acepta una ruta de carpeta directamente. En producción, se debería restringir a un directorio permitido (lista blanca) para evitar acceso a archivos fuera del sandbox.