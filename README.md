# Cl-Legal-RAG

Asistente RAG para consultas sobre la Constitucion Politica de la Republica de Chile, con soporte para:
- consulta de texto vigente
- consulta historica por commits/leyes
- trazabilidad de costo y uso de OpenAI en logs locales

## Estado del proyecto

Implementado y funcional en local:
- Ingesta vigente (`scripts/ingest.py`) a coleccion `current_constitution`
- Ingesta historica commit-aware (`scripts/ingest_history.py`) a coleccion `constitutional_history`
- App Streamlit con modo `Vigente` y `Historica`
- Registro local de uso/costo OpenAI en `logs/openai_usage.jsonl`

## Arquitectura

- `data/raw/constitucion_chile/`
  - Repo raw fuente (`opensourcechile/constitucion_chile`) con historial Git.
- `src/cl_legal_rag/parser.py`
  - Chunking por articulos y metadatos juridicos.
- `src/cl_legal_rag/history_extractor.py`
  - Extraccion incremental por commit (solo archivos/articulos modificados).
- `src/cl_legal_rag/database.py`
  - Chroma local y retrieval.
- `src/cl_legal_rag/embeddings.py`
  - Cliente embeddings con batching defensivo y logging de uso.
- `src/cl_legal_rag/openai_usage.py`
  - Estimacion de costos y escritura de eventos JSONL.
- `app/main.py`
  - UI Streamlit + chat con control anti-alucinacion.

## Requisitos

- Python 3.11+
- `uv`
- `OPENAI_API_KEY` en `.env`

## Setup rapido

1. Instalar dependencias

```bash
uv sync
```

2. Configurar API key

Crear `.env` en la raiz:

```env
OPENAI_API_KEY=sk-...
```

3. Ingesta historica recomendada

```bash
uv run python scripts/ingest_history.py
```

4. Levantar app

```bash
uv run streamlit run app/main.py
```

## Fuente de datos raw

Este proyecto usa como fuente historica:
- `https://github.com/opensourcechile/constitucion_chile.git`

Si no esta clonado en `data/raw/constitucion_chile`, ejecuta:

```bash
git clone https://github.com/opensourcechile/constitucion_chile.git data/raw/constitucion_chile
```

## Logs de uso y costo OpenAI

Archivo:
- `logs/openai_usage.jsonl`

Cada evento guarda:
- `endpoint`, `model`
- metadatos de request
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `estimated_cost_usd`

Resumen:

```bash
uv run python scripts/report_usage.py
```

## Costos (orden de magnitud)

Con el dataset actual, la ingesta suele ser de costo bajo. Aun asi, monitorea siempre con `scripts/report_usage.py` y ajusta:
- `retrieval_k`
- largo de contexto inyectado
- numero de consultas

## Buenas practicas

- Usar `uv run ...` para ejecutar siempre dentro del entorno correcto.
- No versionar `.env` ni `logs/`.
- Mantener el repo raw como fuente de verdad historica.
- Re-ingestar cuando actualices el repo raw.

## Troubleshooting

- Error `max_tokens_per_request` en embeddings:
  - ya mitigado con batching en `src/cl_legal_rag/embeddings.py`.
- Respuesta sin contexto suficiente:
  - el sistema debe responder con mensaje explicito de falta de informacion oficial.

## Documento de continuidad

Para retomar el proyecto en otra sesion con agentes, usa:
- `docs/AGENT.md`
