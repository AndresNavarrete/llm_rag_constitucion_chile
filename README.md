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

- Python 3.10+
- `OPENAI_API_KEY` configurada

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Uso

1. Reemplaza `data/constitucion.md` por el archivo oficial completo.
2. Ejecuta la ingesta:

```bash
python ingest.py
```

3. Levanta la app:

```bash
streamlit run app.py
```

## Ingesta Historica (con commits)

Si quieres indexar cambios historicos por ley/commit:

1. Clona la fuente raw dentro del proyecto:

```bash
git clone https://github.com/opensourcechile/constitucion_chile.git data/raw/constitucion_chile
```

2. Ejecuta:

```bash
python ingest_history.py
```

Esto pobla dos colecciones en Chroma:
- `current_constitution`
- `constitutional_history`

## Comportamiento anti-alucinacion

El prompt de sistema obliga al modelo a responder solo con el contexto recuperado. Si no hay sustento suficiente, entrega un mensaje explicito de falta de informacion oficial en el documento recuperado.
