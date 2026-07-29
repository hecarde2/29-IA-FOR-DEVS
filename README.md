# Documentación — App Store Review Analyzer

API en FastAPI que analiza reseñas de usuarios de App Store desde archivos Excel.

Más información en [backend/docs/](backend/docs/) (instalación, API, arquitectura y ejemplos).

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/analyze` | Analizar una reseña individual |
| `POST` | `/api/analyze/upload` | Subir un archivo `.xlsx` y analizar todas las reseñas |
| `POST` | `/api/analyze/folder` | Escaneo de carpeta con múltiples `.xlsx` |
| `GET` | `/api/analyze/export` | Exportar resultados en JSON o Excel |
| `GET` | `/api/analyze/cost-estimate` | Estimación de impacto económico |

## Flujo de traducción

```
optent_tokens=True:  ES → deep_translator → EN → deepseek-r1:1.5b (Ollama) → extracción
optent_tokens=False: ES → deepseek-r1:1.5b (Ollama) → extracción directa
```

## Requisitos previos

- Python 3.12+
- Ollama corriendo con modelo `deepseek-r1:1.5b` descargado
- `pip install -r requirements.txt` desde la carpeta `backend/`
