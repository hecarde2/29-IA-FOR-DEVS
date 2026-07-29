"""
Script utilitario: genera un Excel con reseñas ficticias (datos de prueba).
No forma parte del backend en sí; es una herramienta de apoyo para tener
datos con los que probar el endpoint /api/analyze de forma masiva.

Uso (desde la carpeta backend/):
    python scripts/generar_excel.py
"""

import random
import sys
from pathlib import Path

import pandas as pd
from faker import Faker

# Carpeta data/ del backend, donde se guarda el Excel generado
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def generar_resenas_excel(nombre_archivo="resenas_productos_50k.xlsx", num_filas=50000):
    print(f"Generando {num_filas} registros en español...")
    fake = Faker("es_ES")

    productos_cat = [
        "Audífonos Bluetooth Wireless", "Smartphone Pro Max 256GB",
        "Laptop Gamer 15.6''", "Reloj Inteligente Sport", "Cámara Digital 4K"
    ]

    plantillas = [
        "Excelente producto, superó mis expectativas.",
        "Llegó a tiempo y en perfecto estado. Muy recomendado.",
        "La aplicación se cierra inesperadamente cada vez que intento subir una foto.",
        "No me gustó la calidad del producto, esperaba más.",
        "Pésimo servicio de entrega, llegó dañado."
    ]

    data = []
    for _ in range(num_filas):
        resena = "" if random.random() < 0.25 else f"{random.choice(plantillas)} {fake.sentence(nb_words=6)}"
        data.append({
            "id_cliente": fake.uuid4()[:8].upper(),
            "cliente": fake.name(),
            "ciudad": fake.city(),
            "producto": random.choice(productos_cat),
            "reseña": resena,
        })

    df = pd.DataFrame(data)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ruta_salida = DATA_DIR / nombre_archivo
    df.to_excel(ruta_salida, index=False, engine="openpyxl")
    print(f"¡Archivo generado con éxito: {ruta_salida}!")


if __name__ == "__main__":
    num_filas = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    generar_resenas_excel(num_filas=num_filas)
