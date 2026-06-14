# Cl-Legal-RAG: Asistente de Consulta Constitucional

## 1. Objetivo del Proyecto
El objetivo de este proyecto es construir un pipeline de RAG (Retrieval-Augmented Generation) de alcance acotado y listo para producción, que permita realizar consultas en lenguaje natural sobre la **Constitución Política de la República de Chile**. El sistema debe garantizar precisión jurídica basándose estrictamente en los documentos indexados, controlando las alucinaciones del modelo de lenguaje.

Este proyecto forma parte de un portafolio profesional y prioriza la modularidad, el código limpio y la correcta estrategia de procesamiento de datos por sobre la complejidad de la infraestructura en la nube.

---

## 2. Alcance y Límites (Scope)

### Dentro del Alcance (IN)
*   **Fuente de datos:** Únicamente el archivo Markdown correspondiente a la Constitución Política de Chile vigente, extraído del repositorio indexador `legalize-dev/legalize-cl`.
*   **Estrategia de Chunking:** Segmentación semántica basada en la estructura del documento. Cada fragmento (*chunk*) indexado debe corresponder estrictamente a un Artículo completo (o secciones lógicas equivalentes si el artículo es excesivamente largo), manteniendo sus encabezados y metadatos.
*   **Base de Datos Vectorial:** Implementación local mediante `ChromaDB` o `FAISS`.
*   **Orquestación y LLM:** Uso de `LangChain` o `LlamaIndex` para el pipeline. Uso de APIs comerciales (OpenAI `text-embedding-3-small` para embeddings y `gpt-4o-mini` para generación).
*   **Interfaz de Usuario:** Una aplicación web simple y funcional desarrollada en `Streamlit`.
*   **Control de Alucinaciones:** Prompt Engineering estricto con instrucciones del sistema para responder exclusivamente con el contexto proveído.

### Fuera del Alcance (OUT) - *No implementar*
*   Indexación de la totalidad de las 6,000+ leyes del repositorio original.
*   Historial de cambios de las leyes mediante embeddings (el análisis de versiones/commits de Git queda fuera de esta iteración).
*   Despliegue en clusters vectoriales en la nube (ej. Pinecone).
*   Sistemas complejos de re-ranking (ej. Cohere) o arquitecturas multi-agente.

---

## 3. Arquitectura del Sistema

El proyecto está dividido en dos fases desacopladas e independientes:

### Fase 1: Pipeline de Ingesta (`ingest.py`)
Proceso de ejecución única (o bajo demanda) que prepara la base de datos:
1.  **Lectura:** Carga el archivo Markdown de la Constitución.
2.  **Parsing/Chunking:** Limpia el texto y lo fragmenta utilizando expresiones regulares o parsers de Markdown para separar el contenido por artículos (`## Artículo X`).
3.  **Metadatos:** Asocia a cada fragmento metadatos clave: `{"articulo": "X", "capitulo": "Y", "fuente": "legalize-cl"}`.
4.  **Vectorización y Almacenamiento:** Genera embeddings y persiste los vectores y el texto en un directorio local de `ChromaDB` (`./chroma_db`).

### Fase 2: Pipeline de Consulta e Interfaz (`app.py`)
Aplicación en tiempo real para el usuario final:
1.  **Interfaz (Streamlit):** Caja de texto para la pregunta del usuario y contenedor del historial de chat.
2.  **Recuperación (Retrieval):** Convierte la consulta en vector, busca los $k$ fragmentos más similares en la base de datos local de Chroma ($k=3$ por defecto).
3.  **Aumento (Augmentation):** Inyecta los textos recuperados dentro de un prompt estructurado de sistema.
4.  **Generación (Generation):** Envía el prompt al LLM y despliega la respuesta en la interfaz de manera progresiva (*streaming*).

---

## 4. Instrucciones para el Agente de Código (Prompt de Inicialización)

> **Instrucciones de desarrollo:**
> 1. Mantén un diseño de código modular. Separa claramente las funciones de procesamiento de texto de las funciones de llamadas a la API.
> 2. Evita la densidad de código; utiliza type hinting y docstrings en las funciones principales.
> 3. Implementa manejo de excepciones para la lectura de archivos y fallas en las llamadas de API de OpenAI.
> 4. Al configurar el prompt del sistema para el LLM, sé explícito: si la respuesta no se deduce del contexto recuperado, el modelo debe declarar que carece de información oficial en el documento.

---

## 5. Estructura de Archivos Propuesta

```text
cl-legal-rag/
│
├── data/
│   └── constitucion.md       # Archivo origen extraído de legalize-cl
│
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuración de variables de entorno y rutas
│   ├── parser.py             # Lógica personalizada de chunking por artículos
│   └── database.py           # Conexión, inserción y búsqueda en ChromaDB
│
├── ingest.py                 # Script CLI ejecutable para poblar la BD vectorial
├── app.py                    # Aplicación de interfaz de usuario (Streamlit)
│
├── requirements.txt          # Dependencias (langchain/llamaindex, chromadb, streamlit, openai)
└── README.md