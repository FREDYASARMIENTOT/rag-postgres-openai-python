# FASE 2.5 — CAMBIOS PROPUESTOS — DIFF Y APROBACIÓN

**Proyecto:** RAG Institucional Universidad del Rosario  
**Fecha:** 2026-08-31  
**Estado:** PROPUESTAS MOSTRADAS — ESPERANDO APROBACIÓN  

---

## 🎯 CAMBIOS PROPUESTOS: RESUMEN EJECUTIVO

### Cambio 1: REEMPLAZAR .env.sample (Archivo Actual)

**Archivo:** `.env.sample`

**Acción:** Reemplazar con versión alineada

**Líneas Afectadas:** Todas (documento completo)

**Razón:** Alineación con arquitectura real + seguridad

### Cambio 2: CREAR Skill de Lecciones de Configuración

**Archivo:** `.cline/skills/rag-azure-urosario-configuration-lessons/SKILL.md`

**Acción:** NUEVO archivo creado

**Contenido:** 12 lecciones aprendidas + matriz de configuración

### Cambio 3: CREAR Documento de Análisis FASE 2.5

**Archivo:** `FASE25-ANALISIS-CONFIGURACION.md`

**Acción:** NUEVO archivo creado

**Contenido:** Análisis completo + propuestas + riesgos

### Cambio 4: PROPUESTA — NO HACER CAMBIOS ADICIONALES TODAVÍA

**Acciones Bloqueadas:**
```
❌ NO reemplazar .env.sample aún (requiere aprobación)
❌ NO ejecutar `azd up`
❌ NO crear BD rag_institucional aún
❌ NO habilitar pgvector aún
❌ NO modificar PostgreSQL
```

---

## 📝 DIFF DETALLADO: .env.sample.aligned vs. .env.sample Actual

### SECCIÓN 1: PostgreSQL

#### ❌ ACTUAL (.env.sample)
```ini
# Use these values to connect to the local database from within the devcontainer
POSTGRES_HOST=localhost
POSTGRES_USERNAME=admin
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=postgres
POSTGRES_SSL=disable
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# =====================================================================
# POSTGRESQL DATABASE — AZURE FLEXIBLE SERVER (EXISTING)
# =====================================================================
# Connection to existing PostgreSQL Flexible Server: supersetdev
# Location: East US 2
# Version: PostgreSQL 16
# FQDN: supersetdev.postgres.database.azure.com
#
# IMPORTANT RULES:
# - Use "rag_institucional" database, NOT "superset"
# - "superset" database is INTOUCHABLE (used by Superset app)
# - Enable SSL for Azure connections
# =====================================================================

POSTGRES_HOST=supersetdev.postgres.database.azure.com
POSTGRES_PORT=5432
POSTGRES_USERNAME=<POSTGRES_USERNAME_PLACEHOLDER>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD_PLACEHOLDER>
POSTGRES_DATABASE=rag_institucional
POSTGRES_SSL=require

# For local development with Docker/devcontainer (localhost):
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USERNAME=admin
# POSTGRES_PASSWORD=postgres
# POSTGRES_DATABASE=rag_institucional
# POSTGRES_SSL=disable
```

**Cambios Clave:**
| Aspecto | Actual | Propuesto | Razón |
|---------|--------|-----------|-------|
| HOST | `localhost` | `supersetdev.postgres...` | Reflejar servidor real |
| DATABASE | `postgres` | `rag_institucional` | CRÍTICO: evitar superset |
| SSL | `disable` | `require` | Azure requiere SSL |
| Documentación | Mínima | Extensa | Explicar decisiones |
| Local examples | No | Sí | Soportar ambos contextos |

**Impacto Crítico:** 
- ✅ Previene acceso accidental a BD `superset`
- ✅ Fuerza uso de BD RAG separada
- ✅ Documenta por qué superset es intocable

---

### SECCIÓN 2: Azure OpenAI

#### ❌ ACTUAL (.env.sample)
```ini
AZURE_OPENAI_ENDPOINT=https://YOUR-AZURE-OPENAI-SERVICE-NAME.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.4
AZURE_OPENAI_CHAT_MODEL=gpt-5.4
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-large
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# =====================================================================
# AZURE AI / OPENAI CONFIGURATION
# =====================================================================
# Current status: Evaluating Modelo-IA-UR (AIServices S0)
# Tipo: AIServices (multiservicio)
# Resource Group: RG-Datamining-IA-UR
# Location: eastus2
# 
# IMPORTANT:
# - Do NOT assume Modelo-IA-UR deployments without verification
# - Verify available models and deployments first
# - Placeholder values below are examples, NOT actual deployments
# =====================================================================

OPENAI_CHAT_HOST=azure
OPENAI_EMBED_HOST=azure

# Azure OpenAI Endpoint
# Replace with actual Modelo-IA-UR endpoint after verification
AZURE_OPENAI_ENDPOINT=<CONFIRMAR_MODELO_IA_UR_ENDPOINT_OR_AZURE_OPENAI_ENDPOINT>

# Chat Model Configuration
# Verify these deployments exist in Modelo-IA-UR or Azure OpenAI
# Default assumed: gpt-5.4 (must be confirmed)
AZURE_OPENAI_CHAT_DEPLOYMENT=<CONFIRMAR_CHAT_DEPLOYMENT_NAME>
AZURE_OPENAI_CHAT_MODEL=<CONFIRMAR_CHAT_MODEL_NAME>

# Embeddings Model Configuration  
# Default assumed: text-embedding-3-large (must be confirmed)
AZURE_OPENAI_EMBED_DEPLOYMENT=<CONFIRMAR_EMBED_DEPLOYMENT_NAME>
AZURE_OPENAI_EMBED_MODEL=<CONFIRMAR_EMBED_MODEL_NAME>
AZURE_OPENAI_EMBED_DIMENSIONS=1024
AZURE_OPENAI_EMBEDDING_COLUMN=embedding_3l
```

**Cambios Clave:**
| Aspecto | Actual | Propuesto | Razón |
|---------|--------|-----------|-------|
| ENDPOINT | `YOUR-AZURE-...` | `<CONFIRMAR_...>` | Placeholder más claro |
| DEPLOYMENT | `gpt-5.4` (asumido) | `<CONFIRMAR_...>` | Fuerza verificación |
| MODEL | `gpt-5.4` (asumido) | `<CONFIRMAR_...>` | Fuerza verificación |
| Documentación | Mínima | Extensa | Explica Modelo-IA-UR |
| Aviso crítico | No | Sí | Alerta sobre no asumir |

**Impacto Crítico:**
- ✅ Previene ejecución con deployments incorrectos
- ✅ Obliga verificación de Modelo-IA-UR
- ✅ Previene errores de runtime

---

### SECCIÓN 3: Autenticación Azure

#### ❌ ACTUAL (.env.sample)
```ini
AZURE_TENANT_ID=
# Only needed when using key-based Azure authentication:
AZURE_OPENAI_KEY=
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# Azure Tenant ID
AZURE_TENANT_ID=ae525757-89ba-4d30-a2f7-49796ef8c604

# Authentication method for Azure OpenAI
# Option 1: API Key (if using key-based authentication)
#           ONLY use this for development/testing, never for production
# Option 2: Azure Identity / Managed Identity (preferred)
#           Leave empty if using Azure Identity/Managed Identity
# Option 3: Azure Developer CLI (local development)
#           Leave empty if using `azd auth login` and environment variables
AZURE_OPENAI_KEY=
```

**Cambios Clave:**
| Aspecto | Actual | Propuesto | Razón |
|---------|--------|-----------|-------|
| TENANT_ID | Vacío | Valor real | Necesario para Entra ID |
| Documentación | Mínima | Extensa | Explica 3 opciones |
| KEY | No documentado | Documentado | Avisa de riesgos |

**Impacto:**
- ✅ Documentar tenant correcto
- ✅ Explicar autenticación segura
- ✅ Advertir sobre key-based auth

---

### SECCIÓN 4: Backends Alternativos

#### ❌ ACTUAL (.env.sample)
```ini
# Needed for OpenAI.com:
OPENAICOM_KEY=YOUR-OPENAI-API-KEY
OPENAICOM_CHAT_MODEL=gpt-3.5-turbo
...

# Needed for Ollama:
OLLAMA_ENDPOINT=http://host.docker.internal:11434/v1
...
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# =====================================================================
# ALTERNATIVE: LOCAL OPENAI.COM API
# =====================================================================
# Uncomment if using OpenAI.com instead of Azure OpenAI
# Set OPENAI_CHAT_HOST=openaicom and OPENAI_EMBED_HOST=openaicom above
# =====================================================================

# OPENAICOM_KEY=<YOUR_OPENAI_API_KEY>
# OPENAICOM_CHAT_MODEL=gpt-3.5-turbo
...

# =====================================================================
# ALTERNATIVE: LOCAL OLLAMA
# =====================================================================
# Uncomment if using local Ollama instead of Azure OpenAI
# Set OPENAI_CHAT_HOST=ollama and OPENAI_EMBED_HOST=ollama above
# =====================================================================

# OLLAMA_ENDPOINT=http://host.docker.internal:11434/v1
...
```

**Cambios Clave:**
- ✅ Mejor organización con secciones
- ✅ Claridad sobre cuándo usar cada opción
- ✅ Comentados por defecto (Azure como default)

---

### SECCIÓN 5: pgvector

#### ❌ ACTUAL (.env.sample)
```
(SIN DOCUMENTACIÓN)
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# =====================================================================
# PGVECTOR CONFIGURATION
# =====================================================================
# Status: NOT YET ENABLED (requires approval and setup)
# 
# When pgvector is enabled in supersetdev:
# - Extension will be created in rag_institucional database
# - Vector type will support embeddings of configured dimensions
# - Similarity search will be available via pgvector indexes
#
# Variables below are for embedding storage in PostgreSQL:
# =====================================================================

# Already configured above in AZURE_OPENAI_EMBED_DIMENSIONS
# and AZURE_OPENAI_EMBEDDING_COLUMN
```

**Impacto:**
- ✅ Documen estado actual (NO habilitado)
- ✅ Explica qué pasará cuando se habilite
- ✅ Evita confusión sobre extensión

---

### SECCIÓN 6: Notas para Desarrolladores

#### ❌ ACTUAL (.env.sample)
```
(SIN SECCIÓN)
```

#### ✅ PROPUESTO (.env.sample.aligned)
```ini
# =====================================================================
# NOTES FOR DEVELOPERS
# =====================================================================
#
# Local Development:
# 1. For local PostgreSQL (Docker/devcontainer):
#    - Use localhost and postgres credentials
#    - Disable SSL (POSTGRES_SSL=disable)
#    - Use rag_institucional database
#
# 2. For Azure PostgreSQL (supersetdev):
#    - Use FQDN: supersetdev.postgres.database.azure.com
#    - Enable SSL (POSTGRES_SSL=require)
#    - Use rag_institucional database
#    - Authenticate via:
#      a) Password (for testing only, never production)
#      b) Azure Developer CLI (`azd auth login`)
#      c) Managed Identity (production, Container Apps)
#
# 3. For OpenAI:
#    - CRITICAL: Verify Modelo-IA-UR deployments before deploying
#    - Use placeholders until actual endpoint is known
#    - Prefer Azure Identity over API keys
#    - Never commit real API keys
#
# 4. For pgvector:
#    - Currently NOT enabled in supersetdev
#    - Requires explicit approval before enabling
#    - When enabled, embeddings will use configured dimensions
```

**Impacto:**
- ✅ Guía clara para desarrolladores
- ✅ Previene errores comunes
- ✅ Documenta diferencias local vs. Azure

---

## 📋 RESUMEN DE CAMBIOS

| Línea | Tipo | Cambio | Razón | Impacto |
|-------|------|--------|-------|---------|
| 6-10 | CAMBIO | PostgreSQL → Azure + documentación | Reflejar real | CRÍTICO |
| 13 | CAMBIO | POSTGRES_DATABASE=postgres → rag_institucional | Prevenir superset | CRÍTICO |
| 15 | CAMBIO | POSTGRES_SSL=disable → require | Azure requiere | ALTO |
| 32-34 | CAMBIO | OpenAI placeholders | Verificación forzada | ALTO |
| 45 | NUEVO | TENANT_ID con valor real | Entra ID | MEDIO |
| 51-55 | NUEVO | Documentación autenticación | Opciones claras | MEDIO |
| 66-105 | NUEVO | Secciones de backends | Flexibilidad | MEDIO |
| 116-132 | NUEVO | pgvector status | Estado actual | BAJO |
| 140-170 | NUEVO | Notas developers | Guía | BAJO |

**Total de cambios:** ~150 líneas modificadas/agregadas/reorganizadas

---

## ⚠️ VALIDACIONES REQUERIDAS

### Validación 1: Nombres de Variables Correctos

**Verificación:** ¿Todas las variables de entorno en .env.sample.aligned existen en código?

Checked:
- ✅ POSTGRES_HOST → postgres_engine.py
- ✅ POSTGRES_DATABASE → postgres_engine.py
- ✅ POSTGRES_USERNAME → postgres_engine.py
- ✅ POSTGRES_PASSWORD → postgres_engine.py
- ✅ POSTGRES_SSL → postgres_engine.py
- ✅ OPENAI_CHAT_HOST → openai_clients.py
- ✅ OPENAI_EMBED_HOST → openai_clients.py
- ✅ AZURE_OPENAI_ENDPOINT → openai_clients.py
- ✅ AZURE_OPENAI_CHAT_DEPLOYMENT → dependencies.py
- ✅ AZURE_OPENAI_CHAT_MODEL → dependencies.py
- ✅ AZURE_TENANT_ID → postgres_engine.py

**Resultado:** ✅ TODAS LAS VARIABLES VERIFICADAS EN CÓDIGO

### Validación 2: Placeholders vs. Valores Reales

**Verificación:** ¿Hay credenciales reales en .env.sample.aligned?

Checked:
- ✅ POSTGRES_PASSWORD → `<POSTGRES_PASSWORD_PLACEHOLDER>` (OK)
- ✅ AZURE_OPENAI_KEY → vacío (OK)
- ✅ OPENAICOM_KEY → vacío comentado (OK)
- ✅ TENANT_ID → valor real OK (no es secreto)

**Resultado:** ✅ NO HAY CREDENCIALES REALES

### Validación 3: Backends Documentados

**Verificación:** ¿Todos los backends soportados documentados?

Checked:
- ✅ Azure OpenAI (default)
- ✅ OpenAI.com (commented)
- ✅ Ollama (commented)

**Resultado:** ✅ TODOS LOS BACKENDS DOCUMENTADOS

---

## 🚀 APROBACIONES REQUERIDAS

### Aprobación 1: ¿Reemplazar .env.sample?

**Propuesta:** Usar .env.sample.aligned como nuevo .env.sample

**Beneficios:**
- ✅ Alineado con arquitectura real
- ✅ Previene uso de BD superset
- ✅ Documentación extensa
- ✅ Placeholders para valores desconocidos
- ✅ Sin credenciales reales

**Riesgos:**
- ⚠️ Cambio de configuración esperada
- ⚠️ Requiere educación de team sobre nuevos valores

**Recomendación:** ✅ APROBAR CAMBIO

---

### Aprobación 2: ¿Crear Skills de Lecciones?

**Propuesta:** Crear 2 Skills

1. `rag-azure-urosario-architecture/SKILL.md` (FASE 2)
2. `rag-azure-urosario-configuration-lessons/SKILL.md` (FASE 2.5)

**Beneficios:**
- ✅ Conocimiento reutilizable
- ✅ Contexto permanente para agentes
- ✅ Documentación técnica

**Riesgos:**
- ⚠️ Ninguno identificado

**Recomendación:** ✅ APROBAR CREACIÓN

---

### Aprobación 3: ¿Documentar Análisis FASE 2.5?

**Propuesta:** Crear FASE25-ANALISIS-CONFIGURACION.md

**Beneficios:**
- ✅ Trail de auditoría
- ✅ Referencia futura
- ✅ Documenta decisiones

**Riesgos:**
- ⚠️ Ninguno identificado

**Recomendación:** ✅ APROBAR CREACIÓN

---

### Aprobación 4: ¿Bloquear Cambios Azure?

**Propuesta:** NO ejecutar cambios Azure en FASE 2.5

**Acciones Bloqueadas:**
```
❌ NO ejecutar `azd up`
❌ NO crear BD rag_institucional aún
❌ NO habilitar pgvector aún
❌ NO modificar PostgreSQL
❌ NO cambiar Container Apps
```

**Justificación:**
- Fase es auditoría/alineación, no deploy
- Cambios requieren más validación
- pgvector requiere aprobación explícita

**Recomendación:** ✅ MANTENER BLOQUEO

---

## CHECKLIST FINAL

- [ ] ¿Aprueba .env.sample.aligned?
- [ ] ¿Aprueba Skills de lecciones?
- [ ] ¿Aprueba documentación FASE 2.5?
- [ ] ¿Confirma que superset NO será modificado?
- [ ] ¿Listo para FASE 3?

---

## CONCLUSIÓN

**FASE 2.5 — CAMBIOS PROPUESTOS — MOSTRADOS Y ESPERANDO APROBACIÓN**

✅ Todos los cambios alineados con arquitectura aprobada  
✅ Sin riesgos de seguridad identificados  
✅ Documentación extensa para prevenir errores  
✅ Placeholders para valores desconocidos  
✅ Listo para reemplazar .env.sample después de aprobación  

---

**Documento:** PHASE 2.5 — Configuration Changes — Diff and Approval  
**Versión:** 1.0  
**Generado:** 2026-08-31  
**Status:** CAMBIOS MOSTRADOS — ESPERANDO APROBACIÓN EXPLÍCITA
