"""
Capa de "servicio": aquí vive la lógica de negocio, separada del router.
Esto permite reutilizar y probar la lógica sin depender de FastAPI,
y es el lugar donde en el futuro se conectaría un traductor real
o un modelo de IA para la extracción de datos.
"""

import io
import json
from pathlib import Path

import ollama
import pandas as pd
import tiktoken
from deep_translator import GoogleTranslator

from app.core.config import TOKEN_ENCODING
from app.models.schemas import (
    AnalysisResponse,
    ExtractedErrorData,
    SeverityLevel,
    TokenMetrics,
)

_encoder = tiktoken.get_encoding(TOKEN_ENCODING)


def _traducir_es_a_en(texto_es: str) -> str:
    return GoogleTranslator(source="es", target="en").translate(texto_es)


def _extraer_datos_error(texto_es: str, texto_en: str) -> ExtractedErrorData:
    prompt = (
        "Extrae datos estructurados de una reseña de usuario de una app. "
        "Devuelve SOLO un JSON válido con las siguientes claves: "
        "\"error_type\" (tipo de error: crash, bug, performance, ui, login, payment, other), "
        "\"component\" (componente afectado), "
        "\"severity\" (low, medium, high, critical), "
        "\"summary_en\" (brief English summary), "
        "\"summary_es\" (brief Spanish summary). "
        "Texto de la reseña en inglés: " + texto_en
    )
    response = ollama.generate(
        model="deepseek-r1:1.5b",
        prompt=prompt,
        format={
            "type": "object",
            "properties": {
                "error_type": {"type": "string"},
                "component": {"type": "string"},
                "severity": {"type": "string"},
                "summary_en": {"type": "string"},
                "summary_es": {"type": "string"},
            },
            "required": ["error_type", "component", "severity", "summary_en", "summary_es"],
        },
    )
    result = json.loads(response["response"])
    return ExtractedErrorData(
        error_type=result.get("error_type", "other"),
        component=result.get("component", "unknown"),
        severity=SeverityLevel(result.get("severity", "medium")),
        summary_en=result.get("summary_en", ""),
        summary_es=result.get("summary_es", ""),
    )


def _detectar_columna_reseña(df: pd.DataFrame) -> str:
    candidatas = ["reseña", "review", "text", "comment", "texto", "review_text", "resena"]
    columnas = [c.lower().strip() for c in df.columns]
    for cand in candidatas:
        if cand in columnas:
            return df.columns[columnas.index(cand)]
    if "reseña" in columnas or "review" in columnas:
        for c in df.columns:
            if c.lower().strip() in ("reseña", "review"):
                return c
    for c in df.columns:
        if any(kw in c.lower() for kw in ["review", "rese", "text", "comment"]):
            return c
    return df.columns[0]


def _analizar_fila(texto: str, optent_tokens: bool) -> AnalysisResponse:
    texto = str(texto).strip()
    if not texto:
        return AnalysisResponse(
            metrics=TokenMetrics(original_tokens=0, translated_tokens=0, tokens_saved_per_request=0),
            extracted_data=ExtractedErrorData(
                error_type="unknown",
                component="none",
                severity=SeverityLevel.LOW,
                summary_en="",
                summary_es="",
            ),
        )
    return analizar_resena(texto, optent_tokens=optent_tokens)


def analizar_resena(texto_es: str, optent_tokens: bool = False) -> AnalysisResponse:
    if optent_tokens:
        texto_en = _traducir_es_a_en(texto_es)
    else:
        texto_en = texto_es

    count_es = len(_encoder.encode(texto_es))
    count_en = len(_encoder.encode(texto_en))
    tokens_ahorrados = count_es - count_en

    metrics = TokenMetrics(
        original_tokens=count_es,
        translated_tokens=count_en,
        tokens_saved_per_request=tokens_ahorrados,
    )

    extracted_data = _extraer_datos_error(texto_es, texto_en)

    return AnalysisResponse(metrics=metrics, extracted_data=extracted_data)


def procesar_archivo_excel(contents: bytes, optent_tokens: bool = False) -> list:
    df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
    col_reseña = _detectar_columna_reseña(df)
    resultados = []
    for valor in df[col_reseña]:
        resultados.append(_analizar_fila(valor, optent_tokens))
    return resultados


def procesar_carpeta_excel(carpeta: Path, optent_tokens: bool = False) -> list:
    archivos_xlsx = list(carpeta.glob("*.xlsx")) + list(carpeta.glob("*.xls"))
    resultados = []
    for archivo in archivos_xlsx:
        df = pd.read_excel(archivo, engine="openpyxl")
        col_reseña = _detectar_columna_reseña(df)
        for valor in df[col_reseña]:
            resultados.append(_analizar_fila(valor, optent_tokens))
    return resultados
