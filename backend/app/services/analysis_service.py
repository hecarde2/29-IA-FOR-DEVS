import asyncio
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncGenerator

os.environ["OMP_NUM_THREADS"] = "12"
os.environ["MKL_NUM_THREADS"] = "12"
os.environ["OPENBLAS_NUM_THREADS"] = "12"

import joblib
import numpy as np
import pandas as pd
import tiktoken
from deep_translator import GoogleTranslator
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.config import TOKEN_ENCODING
from app.models.schemas import (
    AnalysisResponse,
    ExtractedErrorData,
    SeverityLevel,
    TokenMetrics,
)

_encoder = tiktoken.get_encoding(TOKEN_ENCODING)

_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
_vectorizer = joblib.load(_MODELS_DIR / "vectorizer.joblib")
_clf_error = joblib.load(_MODELS_DIR / "error_type_model.joblib")
_clf_sev = joblib.load(_MODELS_DIR / "severity_model.joblib")

_ERROR_TYPE_CLASSES = ["crash", "bug", "performance", "ui", "login", "payment", "other"]
_SEVERITY_CLASSES = ["low", "medium", "high", "critical"]

MAX_CLUSTERS_PER_PRODUCT = 10
MIN_REVIEWS_FOR_CLUSTERING = 50

_COMPONENT_KEYWORDS = {
    "login/auth": ["login", "sesión", "contraseña", "password", "cuenta", "registro",
                    "autentic", "usuario", "iniciar sesión", "registrarse"],
    "perfil": ["perfil", "avatar", "foto de perfil", "biografía", "bio", "descripción",
               "foto", "nombre de usuario"],
    "busqueda": ["buscar", "búsqueda", "filtro", "encontrar", "resultados de búsqueda",
                 "buscador", "explorar"],
    "pago/factura": ["pago", "cobro", "factura", "compra", "tarjeta", "suscripción",
                     "precio", "reembolso", "devolución", "checkout"],
    "navegacion": ["menú", "navegación", "pantalla", "página", "sección", "inicio",
                   "volver", "atrás", "ir a"],
    "notificaciones": ["notificación", "aviso", "alerta", "push", "notificar",
                       "recordatorio", "campana"],
    "sincronizacion": ["sincroniz", "actualiz", "cloud", "nube", "backup",
                       "copiar", "guardar en la nube"],
    "rendimiento": ["lento", "rápido", "velocidad", "carga", "rendimiento",
                    "memoria", "batería", "consumo", "optimiz"],
    "interfaz/ui": ["interfaz", "diseño", "visual", "botón", "icono", "fuente",
                    "color", "tema", "oscuro", "claro"],
    "camara": ["cámara", "foto", "imagen", "escáner", "qr", "código"],
    "chat/mensajes": ["mensaje", "chat", "conversación", "enviar mensaje",
                      "burbuja", "notificar mensaje"],
}

_translator_pool = ThreadPoolExecutor(max_workers=6)


def _extraer_componente(texto: str) -> str:
    texto_lower = texto.lower()
    best_score = 0
    best_component = "general"
    for component, keywords in _COMPONENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in texto_lower)
        if score > best_score:
            best_score = score
            best_component = component
    return best_component


def _generar_summary(texto: str, max_chars: int = 100) -> str:
    texto = texto.strip()
    if not texto:
        return ""
    if len(texto) <= max_chars:
        return texto
    truncated = texto[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 20:
        truncated = truncated[:last_space]
    return truncated + "..."


def _traducir_lote(textos: list[str]) -> list[str]:
    translator = GoogleTranslator(source="es", target="en")
    return list(_translator_pool.map(translator.translate, textos))


_K_FIXO = 5


def _optimal_k(X, k_min=2, k_max=MAX_CLUSTERS_PER_PRODUCT):
    """Heurística rápida: usar k fijo (5) o menos si hay pocos datos."""
    n_samples = X.shape[0]
    if n_samples < 4:
        return 1
    return min(_K_FIXO, n_samples - 1)


def _cluster_producto(textos: list[str]) -> tuple[list[tuple[int, str, int]], list[int] | None]:
    """Retorna ([(cluster_id, texto_representativo, num_resenas), ...], labels_per_texto)"""
    n = len(textos)
    if n == 0:
        return [], None
    if n < MIN_REVIEWS_FOR_CLUSTERING:
        rep = max(textos, key=len)
        return [(0, rep, n)], None

    tfidf = TfidfVectorizer(max_features=500, ngram_range=(1, 2), lowercase=True)
    X = tfidf.fit_transform(textos)

    k = _optimal_k(X)
    k = max(1, k)

    km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=1, max_iter=50, batch_size=2048)
    labels = km.fit_predict(X)

    representantes = []
    for cluster_id in range(k):
        mask = labels == cluster_id
        cluster_indices = np.where(mask)[0]
        if len(cluster_indices) == 0:
            continue
        X_cluster = X[cluster_indices]
        centroid = km.cluster_centers_[cluster_id]
        dists = np.linalg.norm(X_cluster.toarray() - centroid, axis=1)
        rep_idx = cluster_indices[np.argmin(dists)]
        representantes.append((cluster_id, textos[rep_idx], len(cluster_indices)))

    return representantes, labels.tolist()


def _procesar_producto_grupo(
    prod_name: str,
    textos_grupo: list[str],
    optent_tokens: bool,
) -> tuple[list[AnalysisResponse], dict]:
    """Procesa un solo producto: clustering, clasificación, tokens."""
    timings = {}

    if not textos_grupo:
        return [], timings

    t0 = time.time()
    reps, labels = _cluster_producto(textos_grupo)
    timings["clustering"] = time.time() - t0

    rep_textos = [r[1] for r in reps]

    if optent_tokens:
        t0 = time.time()
        translator = GoogleTranslator(source="es", target="en")
        rep_textos_en = list(_translator_pool.map(translator.translate, rep_textos))
        timings["traduccion"] = time.time() - t0
    else:
        rep_textos_en = rep_textos

    t0 = time.time()
    X = _vectorizer.transform(rep_textos)
    pred_error = _clf_error.predict(X)
    pred_sev = _clf_sev.predict(X)
    timings["clasificacion"] = time.time() - t0

    t0 = time.time()
    results = []
    for i, (cluster_id, rep_texto, n_reviews) in enumerate(reps):
        et = _ERROR_TYPE_CLASSES[pred_error[i]]
        sev = _SEVERITY_CLASSES[pred_sev[i]]
        comp = _extraer_componente(rep_texto)
        sum_en = _generar_summary(rep_textos_en[i])
        sum_es = _generar_summary(rep_texto)
        tokens_rep_es = len(_encoder.encode(rep_texto))

        if labels is not None:
            cluster_texts = [textos_grupo[j] for j in range(len(textos_grupo)) if labels[j] == cluster_id]
            tokens_es = sum(len(_encoder.encode(t)) for t in cluster_texts)
        else:
            tokens_es = sum(len(_encoder.encode(t)) for t in textos_grupo)

        if optent_tokens:
            tokens_en = n_reviews * len(_encoder.encode(rep_textos_en[i]))
        else:
            tokens_en = tokens_es

        results.append(AnalysisResponse(
            metrics=TokenMetrics(
                original_tokens=tokens_es,
                translated_tokens=tokens_en,
                tokens_saved_per_request=tokens_es - tokens_rep_es,
            ),
            extracted_data=ExtractedErrorData(
                error_type=et,
                component=comp,
                severity=SeverityLevel(sev),
                summary_en=sum_en,
                summary_es=sum_es,
                producto=prod_name,
                cluster_id=cluster_id,
                reviews_in_cluster=n_reviews,
            ),
        ))
    timings["tiktoken"] = time.time() - t0

    return results, timings


def _procesar_por_producto(
    df: pd.DataFrame,
    col_resena: str,
    col_producto: str,
    optent_tokens: bool,
) -> tuple[list[AnalysisResponse], dict]:
    timings = {}
    all_results = []

    t0 = time.time()
    product_groups = list(df.groupby(col_producto))
    timings["agrupacion"] = time.time() - t0

    productos = [(name, group[col_resena].dropna().astype(str).tolist()) for name, group in product_groups]

    with ThreadPoolExecutor(max_workers=len(productos)) as pool:
        futures = [
            pool.submit(_procesar_producto_grupo, name, textos, optent_tokens)
            for name, textos in productos
        ]
        for fut in futures:
            results_chunk, t_chunk = fut.result()
            all_results.extend(results_chunk)
            for k, v in t_chunk.items():
                timings[k] = timings.get(k, 0.0) + v

    return all_results, timings


def procesar_archivo_excel(contents: bytes, optent_tokens: bool = False) -> list[AnalysisResponse]:
    df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
    col_resena = _detectar_columna_reseña(df)
    col_producto = _detectar_columna_producto(df)

    if col_producto:
        results, _ = _procesar_por_producto(df, col_resena, col_producto, optent_tokens)
    else:
        textos = df[col_resena].dropna().astype(str).tolist()
        results = _procesar_sin_producto(textos, optent_tokens)
    return results


def procesar_carpeta_excel(carpeta: Path, optent_tokens: bool = False) -> list[AnalysisResponse]:
    archivos = list(carpeta.glob("*.xlsx")) + list(carpeta.glob("*.xls"))
    resultados = []
    for archivo in archivos:
        df = pd.read_excel(archivo, engine="openpyxl")
        col_resena = _detectar_columna_reseña(df)
        col_producto = _detectar_columna_producto(df)
        if col_producto:
            lote, _ = _procesar_por_producto(df, col_resena, col_producto, optent_tokens)
        else:
            textos = df[col_resena].dropna().astype(str).tolist()
            lote = _procesar_sin_producto(textos, optent_tokens)
        resultados.extend(lote)
    return resultados


def _procesar_sin_producto(textos: list[str], optent_tokens: bool) -> list[AnalysisResponse]:
    """Fallback cuando no hay columna de producto: clustering global."""
    reps, labels = _cluster_producto(textos)
    results = []
    for cluster_id, rep_texto, n_reviews in reps:
        X = _vectorizer.transform([rep_texto])
        pred_error = _clf_error.predict(X)[0]
        pred_sev = _clf_sev.predict(X)[0]
        et = _ERROR_TYPE_CLASSES[pred_error]
        sev = _SEVERITY_CLASSES[pred_sev]
        comp = _extraer_componente(rep_texto)
        sum_en = _generar_summary(rep_texto)
        sum_es = _generar_summary(rep_texto)
        tokens_rep = len(_encoder.encode(rep_texto))

        if labels is not None:
            cluster_texts = [textos[j] for j in range(len(textos)) if labels[j] == cluster_id]
            tokens_es = sum(len(_encoder.encode(t)) for t in cluster_texts)
        else:
            tokens_es = sum(len(_encoder.encode(t)) for t in textos)

        results.append(AnalysisResponse(
            metrics=TokenMetrics(
                original_tokens=tokens_es,
                translated_tokens=tokens_es,
                tokens_saved_per_request=tokens_es - tokens_rep,
            ),
            extracted_data=ExtractedErrorData(
                error_type=et,
                component=comp,
                severity=SeverityLevel(sev),
                summary_en=sum_en,
                summary_es=sum_es,
                producto="N/A",
                cluster_id=cluster_id,
                reviews_in_cluster=n_reviews,
            ),
        ))
    return results


async def procesar_archivo_excel_stream(
    contents: bytes,
    optent_tokens: bool = False,
) -> AsyncGenerator[str, None]:

    def _emit(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield _emit("progress", {"stage": "lectura", "message": "Leyendo archivo Excel...", "progress": 0})

    df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
    col_resena = _detectar_columna_reseña(df)
    col_producto = _detectar_columna_producto(df)

    if col_producto:
        total_original = len(df[col_resena].dropna())
    else:
        total_original = len(df[col_resena].dropna())

    if total_original == 0:
        yield _emit("progress", {
            "stage": "completo",
            "message": "No se encontraron reseñas en el archivo",
            "progress": 100,
            "total": 0,
            "processed": 0,
            "results": [],
            "timings": {},
        })
        return

    yield _emit("progress", {
        "stage": "lectura",
        "message": f"Archivo leído: {total_original} reseñas",
        "progress": 3,
        "total": total_original,
        "processed": 0,
    })

    if col_producto:
        n_productos = df[col_producto].nunique()
        yield _emit("progress", {
            "stage": "clustering",
            "message": f"Agrupando por producto ({n_productos} productos)...",
            "progress": 8,
            "total": total_original,
            "processed": 0,
        })
    else:
        yield _emit("progress", {
            "stage": "clustering",
            "message": "Agrupando reseñas similares...",
            "progress": 8,
            "total": total_original,
            "processed": 0,
        })

    def _do_full_processing():
        if col_producto:
            return _procesar_por_producto(df, col_resena, col_producto, optent_tokens)
        else:
            textos = df[col_resena].dropna().astype(str).tolist()
            return _procesar_sin_producto(textos, optent_tokens), {}

    all_results, timings = await asyncio.get_event_loop().run_in_executor(
        None, _do_full_processing
    )

    yield _emit("progress", {
        "stage": "clasificacion",
        "message": f"Clasificando {len(all_results)} representantes...",
        "progress": 90,
        "total": total_original,
        "processed": total_original,
    })

    yield _emit("progress", {
        "stage": "completo",
        "message": f"Completado: {total_original} reseñas → {len(all_results)} grupos representativos",
        "progress": 100,
        "total": total_original,
        "processed": total_original,
        "results": [r.model_dump() for r in all_results],
        "timings": timings,
    })


def _detectar_columna_producto(df: pd.DataFrame):
    candidatas = ["producto", "product", "app", "aplicacion", "producto_id", "product_id", "sku"]
    columnas = [c.lower().strip() for c in df.columns]
    for cand in candidatas:
        if cand in columnas:
            return df.columns[columnas.index(cand)]
    return None


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


def analizar_resena(texto_es: str, optent_tokens: bool = False) -> AnalysisResponse:
    X = _vectorizer.transform([texto_es])
    pred_error = _clf_error.predict(X)[0]
    pred_sev = _clf_sev.predict(X)[0]

    if optent_tokens:
        translator = GoogleTranslator(source="es", target="en")
        texto_en = translator.translate(texto_es)
    else:
        texto_en = texto_es

    return AnalysisResponse(
        metrics=TokenMetrics(
            original_tokens=len(_encoder.encode(texto_es)),
            translated_tokens=len(_encoder.encode(texto_en)),
            tokens_saved_per_request=0,
        ),
        extracted_data=ExtractedErrorData(
            error_type=_ERROR_TYPE_CLASSES[pred_error],
            component=_extraer_componente(texto_es),
            severity=SeverityLevel(_SEVERITY_CLASSES[pred_sev]),
            summary_en=_generar_summary(texto_en),
            summary_es=_generar_summary(texto_es),
            producto="",
            cluster_id=-1,
            reviews_in_cluster=1,
        ),
    )

