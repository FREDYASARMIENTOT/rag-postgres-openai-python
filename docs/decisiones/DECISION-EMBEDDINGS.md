# Decisión de Embeddings — RAG Institucional

**Documento:** DECISION-EMBEDDINGS.md
**Versión:** 2.0 — Fase Foundry (align con script deployment)
**Fecha:** 2026-01-09
**Status:** ✅ IMPLEMENTACIÓN COMPLETADA — Deployment verificado en Azure

---

## 1. Objetivo

Documentar y decidir qué modelo de embeddings utilizará el RAG Institucional de la Universidad del Rosario, con criterios verificables y trazables.

## 2. Requisitos del RAG

| Requisito | Detalle |
|-----------|---------|
| Idioma principal | Español (90%+ del corpus institucional) |
| Idiomas secundarios | Inglés, posiblemente portugués/francés |
| Tipo de contenido | Documentos administrativos, académicos, normativos |
| Longitud de chunks | 512-1024 tokens (estimado) |
| Volumen estimado | Miles a decenas de miles de documentos |
| Latencia objetivo | < 2s por consulta de retrieval |
| Precisión mínima | Recall@10 > 0.80 en queries de prueba |

## 3. Modelos Candidatos

### 3.1 text-embedding-3-large (Foundry) — SELECCIONADO

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Foundry (Modelo-IA-UR) |
| Dimensiones | 256, 512, 1024, 3072 (configurable vía `dimensions`) |
| Dimensión elegida | **1024** (balance calidad/rendimiento/costo) |
| Costo | Medio ($0.13/1K tokens input) |
| Latencia | Moderado |
| Multilingüe | ✅ Sí (entrenado multilingüe) |
| Deployment | `ur-rag-embedding-3-large` (creado por script) |
| Decisión | **✅ DECISIÓN FINAL** |

### 3.2 text-embedding-3-small (alternativa)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI |
| Dimensiones | 512, 256, 1536 (configurable vía `dimensions`) |
| Costo | Bajo ($0.02/1K tokens input) |
| Latencia | Rápido |
| Multilingüe | ✅ Sí (entrenado multilingüe) |
| Disponible en | Azure OpenAI, OpenAI API |
| Recomendación | Alternativa de menor costo si el benchmark lo permite |

### 3.3 text-embedding-ada-002 (OpenAI legacy)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI |
| Dimensiones | 1536 (fijas, no configurables) |
| Costo | Medio |
| Latencia | Moderado |
| Multilingüe | ✅ Sí |
| Disponible en | Azure OpenAI |
| Recomendación | ❌ No recomendado (deprecado, sin reducción dimensional) |

### 3.4 Nomic Embed Text (open-source)

| Atributo | Valor |
|----------|-------|
| Proveedor | Nomic / open-source |
| Dimensiones | 768 (fijas) |
| Costo | 0 (self-hosted) o vía Nomic API |
| Latencia | Variable según hosting |
| Multilingüe | Parcial |
| Disponible en | Self-hosted o API externa |
| Recomendación | Alternativa open-source si presupuesto es crítico |

## 4. Análisis Comparativo

| Criterio | text-embedding-3-small | text-embedding-3-large | ada-002 | Nomic |
|----------|----------------------|----------------------|---------|-------|
| Dimensiones máximas | 1536 | 3072 | 1536 | 768 |
| Costo/1K tokens | $0.02 | $0.13 | $0.10 | $0 (self) |
| Calidad retrieval | Alta | Muy alta | Alta | Alta |
| Disponibilidad Foundry | ❌ No creado | ✅ `ur-rag-embedding-3-large` | ❌ No | ❌ No |
| Reducción dimensional | ✅ Sí (dimensions param) | ✅ Sí (dimensions param) | ❌ No | ❌ No |
| Multilingüe | ✅ Sí | ✅ Sí | ✅ Sí | Parcial |
| Maturity API v1 | ✅ Sí | ✅ Sí | ✅ Sí | Media |

## 5. Costos Estimados

Suponiendo 1M tokens de input/mes para embeddings:

| Modelo | Costo/mes |
|--------|-----------|
| text-embedding-3-small | ~$20 USD |
| text-embedding-3-large | ~$130 USD |
| Ada-002 | ~$100 USD |
| Nomic (self-hosted) | Costo infraestructura |

## 6. Impacto en pgvector

| Dimensión | Tamaño por vector (float32) | Index HNSW | Performance relativa |
|-----------|---------------------------|------------|---------------------|
| 768 | 3 KB | Rápido | Referencia |
| 1024 | 4 KB | Moderado | ~10% más lento |
| 1536 | 6 KB | Lento | ~25% más lento |
| 3072 | 12 KB | Muy lento | ~60% más lento |

## 7. Decisión

**DECISIÓN: text-embedding-3-large con 1024 dimensiones en Foundry**

Justificación:
1. **Dedicado** — Deployment `ur-rag-embedding-3-large` creado específicamente
   para el RAG, sin compartir cuota.
2. **Dimensión 1024** — Balance entre calidad de retrieval y rendimiento
   pgvector (4 KB por vector, ~10% más lento que 768d).
3. **Calidad superior** — text-embedding-3-large ofrece la mejor calidad
   de embeddings de OpenAI, relevante para corpus institucional en español.
4. **Desplegado por script** — `deploy-foundry-rag-institucional.ps1` crea
   el deployment automáticamente.
5. **Flexibilidad** — Migrar a 1536 o 3072 dimensiones solo requiere cambiar
   `FOUNDRY_EMBEDDING_DIMENSIONS` y regenerar embeddings.

**⚠️ VALIDACIÓN PENDIENTE:**
1. Ejecutar benchmark con corpus institucional real.
2. Evaluar recall@10 con queries típicas del dominio.
3. Medir latencia real en supersetdev.

## 8. Criterios para Cambiar de Dimensión o Modelo

| Criterio | Acción |
|----------|--------|
| Recall@10 < 0.80 con 1024d | Probar 1536d o 3072d |
| Costo de embeddings > $50/mes | Considerar text-embedding-3-small |
| Latencia pgvector > 2s por query | Reducir a 768d o indexar HNSW |

## 9. Estado Actual

| Elemento | Estado |
|----------|--------|
| Deployment `ur-rag-embedding-3-large` en Foundry | ✅ CREADO — Succeeded (2026-01-09) |
| text-embedding-3-large en Foundry | ✅ CONFIGURADO (default en `dependencies.py`) |
| Endpoint Foundry confirmado | ✅ `https://modelo-ia-ur.cognitiveservices.azure.com/` |
| Benchmark con corpus real | ❌ NO REALIZADO (pendiente) |
| Dimensión configurada | 1024 (vía `FOUNDRY_EMBEDDING_DIMENSIONS`) |
| Dimensión alternativa | 1536 (si el benchmark lo recomienda) |
| Columna vectorial actual | `embedding_3l` (configurable) |
| Contrato de embeddings | `ProveedorEmbeddings` en `proveedores.py` |
| Legacy `sii-supervisor-gpt-4o-mini` intacto | ✅ CONFIRMADO |

## 10. Referencias

- [Guía de generación de embeddings](../desarrollo/GENERACION-EMBEDDINGS.md)
- [Arquitectura del RAG](../arquitectura/ARCHITECTURA-RAG.md)
- [Integración Foundry](../arquitectura/FOUNDRY-INTEGRATION.md)
- [Diseño Vectorial](../arquitectura/DISEÑO-VECTORIAL-RAG.md)
- [Decisión de LLM Foundry](DECISION-LLM-FOUNDRY.md)
- Código: `src/backend/fastapi_app/embeddings.py`
- Código: `src/backend/fastapi_app/proveedores.py`
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [pgvector documentation](https://github.com/pgvector/pgvector)