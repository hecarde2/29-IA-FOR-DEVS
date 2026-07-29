# Ejemplos de uso

## 1. Analizar una reseña individual

### Con `curl`

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil desde la galería de mi teléfono.", "optent_tokens": true}'
```

### Con Python

```python
import httpx

response = httpx.post(
    "http://127.0.0.1:8000/api/analyze",
    json={
        "text": "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil.",
        "optent_tokens": True
    }
)
result = response.json()
print(result["extracted_data"]["error_type"])  # crash
print(result["extracted_data"]["component"])   # profile_picture_upload
print(result["metrics"]["original_tokens"])     # tokens en español
print(result["metrics"]["translated_tokens"])   # tokens en inglés
```

## 2. Subir un archivo Excel

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/upload \
  -F "file=@resenas_productos_50k.xlsx" \
  -F "optent_tokens=false"
```

## 3. Procesar una carpeta de archivos Excel

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/folder \
  -F "folder_path=C:/Users/usuario/reviews" \
  -F "optent_tokens=true"
```

## 4. Estimar costo para 10,000 reseñas/día

### Con traducción (optimizado)

```bash
curl "http://127.0.0.1:8000/api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true"
```

### Sin traducción (directo)

```bash
curl "http://127.0.0.1:8000/api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=false"
```

## 5. Exportar resultados en JSON

```bash
curl "http://127.0.0.1:8000/api/analyze/export?format=json" > resultados.json
```

## 6. Exportar resultados en Excel

```bash
curl "http://127.0.0.1:8000/api/analyze/export?format=excel" > resultados.xlsx
```

## 7. Verificar que el backend está activo

```bash
curl http://127.0.0.1:8000/
```

Respuesta esperada:

```json
{
  "status": "ok",
  "servicio": "App Store Review Analyzer",
  "docs": "/docs"
}
```

## 8. Abrir la documentación interactiva (Swagger)

Visita `http://127.0.0.1:8000/docs` en tu navegador. Swagger UI permite probar todos los endpoints directamente desde la interfaz web.

## 9. Usar el frontend HTML

Si el backend está corriendo, abre `http://127.0.0.1:8000` en tu navegador. El frontend permite:

1. Seleccionar el modo (archivo o carpeta)
2. Elegir si aplicar optimización de tokens
3. Ejecutar el análisis
4. Ver los resultados en una tabla
5. Exportar en JSON o Excel

## 10. Ejemplo de respuesta completa

```json
{
  "total": 3,
  "results": [
    {
      "metrics": {
        "original_tokens": 30,
        "translated_tokens": 33,
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
  ]
}
```