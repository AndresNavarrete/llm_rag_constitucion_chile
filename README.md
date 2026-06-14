# Cl-Legal-RAG

Pipeline RAG para consultas sobre la Constitucion Politica de la Republica de Chile.

## Estructura

- `data/constitucion.md`: fuente markdown (desde `legalize-cl`)
- `src/config.py`: configuracion y rutas
- `src/parser.py`: chunking semantico por articulo
- `src/database.py`: insercion y busqueda en Chroma local
- `ingest.py`: ingesta y vectorizacion
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

## Comportamiento anti-alucinacion

El prompt de sistema obliga al modelo a responder solo con el contexto recuperado. Si no hay sustento suficiente, entrega un mensaje explicito de falta de informacion oficial en el documento recuperado.
