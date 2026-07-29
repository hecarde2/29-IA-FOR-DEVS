# Guía de Instalación

## Prerrequisitos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |
| Ollama | 0.115.6+ |
| Windows | 10+ |

## Paso 1: Instalar Ollama

1. Descarga Ollama desde [https://ollama.com](https://ollama.com).
2. Instálalo y asegúrate de que el servicio esté corriendo.
3. Descarga el modelo `deepseek-r1:1.5b`:

```powershell
ollama pull deepseek-r1:1.5b
```

4. Verifica que el modelo esté disponible:

```powershell
ollama list
```

Deberías ver `deepseek-r1:1.5b` en la lista.

## Paso 2: Clonar el proyecto

```powershell
cd C:\Users\Usuario\Documents\riwi\IA for Devs\29-IA-FOR-DEVS
```

## Paso 3: Instalar dependencias

Desde la carpeta `backend/`:

```powershell
pip install -r requirements.txt
```

Esto instala:
- `fastapi` — framework web
- `uvicorn` — servidor ASGI
- `tiktoken` — contador de tokens
- `pandas` + `openpyxl` — lectura de Excel
- `deep-translator` — traducción ES→EN
- `ollama` — integración con Ollama
- `python-multipart` — soporte para upload de archivos
- `pyfiglet` — generación de ASCII art
- `faker`, `httpx`, `tqdm` — herramientas de prueba

## Paso 4: Levantar el backend

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

La API estará disponible en:

- **API**: `http://127.0.0.1:8000`
- **Documentación interactiva (Swagger)**: `http://127.0.0.1:8000/docs`
- **Documentación alternativa (ReDoc)**: `http://127.0.0.1:8000/redoc`

## Paso 5: Probar el backend

```powershell
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

## Pasos opcionales

### Generar datos de prueba

```powershell
python scripts/generar_excel.py
```

Genera `backend/data/resenas_productos_50k.xlsx` con 50,000 reseñas ficticias.

### Enviar datos masivos al backend

Con el backend corriendo en otra terminal:

```powershell
python scripts/procesar_excel_async.py
```

Esto envía todas las reseñas del Excel al endpoint `/api/analyze` en paralelo e imprime métricas agregadas.

### Abrir el frontend

Si levantaste el backend con `python -m uvicorn app.main:app --reload`, el frontend HTML se sirve automáticamente en `http://127.0.0.1:8000`.