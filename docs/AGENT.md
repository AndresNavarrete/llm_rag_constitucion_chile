# AGENT

## Objetivo

Continuar y evolucionar `cl-legal-rag` de forma eficiente, manteniendo:
- precision juridica basada solo en contexto recuperado
- trazabilidad historica por commit/ley
- control de costos de OpenAI con logs locales

## Estado actual (baseline)

- Rama principal: `main`
- Ingesta vigente: `scripts/ingest.py`
- Ingesta historica: `scripts/ingest_history.py`
- App: `app/main.py` (modo `Vigente` y `Historica`)
- Chroma local: `chroma_db/`
- Fuente raw historica: `data/raw/constitucion_chile/`
- Log de uso/costo OpenAI: `logs/openai_usage.jsonl`

## Modelos y costos

Config en `src/cl_legal_rag/config.py`:
- Embeddings: `text-embedding-3-small`
- Chat: `gpt-4o-mini`

Observabilidad:
- `src/cl_legal_rag/openai_usage.py` registra tokens/costo estimado por request
- `scripts/report_usage.py` resume costo acumulado

## Start Here (5 min)

1. Sincronizar entorno

```bash
uv sync
```

2. Confirmar API key en `.env`

```env
OPENAI_API_KEY=sk-...
```

3. Actualizar fuente raw (si corresponde)

```bash
git -C data/raw/constitucion_chile pull
```

4. Reingestar historico

```bash
uv run python scripts/ingest_history.py
```

5. Levantar app

```bash
uv run streamlit run app/main.py
```

6. Revisar costo acumulado

```bash
uv run python scripts/report_usage.py
```

## Decisiones de arquitectura ya tomadas

- Dos colecciones vectoriales separadas:
  - `current_constitution`
  - `constitutional_history`
- Chunking por articulo (no por fragmentos arbitrarios).
- Historico indexado incremental por commit (solo archivos/articulos afectados).
- Logging local JSONL para auditoria de uso y costo.

## Restricciones / no romper

- No eliminar trazabilidad de metadatos (`sha`, `ley`, `commit_date`, `source_file`).
- No mezclar colecciones vigente/historica sin control de modo.
- No desactivar logs de uso OpenAI.
- Mantener respuesta restringida al contexto recuperado.

## Instruccion obligatoria de salida del LLM

En la app, toda respuesta del modelo debe comenzar con el prefijo exacto:

`Mi estimado, `

Si una futura sesion modifica prompts, esta instruccion debe permanecer activa.

## Prioridades sugeridas siguientes

1. Filtros historicos por rango de fecha/ley en UI.
2. Evaluacion automatica (set de preguntas + exactitud de cita por articulo).
3. Dashboard de costos en Streamlit (diario, por endpoint, por modelo).
4. Tests unitarios para parser y extractor historico.
