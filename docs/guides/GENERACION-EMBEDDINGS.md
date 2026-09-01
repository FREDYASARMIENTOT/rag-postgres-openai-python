# Guía de Generación de Embeddings — RAG Institucional

**Documento:** GENERACION-EMBEDDINGS.md
**Versión:** 1.0 — Fase 4
**Fecha:** 2026-01-09
**Status:** ✅ DOCUMENTADO — Pendiente de ejecución

---

## Resumen

Esta guía describe el proceso completo para generar, validar y almacenar embeddings vectoriales para el RAG Institucional de la Universidad del Rosario.

---

## FASE 1: Preparar el Corpus

**Objetivo:** Obtener los documentos institucionales que serán indexados.

**Actividades:**
1. Identificar fuentes de datos institucionales
2. Extraer texto de cada fuente
3. Normalizar formato (UTF-8, sin formatos binarios)
4. Asignar identificador único a cada documento
5. Registrar origen, fecha y tipo de documento

**Herramientas sugeridas:** `python-docx`, `PyMuPDF` (fitz), `beautifulsoup4`, `pdfplumber`

---

## FASE 2: Normalizar Documentos

**Objetivo:** Limpiar y estandarizar el contenido textual.

**Actividades:**
1. Eliminar caracteres de control no imprimibles
2. Normalizar espacios (simples, no tabs/múltiples)
3. Estandarizar saltos de línea (LF en lugar de CRLF)
4. Eliminar marcadores de formato residual

**⚠️ No normalizar:** Mayúsculas de nombres propios, siglas institucionales, números de documentos oficiales.

---

## FASE 3: Eliminar Contenido No Útil

**Eliminar:** Encabezados/pies repetitivos, números de página, tablas de contenido, notas legales estándar, texto repetido.
**Conservar:** Citas, referencias bibliográficas, notas al pie relevantes, metadatos documentales.

---

## FASE 4: Dividir Documentos en Chunks

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Tamaño de chunk | 512 tokens | Suficiente para contexto institucional |
| Overlap | 128 tokens (25%) | Evita pérdida semántica |
| Estrategia | Semántica (por párrafo) + límite de tokens | Respeta estructura documental |

**Proceso recomendado:**
1. Dividir por párrafos (doble salto de línea)
2. Fusionar párrafos pequeños hasta ~256 tokens
3. Cortar párrafos grandes en segmentos de ~512 tokens
4. Mantener overlap de 128 tokens entre chunks consecutivos

---

## FASE 5: Conservar Metadatos

| Campo | Tipo | Obligatorio |
|-------|------|-------------|
| chunk_id | UUID | ✅ |
| documento_id | string | ✅ |
| chunk_index | int | ✅ |
| chunk_total | int | ✅ |
| documento_titulo | string | ✅ |
| documento_tipo | string | ✅ |
| documento_fecha | date | ❌ Opcional |
| documento_dependencia | string | ❌ Opcional |
| chunk_texto | string | ✅ |

---

## FASE 6: Generar Checksum

SHA-256 del texto normalizado del chunk. Almacenar en columna `checksum`. Regenerar embedding solo si el checksum cambió.

---

## FASE 7: Generar Embeddings

**Código existente:** `src/backend/fastapi_app/embeddings.py`

```python
MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES = {
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
}

async def compute_text_embedding(
    text: str, openai_client, model: str,
    deployment=None, dimensions=None,
) -> list[float]: ...
```

---

## FASE 8: Validar Dimensión

Todos los vectores en la misma columna deben tener la misma dimensión (configurada vía `AZURE_OPENAI_EMBED_DIMENSIONS`).

---

## FASE 9: Insertar en PostgreSQL

**Tabla:** `items` (definida en `postgres_models.py`)

**Columnas vectoriales disponibles:**
- `embedding_3l` (1024d) — text-embedding-3-large
- `embedding_nomic` (768d) — nomic-embed-text

**Scripts existentes:** `setup_postgres_database.py`, `setup_postgres_seeddata.py`, `update_embeddings.py`

---

## FASE 10: Crear/Validar Índice pgvector

**Recomendado:** HNSW

```sql
CREATE INDEX IF NOT EXISTS idx_items_embedding_3l_hnsw
ON items USING hnsw (embedding_3l vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

| Índice | Uso | Recomendación |
|--------|-----|---------------|
| HNSW (m=16, ef_construction=200) | Producción (>10K vectores) | ✅ |
| IVFFlat (lists=100) | Prototipos | Alternativa |

---

## FASE 11: Ejecutar Consultas de Prueba

Usar `PostgresSearcher.search()` del módulo `postgres_searcher.py` con queries de prueba representativas del dominio institucional.

---

## FASE 12: Evaluar Retrieval

**Métricas:** recall@k, precision@k, MRR, NDCG@k
**Dataset:** 50-100 queries de ejemplo con juicios de relevancia
**Comparación:** text-embedding-3-small (1024d) vs text-embedding-3-large (3072d)

---

## FASE 13: Registrar Modelo y Versión

```sql
ALTER TABLE items ADD COLUMN IF NOT EXISTS modelo_embedding VARCHAR(128);
ALTER TABLE items ADD COLUMN IF NOT EXISTS version_embedding VARCHAR(32);
ALTER TABLE items ADD COLUMN IF NOT EXISTS fecha_generacion_embedding TIMESTAMPTZ;
ALTER TABLE items ADD COLUMN IF NOT EXISTS dimension_embedding INTEGER;
```

---

## FASE 14: Permitir Reconstrucción de Embeddings

**Script:** `update_embeddings.py`

```bash
python -m fastapi_app.update_embeddings --all
python -m fastapi_app.update_embeddings --missing
python -m fastapi_app.update_embeddings --changed
```

Regenera embeddings solo para items sin embedding válido o con checksum desactualizado.

---

## Referencias

- [Decisión de Embeddings](../decisions/DECISION-EMBEDDINGS.md)
- [Arquitectura del RAG](../ARCHITECTURA-RAG.md)
- Código: `src/backend/fastapi_app/embeddings.py`, `postgres_models.py`, `update_embeddings.py`

---

## Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-01-09 | Creación inicial del documento