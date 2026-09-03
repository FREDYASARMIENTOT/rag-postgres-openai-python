# INFORME E2E — FASE G.1: Portal Local (React + FastAPI + PostgreSQL + Luna)

## A. Estado del Repositorio

| Ítem | Valor |
|---|---|
| **Rama** | `tesis-rag-institucional` |
| **Adelantado** | 3 commits ahead |
| **NO se hizo commit** | ✅ |
| **NO se hizo push** | ✅ |
| **NO se modificó infra** | ✅ |

## B. Backend FastAPI

| Ítem | Valor |
|---|---|
| **URL** | `http://localhost:8000` |
| **Puerto** | 8000 |
| **Estado** | ✅ CORRIENDO |
| **Log** | `src/backend/server.log` |

## C. Frontend React

| Ítem | Valor |
|---|---|
| **Vite dev** | `http://localhost:5173` |
| **FastAPI static** | `http://localhost:8000/poc/` |
| **Estado** | ✅ CORRIENDO |

## D. PDF de Prueba

| Ítem | Valor |
|---|---|
| **Archivo** | `facultades_ur_prueba.pdf` |
| **Tamaño** | 3,832 bytes |

## E. Upload / Ingesta

| Ítem | Valor |
|---|---|
| **Documento ID** | 11 |
| **Estado** | VIGENTE |
| **Fragmentos** | 2 |
| **Embeddings** | 2 (ambos VECTOR(3072)) |

## F. PostgreSQL (rag_institucional)

| Ítem | Valor |
|---|---|
| **Tabla documentos** | `rag.documentos` (ID 11) |
| **Tabla fragmentos** | `rag.fragmentos_documento` (IDs 23, 24) |
| **Dimensión vector** | VECTOR(3072) |
| **pgvector** | ✅ Habilitado |

## G. Retrieval

| Ítem | Valor |
|---|---|
| **Endpoint** | `POST /api/rag/consulta-con-generacion` |
| **Resultados** | 10 fragmentos |
| **PDF incluido** | ✅ (scores 0.2374 y 0.427) |

## H. Luna (Generación)

| Ítem | Valor |
|---|---|
| **Deployment** | `ur-rag-gpt-5-6-luna` |
| **Respuesta** | 8 facultades listadas correctamente |
| **Grounding** | ✅ Fundamentada en contexto |

## I. Fuentes Citadas

| Ítem | Valor |
|---|---|
| **Fragmentos devueltos** | ✅ `fragmentos[]` con `titulo`, `score`, `fuente` |

## J. Prueba Negativa

| Ítem | Valor |
|---|---|
| **Consulta** | `"Presupuesto UR para colonia en Marte?"` |
| **Alucinación** | ❌ **NINGUNA** |
| **Veredicto** | ✅ **PASS** |

## K. Duplicado

| Ítem | Valor |
|---|---|
| **Resultado** | `500` (`UniqueViolationError`) |
| **Manejo graceful** | ❌ No implementado |

## L. MCP

| Ítem | Valor |
|---|---|
| **Flujo** | React → FastAPI (sin MCP) |
| **Herramientas** | 4 disponibles |

## M. Tests

| Resultado | Cantidad |
|---|---|
| **PASS** | 94 ✅ |
| **FAIL** | 1 (pre-existente) |
| **SKIP** | 2 |

## N. Problemas Solucionados

1. **Static assets** → Montaje condicional en `frontend_routes.py`
2. **Lifespan state** → Asignación directa en `__init__.py`
3. **Variable bug** → `servicio_ingesta` corregido en `rag_routes.py`
4. **Duplicado** → Pendiente mejora en `servicio_ingesta.py`

## O. Conclusiones

1. **✅ E2E COMPLETO**: React → FastAPI → PostgreSQL → Luna
2. **✅ Ingestiona y fragmenta PDF**: 2 fragmentos VECTOR(3072)
3. **✅ Retrieval vectorial funcional**
4. **✅ Generación Luna fundamentada** — 0 alucinaciones
5. **⚠️ 1 test pre-existente falla**
6. **⚠️ Mejora pendiente**: Manejo graceful de duplicados

---

*Generado: 2026-02-09 | Rama: tesis-rag-institucional*