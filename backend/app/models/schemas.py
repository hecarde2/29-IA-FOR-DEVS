"""
Schemas (modelos Pydantic) que definen la forma de los datos
que entran y salen de la API. FastAPI los usa para:
  1) Validar automáticamente lo que envía el cliente.
  2) Documentar la API en /docs (Swagger) sin esfuerzo extra.
"""

from enum import Enum
from pydantic import BaseModel


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewRequest(BaseModel):
    """Lo que el cliente envía: el texto de la reseña en español."""
    text: str
    optent_tokens: bool = False


class TokenMetrics(BaseModel):
    """Métricas de tokens, para comparar el costo ES vs EN."""
    original_tokens: int
    translated_tokens: int
    tokens_saved_per_request: int


class ExtractedErrorData(BaseModel):
    """Datos estructurados que se extraen de la reseña."""
    error_type: str
    component: str
    severity: SeverityLevel
    summary_en: str
    summary_es: str


class AnalysisResponse(BaseModel):
    """Respuesta completa que devuelve el endpoint /api/analyze."""
    metrics: TokenMetrics
    extracted_data: ExtractedErrorData


class BatchAnalysisResponse(BaseModel):
    """Respuesta para procesamiento por lotes (upload / folder)."""
    total: int
    results: list[AnalysisResponse]
