# Decisión de Embeddings — RAG Institucional

**Documento:** DECISION-EMBEDDINGS.md
**Versión:** 1.0 — Fase 4 (Análisis)
**Fecha:** 2026-01-09
**Status:** ⏳ RECOMENDACIÓN INICIAL — SUJETA A VALIDACIÓN DEL CORPUS

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

### 3.1 text-embedding-3-small (Azure OpenAI)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI |
| Dimensiones | 512, 256, 1536 (configurable vía `dimensions`) |
| Costo | Bajo ($0.02/1K tokens input) |
| Latencia | Rápido |
| Multilingüe | ✅ Sí (entrenado multilingüe) |
| Disponible en | Azure OpenAI, OpenAI API |
| Recomendación | **RECOMENDACIÓN INICIAL** |

### 3.2 text-embedding-3-large (Azure OpenAI)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI |
| Dimensiones | 256, 512, 1024, 3072 (configurable vía `dimensions`) |
| Costo | Alto ($0.13/1K tokens input) |
| Latencia | Moderado |
| Multilingüe | ✅ Sí (entrenado multilingüe) |
| Disponible en | Azure OpenAI, OpenAI API |
| Recomendación | Alternativa si small no es suficiente |

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
| Disponibilidad Azure | ✅ Global Standard | ✅ Global Standard | ✅ Legacy | ❌ No |
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

## 7. Decisión Provisional

**RECOMENDACIÓN INICIAL: text-embedding-3-small con 1024 dimensiones**

Justificación:
1. **Costo**: 6.5x más barato que text-embedding-3-large
2. **Dimensión configurable**: Permite 1024 dimensiones, balance entre calidad y rendimiento
3. **Calidad suficiente**: Para corpus institucional en español, la calidad es comparable a large en benchmarks MTEB
4. **Disponibilidad**: Disponible como Global Standard en Azure OpenAI
5. **Flexibilidad**: Si se requiere mayor calidad, migrar a 3-large cambiando solo el deployment name

**⚠️ ESTA RECOMENDACIÓN DEBE VALIDARSE CON:**

1. Un benchmark real contra documento institucional de prueba
2. Evaluación de recall@10 con queries típicas del dominio
3. Medición de latencia real en supersetdev

## 8. Criterios para Cambiar de Modelo

| Criterio | Acción |
|----------|--------|
| Recall@10 < 0.75 con text-embedding-3-small | Probar text-embedding-3-large (3072d) |
| Costo de embeddings > $50/mes | Optimizar chunks o reducir dimensión |
| El deployment no está disponible en Modelo-IA-UR | Crear recurso Azure OpenAI dedicado |
| El deployment está disponible en Modelo-IA-UR | Usar directamente |

## 9. Estado Actual

| Elemento | Estado |
|----------|--------|
| Deployment text-embedding-3-large en Modelo-IA-UR | ⏳ PENDIENTE DE VALIDACIÓN |
| Deployment text-embedding-3-small en Modelo-IA-UR | ⏳ PENDIENTE DE VALIDACIÓN |
| Benchmark con corpus real | ❌ NO REALIZADO |
| Dimensión definitiva | ⏳ PENDIENTE (propuesta: 1024) |
| Columna vectorial actual | `embedding_3l` (1024d) + `embedding_nomic` (768d) |
| Contrato de embeddings | Definido en `embeddings.py` (MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES) |

## 10. Referencias

- [Guía de generación de embeddings](../guides/GENERACION-EMBEDDINGS.md)
- [Arquitectura del RAG](../ARCHITECTURA-RAG.md)
- Código: `src/backend/fastapi_app/embeddings.py`
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [pgvector documentation](https://github.com/pgvector/pgvector)