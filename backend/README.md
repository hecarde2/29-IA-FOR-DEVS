# App Store Review Analyzer — Backend

API en FastAPI que analiza reseñas de usuarios: cuenta tokens (ES vs EN)
con `tiktoken` y extrae datos estructurados del error reportado.

## 1. Estructura de carpetas

```
backend/
├── app/                        # Backend (API)
│   ├── main.py                 # Punto de entrada: crea la app y conecta los routers
│   ├── core/
│   │   └── config.py           # Constantes / configuración
│   ├── models/
│   │   └── schemas.py          # Modelos Pydantic (request/response)
│   ├── routers/
│   │   └── analyze.py          # Endpoint POST /api/analyze
│   └── services/
│       └── analysis_service.py # Lógica de negocio (tokens, traducción, extracción)
├── scripts/                    # Herramientas externas al backend
│   ├── generar_excel.py        # Genera datos de prueba (Excel)
│   └── procesar_excel_async.py # Cliente que consume el backend en paralelo
├── data/
│   └── resenas_productos_50k.xlsx
├── requirements.txt
└── README.md
```

## 2. Cómo se conecta todo (flujo de datos)

```
scripts/generar_excel.py
        │  genera
        ▼
data/resenas_productos_50k.xlsx
        │  lee
        ▼
scripts/procesar_excel_async.py  ──HTTP POST──►  app/main.py (FastAPI)
                                                        │ include_router
                                                        ▼
                                                 app/routers/analyze.py
                                                        │ llama a
                                                        ▼
                                             app/services/analysis_service.py
                                                        │ usa
                                                        ▼
                                             app/models/schemas.py (valida datos)
```

- **`app/main.py`** es el único punto donde se "arma" la aplicación: crea el
  objeto `FastAPI()` y usa `app.include_router(analyze.router)` para conectar
  los endpoints definidos en `app/routers/analyze.py`.
- **`app/routers/analyze.py`** no contiene lógica de negocio: solo valida la
  petición y llama a `analizar_resena()` en el servicio.
- **`app/services/analysis_service.py`** contiene la lógica real (conteo de
  tokens con `tiktoken`, traducción simulada, extracción de datos). Está
  aislado del router para poder probarlo o reemplazarlo (por ejemplo,
  conectar un traductor real) sin tocar la API.
- **`scripts/procesar_excel_async.py`** es un cliente externo: no importa
  nada del backend, se conecta por HTTP (como lo haría cualquier app,
  Postman, o un futuro frontend) a `http://127.0.0.1:8000/api/analyze`.

## 3. Instalación

```bash
cd backend
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Levantar el backend

```bash
cd backend
uvicorn app.main:app --reload
```

- API disponible en: `http://127.0.0.1:8000`
- Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`
- Documentación alternativa (ReDoc): `http://127.0.0.1:8000/redoc`

## 5. Probar el endpoint manualmente

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "La aplicación se cierra al subir una foto de perfil", "optent_tokens": true}'
```

## 5a. Subir un archivo .xlsx

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/upload \
  -F "file=@resenas_productos_50k.xlsx" \
  -F "optent_tokens=false"
```

## 5b. Escaneo de carpeta (Modo B)

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/folder \
  -F "folder_path=/ruta/a/carpeta" \
  -F "optent_tokens=true"
```

## 5c. Estimación de costo

```bash
curl "http://127.0.0.1:8000/api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true"
```

## 5d. Exportar resultados

```bash
curl "http://127.0.0.1:8000/api/analyze/export?format=json"
```

## 6. Probar con datos masivos (opcional)

Con el backend corriendo en otra terminal:

```bash
# 1) Generar datos de prueba (si no existen ya en data/)
python scripts/generar_excel.py

# 2) Enviar todas las reseñas al backend en paralelo
python scripts/procesar_excel_async.py
```

Este segundo script imprime en consola métricas agregadas: tokens en
español vs inglés, tokens ahorrados y el ahorro económico estimado.

## 7. Notas

- No incluye frontend: se prueba vía Swagger UI (`/docs`), `curl`, Postman,
  o el script `scripts/procesar_excel_async.py`.
- `CORS` está abierto (`allow_origins=["*"]`) para que cualquier cliente,
  incluyendo un futuro frontend en otro puerto/dominio, pueda consumir la API.
- La traducción y la extracción de errores están **simuladas** (ver
  `analysis_service.py`); quedan aisladas en funciones propias para
  facilitar su reemplazo por un servicio real (traductor o LLM).
