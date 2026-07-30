"""
Entrena los clasificadores para error_type y severity
usando pseudo-labels generadas por keywords sobre el dataset real.

Uso:
    cd backend && venv/bin/python scripts/train_pipeline.py
"""

import os
import re
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "12"
os.environ["MKL_NUM_THREADS"] = "12"
os.environ["OPENBLAS_NUM_THREADS"] = "12"

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.svm import LinearSVC

TIMINGS = {}

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "resenas_productos_50k.xlsx"
MODELS_DIR = BASE / "app" / "models"

ERROR_TYPE_KEYWORDS = {
    "crash": [
        "se cierra", "cierra inesperadamente", "crash", "bloquea", "pantallazo",
        "se apaga", "se sale", "deja de funcionar", "no funciona", "error inesperado",
        "falla al abrir", "se detiene", "congela", "freeze", "colgar", "se cuelga",
        "reinicia", "pantalla en negro", "no responde", "deja de responder",
        "se cerró", "se cerró sola", "no abre", "explota", "tira error",
    ],
    "bug": [
        "bug", "error", "fallo", "incorrecto", "defecto", "mal",
        "no carga", "no aparece", "no muestra", "problema", "falla",
        "no actualiza", "no guarda", "no envía", "no recibe", "no funciona bien",
        "está mal", "roto", "dañado", "corrupto", "no sincroniza",
        "información incorrecta", "datos incorrectos", "error al guardar",
        "muestra mal", "calcula mal", "no coincide",
    ],
    "performance": [
        "lento", "tarda", "congel", "rendimiento", "performance", "pesado",
        "optimiz", "memoria", "batería", "consume", "lag", "trabado",
        "tarda mucho", "demora", "se demora", "carga lento", "responde lento",
        "consume mucha batería", "consume mucha memoria", "ocupa mucho espacio",
        "calienta", "sobrecalienta", "tarda en abrir", "tarda en cargar",
    ],
    "ui": [
        "interfaz", "ui", "diseño", "pantalla", "botón", "menú",
        "navegación", "visual", "mostrar", "fuente", "tamaño",
        "letra", "color", "icono", "imagen", "layout", "maquetación",
        "no se ve", "se ve mal", "desordenado", "feo", "estética",
        "responsivo", "no responsivo", "se superpone", "corte",
        "texto cortado", "elementos superpuestos", "difícil de leer",
    ],
    "login": [
        "login", "inicio de sesión", "contraseña", "password", "cuenta",
        "usuario", "autentic", "registro", "log in", "sign in",
        "iniciar sesión", "registrarse", "olvidé mi contraseña",
        "no puedo ingresar", "no me deja entrar", "sesión expirada",
        "token", "doble factor", "2fa", "verificación", "código de verificación",
        "no recibe código", "sms", "correo de verificación",
    ],
    "payment": [
        "pago", "cobro", "tarjeta", "factura", "compra", "precio",
        "suscripción", "payment", "checkout", "carrito", "cobrar",
        "me cobraron", "doble cobro", "reembolso", "devolución",
        "no se procesa el pago", "error de pago", "tarjeta rechazada",
        "no me llega la factura", "plan", "premium", "pro", "versión de pago",
    ],
}

SEVERITY_KEYWORDS = {
    "critical": [
        "crítico", "critico", "urgente", "grave",
        "bloquea", "no funciona", "se cierra", "pérdida de datos",
        "seguridad", "inaccesible", "no puedo acceder", "datos perdidos",
        "robaron", "hackearon", "violación", "fuga de información",
        "dinero perdido", "cobro indebido", "emergencia",
    ],
    "high": [
        "muy malo", "terrible", "pésimo", "fatal", "horrible",
        "frustrante", "imposible", "inservible", "inútil",
        "no sirve", "no sirve para nada", "basura",
        "pésima experiencia", "muy frustrante", "inaceptable",
        "decepcionante", "no lo recomiendo",
    ],
    "medium": [
        "malo", "problema", "error", "bug", "lento", "feo", "difícil",
        "molesto", "incómodo", "regular", "podría mejorar",
        "esperaba más", "no me gustó", "decepciona",
        "mejorable", "tiene fallos", "falla a veces",
    ],
    "low": [
        "leve", "menor", "pequeño", "poco", "sugerencia", "mejora",
        "detalle", "cosmético", "estético", "opcional",
        "sería bueno", "sería mejor", "me gustaría",
        "podría añadir", "sugiero", "propongo", "recomendación",
        "detalle menor", "casi perfecto",
    ],
}

COMPONENT_KEYWORDS = {
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


def _pseudo_label_error_type(texto: str) -> str:
    texto_lower = texto.lower()
    for error_type, keywords in ERROR_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in texto_lower:
                return error_type
    return "other"


def _pseudo_label_severity(texto: str) -> str:
    texto_lower = texto.lower()
    exclamation_score = texto.count("!") + texto.count("¡")
    question_score = texto.count("?") + texto.count("¿")
    caps_ratio = sum(1 for c in texto if c.isupper()) / max(len(texto), 1) if texto else 0

    for severity, keywords in SEVERITY_KEYWORDS.items():
        for kw in keywords:
            if kw in texto_lower:
                return severity

    if exclamation_score >= 3 or caps_ratio > 0.5:
        return "high"
    if exclamation_score >= 1:
        return "medium"
    return "low"


def _extraer_componente(texto: str) -> str:
    texto_lower = texto.lower()
    best_score = 0
    best_component = "general"
    for component, keywords in COMPONENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in texto_lower)
        if score > best_score:
            best_score = score
            best_component = component
    return best_component


SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
SEVERITY_CLASSES = ["low", "medium", "high", "critical"]
ERROR_TYPE_CLASSES = ["crash", "bug", "performance", "ui", "login", "payment", "other"]


def train():
    print("=" * 60)
    print("Entrenamiento del pipeline de clasificación")
    print("=" * 60)

    models_dir = MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    t_read = time.time()
    df = pd.read_excel(DATA_PATH, engine="openpyxl")
    textos = df["reseña"].dropna().astype(str).tolist()
    TIMINGS["lectura"] = time.time() - t_read
    print(f"\n✓ Lectura: {TIMINGS['lectura']:.2f}s | {len(textos)} reseñas")

    t_label = time.time()
    y_error_text = [_pseudo_label_error_type(t) for t in textos]
    y_sev_text = [_pseudo_label_severity(t) for t in textos]
    components = [_extraer_componente(t) for t in textos]
    TIMINGS["pseudo_labels"] = time.time() - t_label
    print(f"✓ Pseudo-labels: {TIMINGS['pseudo_labels']:.2f}s")

    label_counts = {}
    for lbl in y_error_text:
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
    print(f"  error_type distribución: {label_counts}")

    sev_counts = {}
    for lbl in y_sev_text:
        sev_counts[lbl] = sev_counts.get(lbl, 0) + 1
    print(f"  severity distribución: {sev_counts}")

    y_error = np.array([ERROR_TYPE_CLASSES.index(e) for e in y_error_text])
    y_sev = np.array([SEVERITY_CLASSES.index(s) for s in y_sev_text])

    t_vec = time.time()
    vectorizer = HashingVectorizer(
        n_features=2 ** 20,
        ngram_range=(1, 2),
        alternate_sign=False,
        analyzer="word",
        lowercase=True,
    )
    X = vectorizer.transform(textos)
    TIMINGS["vectorizacion"] = time.time() - t_vec
    print(f"✓ Vectorización: {TIMINGS['vectorizacion']:.2f}s | matriz: {X.shape}")

    t_train_err = time.time()
    clf_error = LinearSVC(
        random_state=42,
        max_iter=2000,
        dual="auto",
        tol=1e-4,
        C=1.0,
        multi_class="ovr",
    )
    clf_error.fit(X, y_error)
    TIMINGS["train_error"] = time.time() - t_train_err
    acc_err = (clf_error.predict(X) == y_error).mean()
    print(f"✓ Entrenamiento error_type: {TIMINGS['train_error']:.2f}s | accuracy: {acc_err:.4f}")

    t_train_sev = time.time()
    clf_sev = LinearSVC(
        random_state=42,
        max_iter=2000,
        dual="auto",
        tol=1e-4,
        C=1.0,
        multi_class="ovr",
    )
    clf_sev.fit(X, y_sev)
    TIMINGS["train_severity"] = time.time() - t_train_sev
    acc_sev = (clf_sev.predict(X) == y_sev).mean()
    print(f"✓ Entrenamiento severity: {TIMINGS['train_severity']:.2f}s | accuracy: {acc_sev:.4f}")

    t_save = time.time()
    joblib.dump(vectorizer, models_dir / "vectorizer.joblib")
    joblib.dump(clf_error, models_dir / "error_type_model.joblib")
    joblib.dump(clf_sev, models_dir / "severity_model.joblib")
    TIMINGS["guardado"] = time.time() - t_save
    print(f"✓ Modelos guardados en {models_dir}")

    total = sum(TIMINGS.values())
    print(f"\n{'=' * 60}")
    print(f"Tiempo total de entrenamiento: {total:.2f}s")
    print(f"Modelos guardados:")
    print(f"  {models_dir / 'vectorizer.joblib'}")
    print(f"  {models_dir / 'error_type_model.joblib'}")
    print(f"  {models_dir / 'severity_model.joblib'}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train()
