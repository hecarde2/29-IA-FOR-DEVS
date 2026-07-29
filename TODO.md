# TODO — HU-012

> **Estado: COMPLETADO** — Todas las fases implementadas (28/07/2026)

---

## Fase 1: Integración LLM real (Ollama + deep_translator)
- [x] Reemplazar `_traducir_es_a_en()` con llamada real a `deep_translator.GoogleTranslator`
- [x] Reemplazar `_extraer_datos_error()` con llamada a `deepseek-r1:1.5b` vía Ollama (`ollama.generate()`)
- [x] Añadir `optent_tokens` parameter a `analizar_resena()`
- [x] Si `optent_tokens=True`: ES → deep_translator → EN → Ollama extracción
- [x] Si `optent_tokens=False`: ES → Ollama extracción directa
- [x] Añadir `deep-translator==1.11.4` a `requirements.txt`
- [x] Añadir `ollama==0.6.2` a `requirements.txt`

## Fase 2: Endpoint de upload de archivo (Modo A)
- [x] Nuevo endpoint `POST /api/analyze/upload` con `UploadFile`
- [x] Leer `.xlsx` con `pandas` + `openpyxl`
- [x] Detección automática de columna de reseñas
- [x] Procesar cada fila y retornar lista de `AnalysisResponse`
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
- [x] Retornar JSON con schema limpio (`error_type`, `component`, `severity`, `summary_en`, `summary_es`, `tokens`, `cost_usd`)

## Fase 6: Análisis de impacto económico
- [x] Nuevo endpoint `GET /api/analyze/cost-estimate?reviews_per_day=10000&optent_tokens=true|false`
- [x] Calcular tokens ES y EN estimados
- [x] Calcular costo directo vs optimizado
- [x] Retornar ahorro diario/mensual/anual a `$2.50/M tokens`

## Fase 7: Frontend HTML
- [x] Crear `frontend/index.html`
- [x] Selector de modo (Modo A / Modo B)
- [x] Input de archivo `.xlsx` (Modo A) con drag-and-drop
- [x] Input de ruta de carpeta (Modo B)
- [x] Toggle `optent_tokens`
- [x] Botón "Ejecutar análisis"
- [x] Tabla de resultados con columnas: reseña, error_type, component, severity, tokens_es, tokens_en, costo_usd
- [x] Panel de métricas agregadas
- [x] Botón de export JSON/Excel
- [x] Indicador de carga/estado

## Fase 8: Actualizar requirements.txt
- [x] Añadir `deep-translator==1.11.4`
- [x] Añadir `ollama==0.6.2`
- [x] Añadir `python-multipart==0.0.18`
- [x] Verificar compatibilidad con Python 3.14+

## Fase 9: Documentación
- [x] Crear `documentacion/Plan_Implementacion_HU-012.md`
- [x] Crear `README.md` actualizado (backend/README.md con nuevos endpoints)
- [x] Crear `AGENTS.md` con configuración del proyecto
- [x] Crear `TODO.md` con seguimiento de fases