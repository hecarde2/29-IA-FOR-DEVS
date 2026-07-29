"""
Script CLIENTE (no forma parte del backend).

Este script es el que demuestra "cómo se conecta" al backend:
lee el Excel de reseñas y le hace una petición HTTP POST a
http://127.0.0.1:8000/api/analyze por cada reseña, en paralelo
(usando asyncio + httpx), y al final imprime métricas agregadas.

REQUISITO: el backend debe estar corriendo antes de ejecutar este script
    uvicorn app.main:app --reload      (desde la carpeta backend/)

Uso (desde la carpeta backend/):
    python scripts/procesar_excel_async.py
"""

import asyncio
import time
from pathlib import Path

import httpx
import pandas as pd
from tqdm.asyncio import tqdm

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXCEL_FILE = DATA_DIR / "resenas_productos_50k.xlsx"

# URL del backend. Debe coincidir con host/puerto donde corre uvicorn.
API_URL = "http://127.0.0.1:8000/api/analyze"
MAX_CONCURRENT_REQUESTS = 50

PRICE_PER_MILLION_TOKENS_USD = 2.50


async def send_review(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, review_text: str):
    async with semaphore:
        try:
            response = await client.post(API_URL, json={"text": review_text}, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


async def main():
    start_time = time.time()
    print("📂 Cargando dataset...")
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

    # Filtrar el 25% de reseñas vacías
    df_validas = df[df["reseña"].astype(str).str.strip().ne("") & df["reseña"].notna()]
    reseñas = df_validas["reseña"].tolist()

    print(f"📊 Registros totales: {len(df):,}")
    print(f"✅ Reseñas válidas enviadas: {len(reseñas):,}")
    print(f"🔌 Conectando al backend en: {API_URL}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    limits = httpx.Limits(max_keepalive_connections=MAX_CONCURRENT_REQUESTS, max_connections=MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [send_review(client, semaphore, texto) for texto in reseñas]
        results = await tqdm.gather(*tasks, desc="Procesando")

    total_es, total_en, ahorrados = 0, 0, 0
    for res in results:
        if "metrics" in res:
            m = res["metrics"]
            total_es += m["original_tokens"]
            total_en += m["translated_tokens"]
            ahorrados += m["tokens_saved_per_request"]

    elapsed = time.time() - start_time
    costo_es = (total_es / 1_000_000) * PRICE_PER_MILLION_TOKENS_USD
    costo_en = (total_en / 1_000_000) * PRICE_PER_MILLION_TOKENS_USD

    print("\n" + "=" * 50)
    print(f"⏱️ Tiempo total: {elapsed:.2f} segundos")
    print(f"🔹 Tokens Español: {total_es:,}")
    print(f"🔹 Tokens Inglés: {total_en:,}")
    print(f"💡 Tokens Ahorrados: {ahorrados:,}")
    print(f"💵 Ahorro económico: ${costo_es - costo_en:.4f} USD")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
