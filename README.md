# Cl-Legal-RAG

Pipeline RAG para consultas sobre la Constitucion Politica de la Republica de Chile.

## Estructura

- `data/constitucion.md`: fuente markdown (desde `legalize-cl`)
- `src/config.py`: configuracion y rutas
- `src/parser.py`: chunking semantico por articulo
- `src/database.py`: insercion y busqueda en Chroma local
- `src/history_extractor.py`: extraccion historica desde repo git raw
- `ingest.py`: ingesta y vectorizacion
- `ingest_history.py`: ingesta commit-aware (vigente + historica)
- `app.py`: interfaz Streamlit para consulta

## Requisitos

- Python 3.11+
- `OPENAI_API_KEY` configurada

## Entorno (uv recomendado)

```bash
uv sync
```

Esto crea/actualiza `.venv` e instala dependencias de `pyproject.toml`.

Si no tienes `uv`:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Uso

1. Reemplaza `data/constitucion.md` por el archivo oficial completo.
2. Ejecuta la ingesta:

```bash
uv run python ingest.py
```

3. Levanta la app:

```bash
uv run streamlit run app.py
```

## Ingesta Historica (con commits)

Si quieres indexar cambios historicos por ley/commit:

1. Clona la fuente raw dentro del proyecto:

```bash
git clone https://github.com/opensourcechile/constitucion_chile.git data/raw/constitucion_chile
```

2. Ejecuta:

```bash
uv run python ingest_history.py
```

Esto pobla dos colecciones en Chroma:
- `current_constitution`
- `constitutional_history`

## Buenas practicas recomendadas

- Instalar dependencias solo via `uv sync`.
- Ejecutar comandos con `uv run ...` para garantizar el entorno correcto.
- Mantener `pyproject.toml` como fuente de verdad de dependencias.
- Opcional para calidad de codigo:

```bash
uv run ruff check .
```

## Logs de uso y costo OpenAI

Cada llamada a OpenAI (embeddings y chat) se registra localmente en:
- `logs/openai_usage.jsonl`

Incluye:
- endpoint y modelo
- metadatos de request
- tokens (`prompt`, `completion`, `total`)
- costo estimado en USD

Resumen rapido:

```bash
uv run python scripts_usage_report.py
```

## Comportamiento anti-alucinacion

El prompt de sistema obliga al modelo a responder solo con el contexto recuperado. Si no hay sustento suficiente, entrega un mensaje explicito de falta de informacion oficial en el documento recuperado.
