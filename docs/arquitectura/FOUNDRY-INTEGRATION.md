# Integración con Microsoft Foundry — RAG Institucional

**Documento:** FOUNDRY-INTEGRATION.md  
**Versión:** 2.0 — Alineación con script de deployment  
**Fecha:** 2026-01-09  
**Status:** ✅ DOCUMENTADO — Deployments creados por PowerShell

---

## 1. Objetivo

Documentar la estructura de conexión a Microsoft Foundry (Azure AI Studio)
para el RAG Institucional, incluyendo:

- Reutilización del proyecto y recurso existentes.
- Autenticación con Entra ID / Managed Identity.
- Abstracción de ProveedorLLM y ProveedorEmbeddings para permitir
  cambio de proveedor sin modificar lógica de negocio.

---

## 2. Recursos Existentes (REUTILIZAR)

| Recurso | Nombre | Tipo |
|---------|--------|------|
| Proyecto Foundry | `Proyecto-IA-UR` | Azure AI Hub/Project |
| Recurso AI Services | `Modelo-IA-UR` | Cognitive Services (S0) |
| Grupo | `RG-Datamining-SII2.0-Dev` | Resource Group |
| Región | East US 2 | |

### 2.1 NO Crear

- ❌ NO crear nuevo proyecto Foundry.
- ❌ NO crear nuevo recurso Foundry.
- ❌ NO crear nuevo Azure OpenAI (a menos que Foundry no soporte embeddings).

---

## 3. Deployments

### 3.1 Chat — Creado por Script

| Propiedad | Valor |
|-----------|-------|
| Deployment | `ur-rag-gpt-5-6-luna` |
| Modelo | `gpt-5.6-luna` |
| Estado | ✅ CREADO por `deploy-foundry-rag-institucional.ps1` |
| Uso | LLM principal para RAG Institucional (sustituye `gpt-4o-mini`) |

### 3.2 Embeddings — Creado por Script

| Propiedad | Valor |
|-----------|-------|
| Deployment | `ur-rag-embedding-3-large` |
| Modelo | `text-embedding-3-large` |
| Dimensiones | 1024 (configurable vía `FOUNDRY_EMBEDDING_DIMENSIONS`) |
| Estado | ✅ CREADO por `deploy-foundry-rag-institucional.ps1` |

---

## 4. Arquitectura de Conexión

```
[FastAPI — proveedores.py]
    │
    ├── ProveedorLLM ───────────── Foundry (Modelo-IA-UR)
    │   └── OpenAI v1 endpoint (cognitiveservices.azure.com/openai/v1/)
    │
    └── ProveedorEmbeddings ────── Foundry (Modelo-IA-UR)
        └── OpenAI v1 endpoint (cognitiveservices.azure.com/openai/v1/)
```

### 4.1 Endpoint

Para ambos servicios se utiliza la **ruta OpenAI v1** del recurso Foundry
(Modelo-IA-UR). El endpoint tiene el formato:

```
https://<resource-name>.cognitiveservices.azure.com/openai/v1/
```

### 4.2 Diferencias con Azure OpenAI

| Aspecto | Azure OpenAI | Foundry (AI Services) |
|---------|-------------|----------------------|
| Recurso | Azure OpenAI Service | AI Services (multiservicio) |
| Endpoint | `{name}.openai.azure.com` | `{name}.cognitiveservices.azure.com` |
| Auth scope | `cognitiveservices.azure.com` | `cognitiveservices.azure.com` |
| Modelos | Solo OpenAI | OpenAI + otros |
| Deployments | vía Azure OpenAI Studio | vía Foundry (AI Studio) |

---

## 5. Autenticación

### 5.1 Entra ID (Managed Identity) — RECOMENDADO

```python
token_provider = azure.identity.aio.get_bearer_token_provider(
    azure_credential,
    "https://cognitiveservices.azure.com/.default",
)
```

### 5.2 API Key — Alternativa Local

```python
client = AsyncOpenAI(
    base_url="https://<endpoint>/openai/v1/",
    api_key="<key>",
)
```

### 5.3 Scopes

- **Cognitive Services** (OpenAI v1): `https://cognitiveservices.azure.com/.default`
- **Foundry/Machine Learning**: `https://ml.azure.com/.default` (reservado para futuro)

---

## 6. Proveedores (Contratos)

Ver `src/backend/fastapi_app/proveedores.py` para las implementaciones:

### ProveedorLLM

```python
class ProveedorLLM(ABC):
    @property
    def cliente(self) -> AsyncOpenAI: ...
    @property
    def modelo(self) -> str: ...
    @property
    def deployment(self) -> Optional[str]: ...
```

### ProveedorEmbeddings

```python
class ProveedorEmbeddings(ABC):
    @property
    def cliente(self) -> AsyncOpenAI: ...
    @property
    def modelo(self) -> str: ...
    @property
    def deployment(self) -> Optional[str]: ...
    @property
    def dimensiones(self) -> Optional[int]: ...
```

### Factory Functions

```python
def crear_proveedor_llm(cliente, modelo, deployment=None) -> ProveedorLLM: ...
def crear_proveedor_embeddings(cliente, modelo, deployment=None, dimensiones=None) -> ProveedorEmbeddings: ...
```

---

## 7. Configuración

```bash
# Host selector
OPENAI_CHAT_HOST=foundry
OPENAI_EMBED_HOST=foundry

# Foundry endpoint (OpenAI v1 route)
FOUNDRY_OPENAI_ENDPOINT=https://Modelo-IA-UR.cognitiveservices.azure.com

# Chat (creado por deploy-foundry-rag-institucional.ps1)
FOUNDRY_CHAT_DEPLOYMENT=ur-rag-gpt-5-6-luna
FOUNDRY_CHAT_MODEL=gpt-5.6-luna

# Embeddings (creado por deploy-foundry-rag-institucional.ps1)
FOUNDRY_EMBEDDING_DEPLOYMENT=ur-rag-embedding-3-large
FOUNDRY_EMBEDDING_MODEL=text-embedding-3-large
FOUNDRY_EMBEDDING_DIMENSIONS=1024
```

---

## 8. Migración desde Azure OpenAI (Legacy)

| Paso | Acción | Riesgo |
|------|--------|--------|
| 1 | Ejecutar `deploy-foundry-rag-institucional.ps1` | Bajo (idempotente) |
| 2 | Cambiar `OPENAI_CHAT_HOST=foundry`, `OPENAI_EMBED_HOST=foundry` | Bajo |
| 3 | Configurar `FOUNDRY_OPENAI_ENDPOINT` con endpoint real | Medio (si es incorrecto) |
| 4 | Iniciar aplicación (usa defaults `ur-rag-gpt-5-6-luna` / `ur-rag-embedding-3-large` / 1024d) | Bajo |
| 5 | Probar conexión con query simple | Medio |
| 6 | Verificar cuota del deployment `ur-rag-gpt-5-6-luna` | Alto (rate limits) |

---

## 9. Estado de Implementación

| Operación | Estado | Fecha |
|-----------|--------|-------|
| Ejecutar `deploy-foundry-rag-institucional.ps1` | ✅ COMPLETADO | 2026-01-09 |
| Obtener endpoint real del recurso Modelo-IA-UR | ✅ CONFIRMADO: `https://modelo-ia-ur.cognitiveservices.azure.com/` | 2026-01-09 |
| Deployment LLM: `ur-rag-gpt-5-6-luna` (gpt-5.6-luna) | ✅ CREADO — Succeeded | 2026-01-09 |
| Deployment Embeddings: `ur-rag-embedding-3-large` (text-embedding-3-large) | ✅ CREADO — Succeeded | 2026-01-09 |
| Legacy `sii-supervisor-gpt-4o-mini` verificado intacto | ✅ CONFIRMADO | 2026-01-09 |
| Verificar cuota y rate limits del deployment `ur-rag-gpt-5-6-luna` | ⏳ PENDIENTE (monitoreo continuo) | — |
| Ejecutar prueba de embedding con dimensión 1024 | ⏳ PENDIENTE (requiere conexión real a Foundry) | — |
| Validar dimensiones 1024 vs alternativas con corpus real | ⏳ PENDIENTE (benchmark con corpus real) | — |

---

## 10. Referencias

- [Contratos de proveedores](../../src/backend/fastapi_app/proveedores.py)
- [Clientes OpenAI](../../src/backend/fastapi_app/openai_clients.py)
- [Script de deployment](../../deploy-foundry-rag-institucional.ps1) — Crea los deployments Foundry para el RAG
- [Decisión de LLM Foundry](../decisiones/DECISION-LLM-FOUNDRY.md)
- [Decisión de Embeddings](../decisiones/DECISION-EMBEDDINGS.md)
- [Diseño Vectorial](DISEÑO-VECTORIAL-RAG.md)
- [Arquitectura del RAG](ARCHITECTURA-RAG.md)
- [Guía de reutilización Bicep](../operaciones/REUTILIZACION-BICEP.md)
- .env.sample (variables FOUNDRY_*)

---

**Documento:** FOUNDRY-INTEGRATION.md  
**Versión:** 1.0 | **Fecha:** 2026-01-09 | **Status:** ✅ DOCUMENTADO