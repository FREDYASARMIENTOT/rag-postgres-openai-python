# RAG Institucional — Configuration & Lessons Learned Skill

**Status:** Skill reutilizable — Lecciones de Configuración  
**Versión:** 2.1  
**Fecha:** 2026-01-09  
**Proyecto:** RAG Institucional UR  
**Rama:** tesis-rag-institucional  

> **⚠️ ACTUALIZACIÓN 2026-01-09:** Deployment names confirmados tras auditoría Foundry.
> Dimensiones reales de embedding: 3072 (NO 1024).
> Ver [rag-azure-foundry-urosario](../rag-azure-foundry-urosario/SKILL.md) para detalles Foundry.  

---

## 🧩 ESTADO DE FASE 3.2 — Refactorización Completada

**Commit:** `bcb5641` (2026-09-01)

**Resumen de cambios en configuración:**
- `.env.sample` actualizado: valores confirmados, documentación de tareas pendientes
- `.env.sample.aligned` eliminado (consolidado en `.env.sample`)
- Validación de embeddings: `MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES` en `embeddings.py`
- SQL Security: whitelists implementadas en `postgres_searcher.py`
- Tests: 38 unit tests + 2 azure con marcadores `--run-azure`

**Próximos pasos de configuración (Fase 4/5 — 2026-01-09):**
- ~~Migrar a variables Foundry~~ → ✅ NUEVAS variables definidas, deployment names confirmados
- ~~Confirmar deployment de embeddings~~ → ✅ CONFIRMADO: `ur-rag-embedding-3-large` (3072d, dimensions no soportado)
- ~~Confirmar deployment de chat~~ → ✅ CONFIRMADO: `sii-supervisor-gpt-4o-mini` + `ur-rag-gpt-5-6-luna`
- ~~Confirmar `AZURE_OPENAI_EMBED_DIMENSIONS=1024`~~ → ❌ DIMENSIÓN REAL = 3072 (ver skill Foundry)
- Habilitar pgvector en supersetdev (PENDIENTE)
- Crear BD rag_institucional (PENDIENTE)

---

## 📋 LECCIONES APRENDIDAS — CONFIGURACIÓN

### 1. POSTGRESQL DATABASE — Seleccionar la BD Correcta

**Lección aprendida en auditoría:**

El repositorio original (.env.sample) usaba:
```
POSTGRES_DATABASE=postgres
POSTGRES_HOST=localhost
```

**Esto es INCORRECTO para la arquitectura objetivo.**

**Arquitectura real:**
```
Servidor: supersetdev.postgres.database.azure.com
BD principal (INTOCABLE): superset
BD RAG (NUEVA): rag_institucional
```

**Regla de Oro:**
```
NUNCA usar POSTGRES_DATABASE=superset (pertenece a Superset)
NUNCA usar POSTGRES_DATABASE=postgres (administración, riesgoso)
SIEMPRE usar POSTGRES_DATABASE=rag_institucional (RAG exclusivamente)
```

**Por qué importa:**
- BD `superset` contiene esquemas y datos de Superset (producción)
- Modificar `superset` rompe Superset existente
- `rag_institucional` es BD nueva, independiente, exclusiva del RAG
- Separación de BD = seguridad + aislamiento

---

### 2. POSTGRES_HOST — Local vs. Azure

**Lección aprendida:**

Código Python DETECTA AUTOMÁTICAMENTE si es Azure:
```python
if host.endswith(".database.azure.com"):
    token_based_password = True
    # Use Azure Identity
else:
    # Use password authentication
```

**Configuración Local (Docker/devcontainer):**
```
POSTGRES_HOST=localhost
POSTGRES_SSL=disable
POSTGRES_PASSWORD=postgres
```

**Configuración Azure (Producción):**
```
POSTGRES_HOST=supersetdev.postgres.database.azure.com
POSTGRES_SSL=require
POSTGRES_PASSWORD=<token_or_password>
```

**Decisión arquitectónica:**
- Código es FLEXIBLE (soporta ambas)
- Azure PostgreSQL requiere SSL
- Autenticación puede ser password o Azure Identity
- Código maneja ambas automáticamente

---

### 3. AUTENTICACIÓN POSTGRESQL — Tres Opciones

**Lección aprendida inspeccionando código:**

El código soporta 3 mecanismos:

#### Opción A: Password Authentication (dev/testing)
```python
password = password  # Usar POSTGRES_PASSWORD
```

Uso:
```
POSTGRES_PASSWORD=<actual_password>
```

⚠️ **NUNCA usar en producción.** Contraseñas en Git = comprometimiento.

#### Opción B: Azure Developer CLI (local dev)
```python
azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
```

Uso:
```
POSTGRES_PASSWORD=  (dejar vacío)
AZURE_TENANT_ID=ae525757-89ba-4d30-a2f7-49796ef8c604
# Ejecutar: azd auth login
```

✅ **Recomendado para desarrollo local.**

#### Opción C: Managed Identity (producción en Container Apps)
```python
azure_credential = ManagedIdentityCredential()
```

Uso:
```
POSTGRES_PASSWORD=  (dejar vacío)
# Container App asume Managed Identity
```

✅ **Recomendado para producción.**

**Regla:**
- ❌ NUNCA commitar passwords reales en .env
- ✅ USAR placeholders o variables vacías
- ✅ USAR Azure Identity cuando sea posible
- ✅ USAR Key Vault o secretos para valores reales

---

### 4. AZURE OPENAI CONFIGURATION — Verificar Antes de Asumir

**Lección aprendida en auditoría:**

El .env.sample original contenía:
```
AZURE_OPENAI_CHAT_MODEL=gpt-5.4
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-large
```

**PROBLEMA:** Estos valores pueden NO existir en Modelo-IA-UR.

**Descubrimiento de auditoría:**
- Modelo-IA-UR es AIServices (multiservicio), NO Azure OpenAI específico
- NO se conoce qué deployments existen realmente
- NO se puede ASUMIR gpt-5.4 o text-embedding-3-large

**Regla:**
```
❌ NO usar valores de deployment sin verificación
✅ USAR placeholders hasta confirmar
✅ VERIFICAR endpoint, modelos, deployments en Modelo-IA-UR
✅ DOCUMENTAR decisión de OpenAI/Modelo-IA-UR
```

**Configuración Segura (Proposed .env.sample.aligned):**
```
AZURE_OPENAI_ENDPOINT=<CONFIRMAR_MODELO_IA_UR_ENDPOINT>
AZURE_OPENAI_CHAT_DEPLOYMENT=<CONFIRMAR_CHAT_DEPLOYMENT_NAME>
AZURE_OPENAI_CHAT_MODEL=<CONFIRMAR_CHAT_MODEL_NAME>
AZURE_OPENAI_EMBED_DEPLOYMENT=<CONFIRMAR_EMBED_DEPLOYMENT_NAME>
AZURE_OPENAI_EMBED_MODEL=<CONFIRMAR_EMBED_MODEL_NAME>
```

**Ventajas:**
- Imposible ejecutar accidentalmente con valores incorrectos
- Obliga verificación manual antes de usar
- Documentación clara de qué se debe confirmar
- Previene errores de deployments no existentes

---

### 5. POSTGRESQL SSL — Requerido para Azure

**Lección aprendida:**

Local PostgreSQL (localhost):
```
POSTGRES_SSL=disable
```

Azure PostgreSQL Flexible Server:
```
POSTGRES_SSL=require
```

**Por qué:**
- Azure requiere conexiones cifradas
- PostgreSQL local (Docker) puede ser inseguro
- Código maneja ambos modos automáticamente

**Regla:**
```
Si POSTGRES_HOST contiene ".database.azure.com"
  ENTONCES POSTGRES_SSL=require
SINO
  POSTGRES_SSL=disable (desarrollo local)
```

---

### 6. NO HARDCODEAR CREDENCIALES EN .env.sample

**Lección aprendida:**

El .env.sample debe ser un TEMPLATE, NO una configuración real.

**INCORRECTO (nunca hacer esto):**
```
AZURE_OPENAI_KEY=sk-proj-xxxxxxxxxxxx
POSTGRES_PASSWORD=SuperSecretPassword123
```

**CORRECTO:**
```
AZURE_OPENAI_KEY=<PLACEHOLDER_OR_EMPTY>
POSTGRES_PASSWORD=<PLACEHOLDER_OR_EMPTY>
```

**O mejor aún:**
```
AZURE_OPENAI_KEY=  # Leave empty if using Azure Identity
POSTGRES_PASSWORD=  # Leave empty if using Azure Identity
```

**Por qué:**
- .env.sample está en Git
- Cualquiera puede ver los credenciales
- Compromete seguridad completamente
- Violencia de políticas de seguridad cloud

**Regla de Oro:**
```
.env.sample = TEMPLATE SIN VALORES REALES
.env (local) = archivo real, NO commitar
Azure Key Vault = valores reales en producción
CI/CD secrets = valores reales en deployment
```

---

### 7. PGVECTOR — NO ASUMIR QUE ESTÁ HABILITADO

**Lección aprendida:**

El código intenta:
```python
dbapi_connection.run_async(register_vector)
```

Con error handler:
```python
except ValueError:
    logger.warning("Could not register pgvector... vector extension has not been CREATEd")
```

**Hallazgo de auditoría:**
```
azure.extensions = ""  (VACÍO)
pgvector NO está habilitado en supersetdev
```

**Por qué importa:**
- Código espera pgvector pero aún no existe
- SQL `CREATE TABLE ... (embedding vector(1024))` fallará
- Aplicación será quebrada sin pgvector
- Requiere habilitación explícita + validación

**Regla:**
```
❌ NO asumir que pgvector está disponible
✅ VERIFICAR azure.extensions = "pg_cron,pg_stat_statements,vector"
✅ VALIDAR que `CREATE EXTENSION vector;` funciona
✅ HABILITAR solo con aprobación explícita
✅ DOCUMENTAR plan de rollback antes de habilitar
```

---

### 8. VARIABLES DE ENTORNO — Soportar Múltiples Backends

**Lección aprendida inspeccionando código:**

El código soporta múltiples backends:

```
OPENAI_CHAT_HOST = azure | openaicom | ollama
OPENAI_EMBED_HOST = azure | openaicom | ollama
```

**Para Azure:**
```
OPENAI_CHAT_HOST=azure
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_CHAT_DEPLOYMENT=...
```

**Para OpenAI.com:**
```
OPENAI_CHAT_HOST=openaicom
OPENAICOM_KEY=...
OPENAICOM_CHAT_MODEL=...
```

**Para Ollama (local):**
```
OPENAI_CHAT_HOST=ollama
OLLAMA_ENDPOINT=...
OLLAMA_CHAT_MODEL=...
```

**Regla:**
```
.env.sample debe documentar TODOS los backends
Pero SOLO activar uno por configuración
Comentar opciones alternativas
```

---

### 9. PARAMETRIZADAS CON DEFAULTS — No Requerir Todo

**Lección aprendida:**

Código usa pattern:
```python
openai_embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL") or "text-embedding-3-large"
openai_embed_dimensions = int(os.getenv("AZURE_OPENAI_EMBED_DIMENSIONS") or 1024)
```

**Significa:**
- Si variable no está en .env, usa default
- Algunos valores son opcionales
- .env.sample puede tener valores vacíos

**Ejemplo correcto:**
```
# Si no está presente, código asume "text-embedding-3-large"
# Si no está presente, código asume 1024
AZURE_OPENAI_EMBED_DIMENSIONS=1024
AZURE_OPENAI_EMBEDDING_COLUMN=embedding_3l
```

**Regla:**
```
.env.sample debe mostrar valores típicos
Pero comentar cuáles son realmente requeridos
Documentar qué defaults aplica el código
```

---

### 10. TENANT ID — Necesario para Azure Identity

**Lección aprendida:**

Código setup PostgreSQL:
```python
azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
```

Para Azure PostgreSQL Flexible Server con Entra ID.

**Tenant ID de UR:**
```
ae525757-89ba-4d30-a2f7-49796ef8c604
```

**Regla:**
```
✅ Tenant ID es necesario para autenticación Entra ID
✅ Debe estar en .env cuando usando Azure Identity
✅ NO es secreto (es información pública)
✅ Documentar cuál es el tenant ID correcto
```

---

### 11. DOCUMENTACIÓN EN .env.sample — Crítica

**Lección aprendida:**

.env.sample DEBE:
- ✅ Documentar por qué cada variable existe
- ✅ Indicar si es requerida u opcional
- ✅ Mostrar ejemplos para cada backend
- ✅ Advertir sobre no guardar credenciales
- ✅ Documentar diferencias local vs. Azure
- ✅ Incluir notas sobre configuración segura

**.env.sample MAL:**
```
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=postgres
```

**.env.sample BIEN:**
```
# PostgreSQL EXISTING AZURE FLEXIBLE SERVER
# Servidor: supersetdev.postgres.database.azure.com
# Base: rag_institucional (SEPARADA de superset)
POSTGRES_HOST=supersetdev.postgres.database.azure.com
POSTGRES_PASSWORD=  # Use Azure Identity, not password
```

**Regla:**
```
Documentar AMPLIAMENTE en .env.sample
Explicar PORQUÉ y no solo QUE
Incluir ejemplos para diferentes escenarios
Advertir sobre seguridad y production
```

---

### 12. ACTUALIZAR .env.sample CUANDO CAMBIA ARQUITECTURA

**Lección crítica para futuro:**

El .env.sample original estaba diseñado para:
- PostgreSQL local
- Azure OpenAI (con contraseña)
- Desarrollo local

**Pero la arquitectura REAL es:**
- PostgreSQL Azure (supersetdev)
- BD rag_institucional (separada)
- Modelo-IA-UR (AIServices, no OpenAI específico)
- Producción en Container Apps

**Regla:**
```
SIEMPRE alinear .env.sample con arquitectura real
NUNCA dejar plantillas obsoletas en repositorio
DOCUMENTAR cambios de configuración cuando cambia arquitectura
TESTEAR .env.sample localmente antes de commitar
```

---

## 📊 MATRIZ DE CONFIGURACIÓN

| Variable | Requerida | Local | Azure | Placeholder | Notas |
|----------|-----------|-------|-------|-------------|-------|
| POSTGRES_HOST | ✅ | localhost | supersetdev.postgres... | N/A | Detecta automáticamente si es Azure |
| POSTGRES_DATABASE | ✅ | rag_institucional | rag_institucional | ✅ | NUNCA usar "superset" |
| POSTGRES_PASSWORD | ⚠️ | postgres | (empty si Azure Identity) | ✅ | Preferir Azure Identity |
| POSTGRES_SSL | ✅ | disable | require | N/A | Azure requiere SSL |
| AZURE_OPENAI_ENDPOINT | ⚠️ | N/A | https://modelo-ia-ur... | ✅ | VERIFICAR antes de usar |
| AZURE_OPENAI_CHAT_DEPLOYMENT | ⚠️ | N/A | sii-supervisor-gpt-4o-mini | ✅ | También ur-rag-gpt-5-6-luna disponible |
| AZURE_OPENAI_CHAT_MODEL | ⚠️ | N/A | gpt-4o-mini | ✅ | O gpt-5.6-luna para ur-rag-gpt-5-6-luna |
| AZURE_OPENAI_EMBED_DEPLOYMENT | ⚠️ | N/A | ur-rag-embedding-3-large | ✅ | CONFIRMADO en Modelo-IA-UR |
| AZURE_OPENAI_EMBED_MODEL | ⚠️ | N/A | text-embedding-3-large | ✅ | Modelo subyacente al deployment |
| AZURE_OPENAI_EMBED_DIMENSIONS | ⚠️ | N/A | ⚠️ VER NOTA | ✅ | ⚠️ 1024 NO SOPORTADO. Real: 3072 sin dimensions |
| AZURE_OPENAI_KEY | ❌ | N/A | (empty) | ✅ | Preferir Azure Identity |
| AZURE_TENANT_ID | ⚠️ | N/A | ae525757... | N/A | Necesario para Entra ID |

---

## ✅ CHECKLIST: CONFIGURACIÓN ALINEADA

- [ ] ✅ .env.sample apunta a rag_institucional, NO superset
- [ ] ✅ .env.sample documenta múltiples backends (Azure, OpenAI, Ollama)
- [ ] ✅ .env.sample usa placeholders, NO credenciales reales
- [ ] ✅ .env.sample marca variables requeridas vs. opcionales
- [ ] ✅ .env.sample diferencia local vs. Azure
- [ ] ✅ .env.sample advierte sobre pgvector (no habilitado)
- [ ] ✅ .env.sample documenta autenticación (password vs. Azure Identity)
- [ ] ✅ Código Python verificado para mecanismos soportados
- [ ] ✅ PostgreSQL postgres_engine.py soporta ambos: password y Azure Identity
- [ ] ✅ OpenAI clients soportan: Azure, OpenAI.com, Ollama
- [ ] ✅ Dockerfile puede usar secretos de forma segura (NO hardcoded)

---

## 📚 ARCHIVOS RELACIONADOS

- [rag-azure-foundry-urosario/SKILL.md](../rag-azure-foundry-urosario/SKILL.md) — Azure AI Foundry (skill complementaria)
- [rag-azure-urosario-architecture/SKILL.md](../rag-azure-urosario-architecture/SKILL.md) — Arquitectura general
- [docs/pruebas/INFORME-AUDITORIA-RAG-INSTITUCIONAL.md](../../docs/pruebas/INFORME-AUDITORIA-RAG-INSTITUCIONAL.md) — Auditoría Foundry
- [.env.sample.aligned](.env.sample.aligned) — Propuesta de .env.sample actualizado
- [src/backend/fastapi_app/postgres_engine.py](src/backend/fastapi_app/postgres_engine.py) — Autenticación PostgreSQL
- [src/backend/fastapi_app/openai_clients.py](src/backend/fastapi_app/openai_clients.py) — Múltiples backends OpenAI
- [src/backend/fastapi_app/embeddings.py](src/backend/fastapi_app/embeddings.py) — compute_text_embedding (envía dimensions=1024)
- [src/backend/fastapi_app/dependencies.py](src/backend/fastapi_app/dependencies.py) — Variables de entorno de app

---

## 🚀 APLICABLE A

- Configuración de desarrollo local
- Configuración de Container Apps en producción
- Configuración de CI/CD (GitHub Actions)
- Documentación para nuevos desarrolladores
- Auditorías de seguridad (credenciales)
- Debugging de problemas de conexión

---

**Skill:** rag-azure-urosario-configuration-lessons  
**Versión:** 1.0  
**Generado:** 2026-08-31  
**Status:** ACTIVO  
**Reutilizable:** Sí  
**Tipo:** Lecciones de Configuración + Mejores Prácticas
