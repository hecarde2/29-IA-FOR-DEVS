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

Extraer el problema técnico principal de cada reseña con flexibilidad en la fuente de datos y control sobre los costos de uso del LLM. Además, optimizar tokens mediante clustering semántico por producto (50k reseñas → ~25 grupos representativos).

---

## 📄 Contexto de Negocio & Escenario

El equipo necesita procesar comentarios de usuarios almacenados en formatos de hoja de cálculo. La pipeline debe permitir dos modalidades de entrada (archivo único o lote en carpeta) y permitir activar o desactivar la traducción previa según las necesidades del análisis o el presupuesto del cliente.

* **Ejemplo de fila/reseña a procesar (Español):**
> *"La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil desde la galería de mi teléfono."*

---

## ✅ Criterios de Aceptación (Definition of Done)

### **Criterio 1: Ingesta Flexible de Fuentes Excel**

* [x] El sistema permite elegir entre dos modos de carga:
  * **Modo A (Directo):** Cargar/recibir un archivo `.xlsx` individual desde la interfaz o comando.
  * **Modo B (Lote):** Indicar la ruta de una carpeta local para leer y consolidar automáticamente todos los archivos `.xlsx` presentes.
* [x] La columna con el texto de la reseña es detectada automáticamente (keywords: `reseña`, `review`, `text`, `comment`, `texto`, `review_text`, `resena`).
* [x] La columna de producto es detectada automáticamente (keywords: `producto`, `product`, `app`, `aplicacion`).

### **Criterio 2: Pipeline de Optimización de Tokens Opcional**

* [x] La ejecución incluye la bandera `optent_tokens: True/False`.
* [x] **Si está activa (`True`):** El texto se traduce a inglés con `deep_translator` antes de la clasificación.
* [x] **Si está desactivada (`False`):** El texto original en español se procesa directamente.
* [x] Métricas de tokens con `tiktoken` (`o200k_base`) sobre todo el cluster.

### **Criterio 3: Análisis de Impacto Económico y Salida Estructurada**

* [x] Endpoint `GET /api/analyze/cost-estimate` calcula tokens y costo a `$2.50/M tokens`.
* [x] Exportación en JSON/Excel con schema limpio: `{"error_type", "component", "severity", "summary_en", "summary_es", "producto", "cluster_id", "reviews_in_cluster"}`.

### **Criterio 4: Agrupación Semántica por Producto**

* [x] Las reseñas se agrupan por producto (`groupby('producto')`).
* [x] Dentro de cada producto, clustering semántico con TF-IDF + MiniBatchKMeans.
* [x] k óptimo determinado por silhouette score (máx 10 clusters por producto).
* [x] Se selecciona 1 reseña representativa por cluster (más cercana al centroide).
* [x] Métricas de tokens reflejan el total del cluster, no solo el representante.
* [x] Reducción típica: 50k reseñas → ~25 grupos (99.9% de reducción).

### **Criterio 5: Progreso en Tiempo Real**

* [x] Endpoint SSE `POST /api/analyze/upload/stream` envía eventos con etapas: lectura, clustering, clasificación, completo.
* [x] Frontend muestra barra de progreso con etapa actual y reseñas procesadas.

---

## 🏷️ Notas Técnicas

* **Librerías para ingesta:** `pandas` / `openpyxl` / `pathlib`.
* **Clustering:** `scikit-learn` (`TfidfVectorizer`, `MiniBatchKMeans`, `silhouette_score`).
* **Clasificación:** `scikit-learn` (`HashingVectorizer`, `LinearSVC`), `joblib` para serialización.
* **Tokenizador & API:** `tiktoken` (`o200k_base`), `deep_translator`, FastAPI, `python-multipart`.
* **CPU tuning:** `OMP_NUM_THREADS=12`, `MKL_NUM_THREADS=12`, `OPENBLAS_NUM_THREADS=12`.
* **Rendimiento:** 50k reseñas procesadas en ~4.6s (sin traducción).
