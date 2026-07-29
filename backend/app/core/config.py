"""
Configuración central del backend.
Aquí se concentran las constantes que otros módulos necesitan,
para no tener valores "quemados" (hardcodeados) repartidos por el código.
"""
from pyfiglet import Figlet

# Nombre y metadatos de la API (se usan al crear la app FastAPI)
APP_TITLE = "App Store Review Analyzer"
APP_DESCRIPTION = (
    "API que analiza reseñas de usuarios: cuenta tokens con tiktoken, "
    "simula una traducción ES->EN y extrae datos estructurados del error reportado."
)
APP_VERSION = "1.0.0"

# Codificador de tokens usado por tiktoken (el mismo que usan modelos tipo GPT-4o)
TOKEN_ENCODING = "o200k_base"

# Precio de referencia usado solo para el script de análisis masivo (USD por 1M tokens)
PRICE_PER_MILLION_TOKENS_USD = 2.50

# Host/puerto por defecto cuando se levanta con uvicorn
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# ─── GEOXOR Rainbow Banner ───
RAINBOW_COLORS = [
    "\033[91m",  # Red
    "\033[93m",  # Yellow
    "\033[92m",  # Green
    "\033[96m",  # Cyan
    "\033[94m",  # Blue
    "\033[95m",  # Magenta
]

BANNER_RESET = "\033[0m"

_fig = Figlet(font="big")
GEOXOR_BANNER_LINES = _fig.renderText("Geoxor").splitlines()
