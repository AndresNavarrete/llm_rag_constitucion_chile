# AGENT

## Objetivo

Continuar y evolucionar `cl-legal-rag` de forma eficiente, manteniendo:
- precisión jurídica basada solo en contexto recuperado
- trazabilidad histórica por commit/ley
- control de costos de OpenAI con logs locales

---

## Estado actual (baseline)

- Rama principal: `main`
- Ingesta vigente: `scripts/ingest.py`
- Ingesta histórica: `scripts/ingest_history.py`
- App: `app/main.py` (modo `Vigente` y `Histórica`)
- Chroma local: `chroma_db/`
- Fuente raw histórica: `data/raw/constitucion_chile/`
- Log de uso/costo OpenAI: `logs/openai_usage.jsonl`

---

## Arquitectura técnica

### Componentes principales

```
data/raw/constitucion_chile/
  └─ Repo raw fuente (opensourcechile/constitucion_chile) con historial Git

src/cl_legal_rag/
  ├─ parser.py
  │  └─ Chunking por artículos y metadatos jurídicos
  ├─ history_extractor.py
  │  └─ Extracción incremental por commit (solo archivos/artículos modificados)
  ├─ database.py
  │  └─ Chroma local y retrieval
  ├─ embeddings.py
  │  └─ Cliente embeddings con batching defensivo y logging de uso
  ├─ openai_usage.py
  │  └─ Estimación de costos y escritura de eventos JSONL
  └─ config.py
     └─ Configuración centralizada

app/
  ├─ main.py
  │  └─ UI Streamlit + chat con control anti-alucinación
  │     Filtros históricos por ley y rango de fecha
  │     Control de alcance de contexto (top-k) configurable
  ├─ prompts/
  │  └─ system_prompt.md (prompt del sistema, desacoplado del código)
  ├─ styles/
  │  └─ main.css (estilos visuales)
  ├─ templates/
  │  └─ hero.html (bloque HTML de cabecera)
  └─ utils/
     └─ resources.py (loader centralizado de recursos)

scripts/
  ├─ ingest.py (ingesta vigente)
  ├─ ingest_history.py (ingesta histórica)
  └─ report_usage.py (resumen de costos)
```

### Decisiones de arquitectura ya tomadas

- **Dos colecciones vectoriales separadas:**
  - `current_constitution` (vigente)
  - `constitutional_history` (histórica)
- **Chunking por artículo** (no por fragmentos arbitrarios)
- **Indexación histórica incremental por commit** (solo archivos/artículos afectados)
- **Logging local JSONL** para auditoría de uso y costo

---

## Modelos y costos

### Configuración (en `src/cl_legal_rag/config.py`)

- **Embeddings:** `text-embedding-3-small`
- **Chat:** `gpt-4o-mini`

### Observabilidad

- `src/cl_legal_rag/openai_usage.py` registra tokens/costo estimado por request
- `scripts/report_usage.py` resume costo acumulado

### Estructura de logs (JSONL)

Cada evento en `logs/openai_usage.jsonl` contiene:
- `endpoint`, `model`
- metadatos de request
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `estimated_cost_usd`

---

## Start Here para agentes (5 min)

### Setup inicial

```bash
# 1. Sincronizar entorno
uv sync

# 2. Confirmar API key en .env
cat .env
# Debe contener: OPENAI_API_KEY=sk-...

# 3. Actualizar fuente raw (si corresponde)
git -C data/raw/constitucion_chile pull

# 4. Reingestar histórico
uv run python scripts/ingest_history.py

# 5. Levantar app
uv run streamlit run app/main.py

# 6. Revisar costo acumulado
uv run python scripts/report_usage.py
```

---

## Restricciones / No romper

⚠️ **Crítico:** Mantener estas garantías al hacer cambios:

- ❌ No eliminar trazabilidad de metadatos (`sha`, `ley`, `commit_date`, `source_file`)
- ❌ No mezclar colecciones vigente/histórica sin control de modo
- ❌ No desactivar logs de uso OpenAI
- ❌ No permitir respuestas fuera del contexto recuperado

---

## Instrucción obligatoria de salida del LLM

Cuando el agente responda en chat, toda respuesta debe comenzar con el prefijo exacto:

```
Mi estimado, 
```

**Crítico:** Si una futura sesión modifica prompts, esta instrucción debe permanecer activa en `app/prompts/system_prompt.md`.

---

## Troubleshooting

### Error: `max_tokens_per_request` en embeddings

**Solución:** Ya mitigado con batching en `src/cl_legal_rag/embeddings.py`. Si persiste, revisar configuración de batch size.

### Respuesta sin contexto suficiente

**Comportamiento esperado:** El sistema debe responder con mensaje explícito indicando falta de información oficial en la base de datos.

### La base vectorial no existe

```bash
uv run python scripts/ingest_history.py
```

---

## Prioridades sugeridas siguientes

1. ✅ Filtros históricos por rango de fecha/ley en UI (ya implementado)
2. ⏳ Evaluación automática (set de preguntas + exactitud de cita por artículo)
3. ⏳ Dashboard de costos en Streamlit (diario, por endpoint, por modelo)
4. ⏳ Tests unitarios para parser y extractor histórico

---

## Referencias rápidas

- **Config centralizada:** `src/cl_legal_rag/config.py`
- **Prompt del sistema:** `app/prompts/system_prompt.md`
- **Logs de uso:** `logs/openai_usage.jsonl`
- **Datos raw:** `data/raw/constitucion_chile/` (git subdir o clone)
- **Base vectorial:** `chroma_db/` (local, volátil)
