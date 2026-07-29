## 🚀 Historia de Usuario (HU)

**ID:** HU-012

**Título:** Ingesta flexible de datos y optimización opcional de tokens para análisis de reseñas en Excel

**Epic:** Infraestructura de Procesamiento de LLM & Ingesta de Datos

**Estimación:** **3 Story Points**

---

### **Como:**

Analista de Datos / Desarrollador de Software

### **Quiero:**

Un sistema de ingesta que pueda procesar archivos Excel individuales o leer una carpeta completa de archivos Excel con reseñas de usuarios, aplicando de forma opcional un paso de optimización/traducción de tokens vía `/api/analyze`

### **Para:**

Extraer el problema técnico principal de cada reseña con flexibilidad en la fuente de datos y control sobre los costos de uso del LLM.

---

## 📄 Contexto de Negocio & Escenario

El equipo necesita procesar comentarios de usuarios almacenados en formatos de hoja de cálculo. La pipeline debe permitir dos modalidades de entrada (archivo único o lote en carpeta) y permitir activar o desactivar la traducción previa según las necesidades del análisis o el presupuesto del cliente.

* **Ejemplo de fila/reseña a procesar (Español):**
> *"La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil desde la galería de mi teléfono."*



---

## ✅ Criterios de Aceptación (Definition of Done)

### **Criterio 1: Ingesta Flexible de Fuentes Excel**

* [ ] El sistema debe permitir elegir entre dos modos de carga:
* **Modo A (Directo):** Cargar/recibir un archivo `.xlsx` individual desde la interfaz o comando.
* **Modo B (Lote):** Indicar la ruta de una carpeta local para leer y consolidar automáticamente todos los archivos `.xlsx` presentes.


* [ ] Se debe validar que la columna con el texto de la reseña sea detectada correctamente en ambos modos.

### **Criterio 2: Pipeline de Optimización de Tokens Opcional**

* [ ] La ejecución del pipeline debe incluir una bandera/parámetro (`optent_tokens: True/False`).
* [ ] **Si la opción está activa (`True`):** El texto se envía a `/api/analyze` para traducirlo a inglés antes de pasarlo al LLM principal (usando `o200k_base`).
* [ ] **Si la opción está desactivada (`False`):** El texto original en español se procesa directamente en el LLM principal sin pasar por el módulo de traducción.

### **Criterio 3: Análisis de Impacto Económico y Salida Estructurada**

* [ ] El sistema debe permitir calcular el volumen total de tokens y la diferencia de costo ($USD a **$2.50 por millón de tokens**) al comparar el procesamiento directo vs. el optimizado para un volumen de **10,000 reseñas/día**.
* [ ] El modelo debe exportar los resultados clasificados en un esquema JSON/Excel limpio (ejemplo: `{"error_type": "crash", "component": "profile_picture_upload"}`).

---

## 🏷️ Notas Técnicas

* **Librerías sugeridas para ingesta:** `pandas` / `openpyxl` / `pathlib`.
* **Tokenizador & API:** `tiktoken` (`o200k_base`), `deep_translator`, FastAPI.