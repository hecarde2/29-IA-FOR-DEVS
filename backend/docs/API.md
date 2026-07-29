# Referencia de la API

Todos los endpoints están bajo el prefijo `/api`.

---

## `POST /api/analyze`

Analiza una reseña individual.

### Cuerpo de la petición

```json
{
  "text": "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil.",
  "optent_tokens": true
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `text` | `string` | Sí | Texto de la reseña en español |
| `optent_tokens` | `boolean` | No (default: `false`) | Si `true`, traduce ES→EN antes de enviar al LLM |

### Respuesta exitosa (200)

```json
{
  "metrics": {
    "original_tokens": 28,
    "translated_tokens": 31,
    "tokens_saved_per_request": -3
  },
  "extracted_data": {
    "error_type": "crash",
    "component": "profile_picture_upload",
    "severity": "high",
    "summary_en": "App crashes when uploading profile picture from gallery.",
    "summary_es": "La app se cierra al subir foto de perfil desde la galería."
  }
}
```

### Errores

| Código | Descripción |
|---|---|
| `400` | El texto está vacío |

---

## `POST /api/analyze/upload`

Sube un archivo `.xlsx` y analiza todas las reseñas que contiene.

### Formato de la petición

Multipart form-data:

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo `.xlsx` | Sí | Archivo Excel con reseñas |
| `optent_tokens` | boolean | No (default: `false`) | Activar traducción previa |

### Ejemplo con curl

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/upload \
  -F "file=@resenas_productos_50k.xlsx" \
  -F "optent_tokens=false"
```

### Respuesta exitosa (200)

```json
{
  "total": 50000,
  "results": [
    {
      "metrics": { "original_tokens": 28, "translated_tokens": 31, "tokens_saved_per_request": -3 },
      "extracted_data": {
        "error_type": "crash",
        "component": "profile_picture_upload",
        "severity": "high",
        "summary_en": "App crashes when uploading profile picture.",
        "summary_es": "La app se cierra al subir foto de perfil."
      }
    }
  ]
}
```

### Errores

| Código | Descripción |
|---|---|
| `400` | No se proporcionó archivo o el archivo no es `.xlsx` |

---

## `POST /api/analyze/folder`

Escanea una carpeta y procesa todos los archivos `.xlsx` dentro.

### Formato de la petición

Multipart form-data:

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `folder_path` | `string` | Sí | Ruta absoluta o relativa a la carpeta |
| `optent_tokens` | boolean | No (default: `false`) | Activar traducción previa |

### Ejemplo con curl

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/folder \
  -F "folder_path=C:/Users/usuario/reviews" \
  -F "optent_tokens=true"
```

### Errores

| Código | Descripción |
|---|---|
| `400` | La carpeta no existe |

---

## `GET /api/analyze/export`

Exporta resultados en formato JSON o Excel.

### Parámetros de consulta

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `format` | `string` | Sí | `json` o `excel` |
| `optent_tokens` | boolean | No | Filtro por modo de procesamiento |

### Ejemplo

```bash
curl "http://127.0.0.1:8000/api/analyze/export?format=json"
```

---

## `GET /api/analyze/cost-estimate`

Estima el impacto económico para un volumen dado de reseñas por día.

### Parámetros de consulta

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reviews_per_day` | `integer` | No (default: `10000`) | Reseñas procesadas por día |
| `optent_tokens` | boolean | No (default: `false`) | Comparar modo optimizado vs directo |

### Ejemplo

```bash
curl "http://127.0.0.1:8000/api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true"
```

### Respuesta exitosa (200)

```json
{
  "reviews_per_day": 10000,
  "estimated_tokens_es": 440000,
  "estimated_tokens_en": 560000,
  "costo_directo_usd": 1.1000,
  "costo_optimizado_usd": 1.4000,
  "ahorro_diario_usd": -0.3000,
  "ahorro_mensual_usd": -9.0000,
  "ahorro_anual_usd": -109.5000,
  "precio_por_millon_usd": 2.50,
  "optent_tokens": true
}
```

El precio de referencia es **$2.50 USD por millón de tokens**. En Ollama (local), el costo real es $0, pero la estimación compara la diferencia de tokens entre español e inglés como si se usara una API de pago.

---

## `GET /`

Endpoint de estado del servicio.

### Respuesta

```json
{
  "status": "ok",
  "servicio": "App Store Review Analyzer",
  "docs": "/docs"
}
```