# Arquitectura del RAG Institucional — Universidad del Rosario

**Documento:** ARCHITECTURA-RAG.md  
**Versión:** 2.0 — Fase Foundry (Integración Foundry + Desacoplamiento)  
**Fecha:** 2026-01-09  
**Status:** ✅ ACTUALIZADO — Foundry + Contratos de Proveedor

---

## 1. RESUMEN EJECUTIVO

El **RAG Institucional** es un sistema de Retrieval Augmented Generation que permite
consultar documentos institucionales mediante lenguaje natural. Está alojado en Azure
y se integra con PostgreSQL (supersetdev) y Modelo-IA-UR (Azure AI Services).

### Arquitectura en capas

```
[Cliente HTTP]
    │
    ▼
[FastAPI — Configuración y Dependencias]
    │
    ├── [OpenAI Clients] ─────── Modelo-IA-UR / Azure OpenAI
    │
    ├── [Embeddings] ─────────── compute_text_embedding()
    │
    ├── [PostgresSearcher] ───── postgres_searcher.py
    │       ├── build_filter_clause() [SEGURIDAD: whitelists]
    │       ├── search() [vectorial, textual, híbrido]
    │       └── search_and_embed() [orquestación]
    │
    ├── [PostgreSQL + pgvector] ─ supersetdev / rag_institucional
    │
    └── [RAG Flows]
            ├── SimpleRAGChat
            └── AdvancedRAGChat
```

---

## 2. COMPONENTES

### 2.1 Configuración (`dependencies.py`)

Lee toda la configuración desde variables de entorno. Se construye una vez
por request HTTP y se inyecta via dependencias de FastAPI.

**Modelo de datos:** `FastAPIAppContext` (Pydantic)

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| openai_chat_host | Host backend para chat | `foundry`, `azure`, `openai` |
| openai_embed_host | Host backend para embeddings | `foundry`, `azure`, `openai` |
| openai_chat_model | Modelo para chat | `gpt-5.6-luna` |
| openai_embed_model | Modelo para embeddings | `text-embedding-3-large` |
| openai_embed_dimensions | Dimensiones del vector | `1024` |
| openai_chat_deployment | Deployment Azure/Foundry | `ur-rag-gpt-5-6-luna` |
| openai_embed_deployment | Deployment Foundry | `ur-rag-embedding-3-large` |
| embedding_column | Columna vectorial activa | `embedding_3l` |

### 2.1b Proveedores (`proveedores.py`)

Contratos abstractos que desacoplan la lógica de negocio de modelos concretos:

- **ProveedorLLM**: Contrato para clientes de chat. Propiedades: `cliente`, `modelo`, `deployment`.
- **ProveedorEmbeddings**: Contrato para clientes de embeddings. Propiedades: `cliente`, `modelo`, `deployment`, `dimensiones`.

Las implementaciones concretas (`ProveedorLLMBase`, `ProveedorEmbeddingsBase`) reciben el cliente y configuración ya resueltos desde `openai_clients.py`. La lógica de negocio NUNCA contiene nombres de modelos hardcodeados.

### 2.2 Embeddings (`embeddings.py`)

Función única `compute_text_embedding()` que:
- Toma texto, cliente OpenAI, modelo, deployment opcional y dimensiones.
- Valida si el modelo soporta el parámetro `dimensions`.
- Delega en la API de OpenAI/Azure OpenAI.
- Centraliza la decisión de deployment vs modelo.

---

## 3. FLUJO DE DATOS (REQUEST TÍPICO)

```
POST /chat/stream
  │
  ├─ 1. FastAPI inyecta dependencias (context, db_session, openai clients)
  │
  ├─ 2. Se crea PostgresSearcher con la configuración del request
  │
  ├─ 3. Se crea RAGFlow (Simple o Advanced según overrides)
  │     │
  │     ├─ 3a. prepare_context()
  │     │      ├─ query → compute_text_embedding() → vector
  │     │      ├─ vector + text → search() → [Item...]
  │     │      ├─ filters → build_filter_clause() [whitelist validada]
  │     │      └─ context → [docs, thoughts]
  │     │
  │     └─ 3b. answer() / answer_stream()
  │            ├─ prompt = template(user_query, context_docs)
  │            └─ chat_completion → response stream
  │
  └─ 4. Respuesta → cliente HTTP (streaming NDJSON)
```

---

## 4. SEGURIDAD

### 4.1 Inyección SQL

**Riesgo:** El agente LLM (AdvancedRAGChat) puede generar filtros con columnas,
operadores y valores controlados por el usuario.

**Mitigación:**
- Whitelist de columnas: `COLUMNAS_FILTRO_PERMITIDAS`.
- Whitelist de operadores: `OPERADORES_FILTRO_PERMITIDOS`.
- Escape de comillas simples en valores string.
- Filtros no válidos se omiten silenciosamente (no fallan).

**Riesgo residual:**
- `embedding_column` se interpola directamente en SQL (configuración administrativa, no controlada por el agente).

### 4.2 Autenticación

- Azure OpenAI: API Key o Azure Identity (preferido).
- PostgreSQL: Token Azure AD o contraseña.
- Managed Identity para producción (Container Apps).

### 4.3 Secretos

- Ningún secreto está hardcodeado en el código.
- Las claves de API se pasan por variables de entorno.
- Los scripts `setup_postgres_*` requieren confirmación explícita antes de ejecutar.

---

## 5. POSTGRESQL Y PGVECTOR

### 5.1 Arquitectura objetivo

```
supersetdev (PostgreSQL Flexible Server, East US 2, PG16)
    ├── superset           ← BD de Apache Superset (INTOCABLE)
    │   ├── tablas Superset
    │   ├── schemas Superset
    │   └── usuarios Superset
    │
    └── rag_institucional  ← BD del RAG (CREAR en Fase 4)
        ├── schema público
        ├── tabla items
        │   ├── datos textuales
        │   └── columnas vectoriales (pgvector)
        ├── índices HNSW
        └── usuario raguser
```

### 5.2 pgvector

**Estado actual (Fase 3):** NO habilitado en supersetdev.

**Validación implementada en el código:**
- `verify_pgvector_available()`: Detecta si pgvector está instalado en el servidor.
- `verify_pgvector_created()`: Detecta si está creado en la BD actual.
- `register_vector` en event listener: Advertencia graceful si no existe.

**Procedimiento de habilitación (Fase 4):**
```sql
CREATE DATABASE rag_institucional;
\c rag_institucional
CREATE EXTENSION vector;
```
**Modelos soportados:**
- `text-embedding-3-large` (1024 dimensiones, configurable)
- `text-embedding-3-small` (dimensiones configurables)
- `text-embedding-ada-002` (1536 fijas, sin `dimensions`)
- `nomic-embed-text` (768, sin `dimensions`)

### 2.3 Persistencia — PostgreSQL (`postgres_engine.py`)

Crea y gestiona el engine asíncrono SQLAlchemy.

**Autenticación:**
- **Azure Database for PostgreSQL:** Token de Azure AD (Managed Identity o AzureDeveloperCliCredential).
- **PostgreSQL local:** Contraseña directa.

**Validación pgvector:**
- `register_vector` se ejecuta al conectar (event listener).
- Si falla, se registra advertencia (no se bloquea la app).
- `verify_pgvector_available()`: consulta pg_available_extensions.
- `verify_pgvector_created()`: consulta pg_extension.
---

## 6. AZURE AI (Modelo-IA-UR)

### 6.1 Recurso confirmado

| Propiedad | Valor |
|-----------|-------|
| Nombre | Modelo-IA-UR |
| Tipo | AI Services (multiservicio) |
| SKU | S0 |
| Grupo | RG-Datamining-SII2.0-Dev |

### 6.2 Deployments

| Deployment | Modelo | Estado |
|------------|--------|--------|
| `ur-rag-gpt-5-6-luna` | `gpt-5.6-luna` | ✅ CREADO por `deploy-foundry-rag-institucional.ps1` |
| `sii-supervisor-gpt-4o-mini` | `gpt-4o-mini` | 🔄 LEGACY (Azure OpenAI) — PROTEGIDO |
| `ur-rag-embedding-3-large` | `text-embedding-3-large` | ✅ CREADO por `deploy-foundry-rag-institucional.ps1` |

### 6.3 Estado de Implementación

1. ✅ Deployments creados por `deploy-foundry-rag-institucional.ps1`.
2. ✅ `FOUNDRY_OPENAI_ENDPOINT` confirmado: `https://modelo-ia-ur.cognitiveservices.azure.com/`
3. ⏳ Validar dimensiones 1024 con benchmark de corpus real (pendiente).
4. ⏳ Verificar cuota del deployment `ur-rag-gpt-5-6-luna` para el RAG (pendiente).

---

## 7. MULTI-AGENTE

Actualmente la aplicación expone endpoints REST que cualquier agente puede consumir.
El diseño futuro prevé una capa RAG Service Layer compartida:

```
Agente A   Agente B   Agente C
    └────────┼────────┘
             ▼
      RAG Service Layer
        ┌────┴────┐
        ▼         ▼
  PostgreSQL    Azure AI
  + pgvector    (Modelo-IA-UR)
```

**Principios:**
- El RAG no debe conocer qué agente lo usa.
- La persistencia (PostgreSQL + pgvector) es compartida.
- Cada agente puede tener su propia configuración de retrieval/generación.

---

## 8. OBSERVABILIDAD

- Logger name: `ragapp`, nivel configurable.
- Application Insights no integrado (APPLICATIONINSIGHTS_CONNECTION_STRING vacío).
- No hay tracing de requests a OpenAI ni métricas de latencia.

---

## 9. COSTOS

| Recurso reutilizado | Costo/mes estimado |
|---------------------|--------------------|
| supersetdev (PG B1ms, 32GB) | ~$15 USD |
| Modelo-IA-UR (S0, según uso) | ~$10-30 USD |
| **Ahorro por reutilización** | **~$60-120 USD/mes** |

---

## 10. LÍMITES

- PostgreSQL: 32GB storage, B1ms burstable, pgvector no habilitado.
- Modelo-IA-UR: AI Services S0, rate limits ~10K TPM, embeddings no confirmado.
- Streaming: NDJSON, timeout depende de disponibilidad del modelo.

---

## 11. REFERENCIAS

- Código fuente: `src/backend/fastapi_app/`
- Tests: `src/backend/tests/`
- Infraestructura: `infra/`
- Lecciones aprendidas: `docs/decisiones/LESSONS-LEARNED.md`
- Decisión de embeddings: `docs/decisiones/DECISION-EMBEDDINGS.md`
- Integración Foundry: `docs/arquitectura/FOUNDRY-INTEGRATION.md`
- Skills del proyecto: `.cline/skills/`

---

**Documento:** ARCHITECTURA-RAG.md  
**Versión:** 1.0 | **Fecha:** 2026-01-09 | **Status:** ✅ ACTUALIZADO