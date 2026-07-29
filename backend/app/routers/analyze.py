"""
Router (controlador) del recurso "analyze".
Un router es un grupo de endpoints relacionados que luego se
"conecta" (include_router) a la app principal en app/main.py.

Aquí NO va lógica de negocio: solo se valida la petición
y se delega el trabajo real al servicio (app/services/analysis_service.py).
"""

from fastapi import APIRouter, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse

from app.core.config import PRICE_PER_MILLION_TOKENS_USD
from app.models.schemas import AnalysisResponse, BatchAnalysisResponse, ReviewRequest
from app.services.analysis_service import (
    analizar_resena,
    procesar_archivo_excel,
    procesar_carpeta_excel,
)
from pathlib import Path

router = APIRouter(prefix="/api", tags=["Análisis de reseñas"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_review(payload: ReviewRequest) -> AnalysisResponse:
    texto_es = payload.text.strip()
    if not texto_es:
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    return analizar_resena(texto_es, optent_tokens=payload.optent_tokens)


@router.post("/analyze/upload", response_model=BatchAnalysisResponse)
async def analyze_upload(
    file: UploadFile,
    optent_tokens: bool = Form(False),
) -> BatchAnalysisResponse:
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx.")

    contents = await file.read()
    results = procesar_archivo_excel(contents, optent_tokens=optent_tokens)
    return BatchAnalysisResponse(total=len(results), results=results)


@router.post("/analyze/folder", response_model=BatchAnalysisResponse)
async def analyze_folder(
    folder_path: str = Form(...),
    optent_tokens: bool = Form(False),
) -> BatchAnalysisResponse:
    path = Path(folder_path)
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"La carpeta no existe: {folder_path}")

    results = procesar_carpeta_excel(path, optent_tokens=optent_tokens)
    return BatchAnalysisResponse(total=len(results), results=results)


@router.get("/analyze/export")
async def export_results(
    format: str = "json",
    optent_tokens: bool = False,
) -> dict:
    return {
        "format": format,
        "note": "Export endpoint requires prior batch processing via /api/analyze/upload or /api/analyze/folder",
        "supported_formats": ["json", "excel"],
    }


def _estimar_tokens_por_reseña(optent_tokens: bool) -> dict:
    texto_ejemplo = "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil."
    count_es = 44
    if optent_tokens:
        count_en = 56
    else:
        count_en = count_es
    return {"es": count_es, "en": count_en}


@router.get("/analyze/cost-estimate")
async def cost_estimate(reviews_per_day: int = 10000, optent_tokens: bool = False) -> dict:
    tokens = _estimar_tokens_por_reseña(optent_tokens)
    costo_directo = (tokens["es"] * reviews_per_day / 1_000_000) * PRICE_PER_MILLION_TOKENS_USD
    costo_optimizado = (tokens["en"] * reviews_per_day / 1_000_000) * PRICE_PER_MILLION_TOKENS_USD
    ahorro_diario = costo_directo - costo_optimizado
    return {
        "reviews_per_day": reviews_per_day,
        "estimated_tokens_es": tokens["es"] * reviews_per_day,
        "estimated_tokens_en": tokens["en"] * reviews_per_day,
        "costo_directo_usd": round(costo_directo, 4),
        "costo_optimizado_usd": round(costo_optimizado, 4),
        "ahorro_diario_usd": round(ahorro_diario, 4),
        "ahorro_mensual_usd": round(ahorro_diario * 30, 4),
        "ahorro_anual_usd": round(ahorro_diario * 365, 4),
        "precio_por_millon_usd": PRICE_PER_MILLION_TOKENS_USD,
        "optent_tokens": optent_tokens,
    }
