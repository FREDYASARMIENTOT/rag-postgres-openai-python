# RAG Institucional Universidad del Rosario — Azure AI Foundry Skill

**Status:** Skill reusable — Azure AI Foundry  \
**Versión:** 1.0  \
**Fecha:** 2026-01-09  \
**Basado en:** Auditoría real (TEST-001 a TEST-019)  \
**Commit:** ffe41ff  \
**Rama:** tesis-rag-institucional  \
**Operador:** analiticaur@urosario.edu.co

---

## 🎯 PROPÓSITO

Esta skill es la **fuente técnica de verdad** para todas las operaciones relacionadas
con Azure AI Foundry en el proyecto RAG Institucional de la Universidad del Rosario.

**No reemplaza** las skills `rag-azure-urosario-architecture` (arquitectura general)
ni `rag-azure-urosario-configuration-lessons` (lecciones de configuración PostgreSQL).

**Complementa** esas skills con información específica del ecosistema Foundry:
AI Resource, deployments, autenticación RBAC/API key, dimensiones reales de embeddings,
y comandos de descubrimiento.

---

## 📐 ALCANCE

| Incluye | No incluye |
|---------|------------|
| AI Resource Modelo-IA-UR | PostgreSQL (skill separada futura) |
| Foundry Proyecto-IA-UR | Container Apps |
| Deployments Foundry | GitHub Actions / CI/CD |
| Embeddings Foundry (text-embedding-3-large) | Infraestructura Bicep |
| Chat Foundry (gpt-4o-mini, gpt-5.6-luna) | Script de backup (respaldo-azure-rag-institucional.ps1) |
| Autenticación Foundry (API key vs RBAC) | Modificaciones de infraestructura |
| Comandos de descubrimiento (read-only) | Creación/modificación de deployments |
| Tests conocidos (TEST-001 a TEST-019) | |

---

## ☁ RECURSOS AZURE

### Subscription

```
Nombre: Sub-Tecnologia-Datamining
ID:     01bfad48-c092-4712-bc72-f141eb01a8d4
Tenant: ae525757-89ba-4d30-a2f7-49796ef8c604 (Universidad del Rosario)
```

**⚠️ IMPORTANTE:** Estos valores deben **validarse dinámicamente** con Azure CLI
y NO asumirse ciegamente. El tenant y subscription pueden cambiar.

```shell
az account show
az account subscription list
```

### Resource Group REAL del AI Resource

```
Nombre: RG-Datamining-IA-UR
Región: East US 2
```

**⚠️ CORRECCIÓN CRÍTICA RESPECTO A DOCUMENTACIÓN ANTERIOR:**

El AI Resource **Modelo-IA-UR** NO está en:

```
RG-Datamining-SII2.0-Dev   ← INCORRECTO
```

Está en:

```
RG-Datamining-IA-UR        ← REAL
```

Este error se ha propagado en documentación anterior y scripts de despliegue.
**Cualquier script o configuración que use `RG-Datamining-SII2.0-Dev` para
referenciar Modelo-IA-UR debe corregirse.**

### AI Resource

```
Nombre:    Modelo-IA-UR
Tipo:      AIServices (Cognitive Services)
SKU:       S0
Región:    East US 2
Endpoint:  https://modelo-ia-ur.cognitiveservices.azure.com/
Estado:    Succeeded
Identidad: SystemAssigned
Network:   Public, Allow
```

```shell
az cognitiveservices account show \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR
```

### Foundry Project

```
Nombre: Proyecto-IA-UR
```

El proyecto Foundry está asociado al AI Resource. No tiene su propio endpoint
de inferencia. Se usa para gestionar deployments, no para llamadas API directas.

---

## 🔤 EMBEDDINGS

### HALLAZGO CRÍTICO: dimensions=1024 NO SOPORTADO

La auditoría demostró un comportamiento asimétrico en el deployment
`ur-rag-embedding-3-large`:

| Condición | Resultado | Dimensión |
|-----------|-----------|-----------|
| Sin `dimensions` en body | ✅ 200 OK | 3072 dimensiones |
| Con `dimensions=1024` en body | ❌ 404 DeploymentNotFound | N/A |

**TEST-012: FAIL** — El deployment no acepta el parámetro `dimensions`.
**TEST-013: PASS** — Sin `dimensions`, el vector retornado es numéricamente
válido (sin NaN, sin Inf, rango típico [-0.08, 0.09]).

### Principio fundamental

```
CONFIGURACIÓN DECLARADA ≠ CAPACIDAD REAL DEL DEPLOYMENT
```

El código actual tiene:

```python
# embeddings.py línea 24-26
MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES = frozenset({
    "text-embedding-3-small",
    "text-embedding-3-large",
})
```

Y en `dependencies.py` línea 55:

```python
openai_embed_dimensions: Optional[int] = 1024
```

**Esto provocaría que `compute_text_embedding()` envíe `dimensions=1024`,
lo que causa 404 DeploymentNotFound en el Foundry real.**

### Estado REAL comprobado

| Atributo | Valor |
|----------|-------|
| Modelo lógico | `text-embedding-3-large` |
| Deployment Azure | `ur-rag-embedding-3-large` |
| Dimensiones solicitadas | 1024 (configuración actual del código) |
| Dimensiones realmente devueltas | **3072** (sin dimensions) |
| ¿Soporta dimensions? | ❌ NO |

### Implicaciones arquitectónicas

1. **PostgreSQL no puede usar Vector(1024)** — La dimensión real es 3072.
2. **Código actual fallará** si se conecta a Foundry con `dimensions=1024`.
3. **El modelo en `MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES`**
   está correcto para OpenAI.com (que sí soporta `dimensions`), pero
   incorrecto para este deployment Foundry específico.
4. **La variable `FOUNDRY_EMBEDDING_DIMENSIONS=1024`**
   (o `AZURE_OPENAI_EMBED_DIMENSIONS=1024`) no refleja la capacidad real.

### Opciones de resolución (para fase futura)

| Opción | Descripción | Riesgo |
|--------|-------------|--------|
| A | Cambiar columna PostgreSQL a `Vector(3072)` | Requiere recrear índices HNSW y seed data |
| B | Recrear deployment con versión que soporte `dimensions` | Puede afectar otros usuarios |
| C | Reducir dimensionalidad post-procesamiento (PCA/TruncatedSVD) | Pérdida de información, overhead |
| D | Usar `text-embedding-3-small` (1536d, soporta dimensions) | Cambio de modelo, reevaluar recall |

**Ninguna opción debe ejecutarse sin aprobación explícita.**

### Código relacionado

| Archivo | Función/Variable | Relevancia |
|---------|-----------------|------------|
| `src/backend/fastapi_app/embeddings.py` | `compute_text_embedding()` | Punto de entrada único para generación de embeddings |
| `src/backend/fastapi_app/openai_clients.py` | `_crear_cliente_openai_foundry()` | Crea cliente Foundry con API key o Azure Identity |
| `src/backend/fastapi_app/dependencies.py` | `openai_embed_dimensions = 1024` | Default que causaría fallo con Foundry |
| `src/backend/fastapi_app/proveedores.py` | `ProveedorEmbeddings` | Contrato abstracto, recibe dimensiones desde configuración |

---

## 🔐 AUTENTICACIÓN

### Mecanismos comprobados

| Mecanismo | Resultado | Detalle |
|-----------|-----------|---------|
| **API Key** (de Modelo-IA-UR) | ✅ PASS | `az cognitiveservices account keys list` funciona |
| **Azure Identity / RBAC** (analiticaur@urosario.edu.co) | ❌ FAIL | 401 Unauthorized — falta rol Cognitive Services OpenAI User |
| **Azure Identity / RBAC** (Managed Identity) | ❓ NO PROBADO | Pendiente de implementación en Container Apps |

### API Key

```shell
# Obtener API key
az cognitiveservices account keys list \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR
```

La API key funciona directamente con el endpoint del AI Resource:

```python
cliente = openai.AsyncOpenAI(
    base_url="https://modelo-ia-ur.cognitiveservices.azure.com/openai/v1/",
    api_key="<key_obtenida>",
)
```

**⚠️ La skill NO recomienda almacenar API keys en el repositorio.**
Las API keys deben usarse solo para testing controlado.

### Azure Identity (RBAC)

```python
cliente = openai.AsyncOpenAI(
    base_url="https://modelo-ia-ur.cognitiveservices.azure.com/openai/v1/",
    api_key=token_provider,
)
# token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
```

**Estado actual:** Falló para `analiticaur@urosario.edu.co` con 401.

### Prioridad arquitectónica

```
1. Managed Identity (Container Apps) ← Prioridad máxima para producción
2. Azure Developer CLI (local dev)    ← Testing local con Azure Identity
3. API Key                            ← Solo testing controlado, NUNCA en repositorio
```

---

## 👤 RBAC

### GAP documentado: Cognitive Services OpenAI User

**Rol faltante:** `Cognitive Services OpenAI User`

**Recurso objetivo:** Modelo-IA-UR (AI Resource)

**Identidad que lo requiere:**
- `analiticaur@urosario.edu.co` (para desarrollo local con Azure Identity)
- Managed Identity de Container Apps (para producción)

**Verificación:**

```shell
az role assignment list \
  --assignee analiticaur@urosario.edu.co \
  --scope /subscriptions/01bfad48-c092-4712-bc72-f141eb01a8d4/resourceGroups/RG-Datamining-IA-UR/providers/Microsoft.CognitiveServices/accounts/Modelo-IA-UR
```

**NO ejecutar automáticamente:**

```shell
# SOLO INFORMATIVO — NO EJECUTAR
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <principal> \
  --scope /subscriptions/<sub>/resourceGroups/RG-Datamining-IA-UR/providers/Microsoft.CognitiveServices/accounts/Modelo-IA-UR
```

La skill solo documenta:
- qué permiso falta
- qué recurso necesita el permiso
- qué identidad lo requiere
- cómo verificarlo

---

## 🔍 DISCOVERY (COMANDOS READ-ONLY)

### Subscription y Tenant

```shell
az account show
az account subscription list
```

### Resource Group

```shell
az group show --name RG-Datamining-IA-UR
```

### AI Resource

```shell
az cognitiveservices account show \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR
```

### Deployments

```shell
# Listar todos
az cognitiveservices account deployment list \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR

# Ver deployment específico
az cognitiveservices account deployment show \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR \
  --deployment-name ur-rag-gpt-5-6-luna

az cognitiveservices account deployment show \
  --name Modelo-IA-UR \
  --resource-group RG-Datamining-IA-UR \
  --deployment-name ur-rag-embedding-3-large
```

### API (inferencia directa)

```shell
# Probar chat completion
curl -X POST "https://modelo-ia-ur.cognitiveservices.azure.com/openai/deployments/ur-rag-gpt-5-6-luna/chat/completions?api-version=2024-06-01" \
  -H "api-key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hola"}]}'

# NOTA: Para AI Services / Foundry, probar también la ruta /openai/v1/...
```

---

## ✅ VALIDACIÓN EMPÍRICA

### Niveles de validación obligatorios

Toda integración Foundry debe validarse en **tres niveles**:

#### NIVEL 1 — Azure metadata (Azure CLI)

| Elemento | Comando | Verificación |
|----------|---------|-------------|
| Resource existe | `az cognitiveservices account show` | Estado: Succeeded |
| Endpoint alcanzable | GET al endpoint | HTTP 200 |
| Deployment listado | `az cognitiveservices account deployment list` | Estado: Running |
| Modelo correcto | Mismo comando | Modelo esperado |
| SKU / Capacity | Mismo comando | Capacidad suficiente |
| Versión de modelo | Mismo comando | Versión específica |

#### NIVEL 2 — Autenticación (HTTP)

| Prueba | Método | Éxito | Falla |
|--------|--------|-------|-------|
| API key | POST con `api-key` header | 200 OK | 401/403 |
| Azure Identity (RBAC) | POST con token Bearer | 200 OK | 401 |
| Token vencido | Misma prueba con token expirado | — | 401 |

#### NIVEL 3 — Inferencia real (Semántica)

| Prueba | Método | Éxito |
|--------|--------|-------|
| Chat completion | POST chat/completions con mensaje simple | Respuesta coherente |
| Embedding simple | POST embeddings con texto simple | Vector válido |
| Dimensión correcta | Verificar len(data[0].embedding) | 3072 (actual) |
| Latencia TTFT | Medir tiempo hasta primer token | < 500ms |
| Sin NaN/Inf | Validar todos los floats | NaN=False, Inf=False |

**Nunca considerar un deployment "validado" solamente porque Azure muestra
estado Succeeded.** Los errores de inferencia solo se detectan en Nivel 3.

---

## 📊 TESTS CONOCIDOS (TEST-001 a TEST-019)

### Tests Foundry (Azure + Identidad)

| ID | Resultado | Descripción |
|----|-----------|-------------|
| TEST-001 | ✅ PASS | Azure CLI / sesión activa |
| TEST-002 | ⚠️ WARNING | AI Resource encontrado, pero RG corregido a RG-Datamining-IA-UR |
| TEST-003 | ✅ PASS | 4 deployments encontrados en Modelo-IA-UR |
| TEST-011 | ✅ PASS | Cliente Foundry embeddings con API key |
| TEST-012 | ❌ FAIL | Embedding con dimensions=1024 → 404 DeploymentNotFound |
| TEST-013 | ✅ PASS | Embedding sin dimensions → 3072 dimensiones válidas |
| TEST-018 | ✅ PASS | Luna (ur-rag-gpt-5-6-luna) responde correctamente en ~742ms |

### Tests PostgreSQL (bloqueados — para skill futura)

| ID | Resultado | Descripción |
|----|-----------|-------------|
| TEST-004 | ✅ PASS | PostgreSQL server supersetdev existe, Ready |
| TEST-005 | ❌ FAIL | BD rag_institucional NO EXISTE |
| TEST-006 | ❌ BLOCKED | pgvector: azure.extensions = "" (vacío) |
| TEST-007 | ❌ BLOCKED | Tabla items no existe (BD no existe) |
| TEST-008 | ❌ BLOCKED | Columna embedding_3l no existe |
| TEST-009 | ❌ BLOCKED | Dimensión embedding desconocida |
| TEST-010 | ❌ BLOCKED | Índice HNSW no existe |
| TEST-015 | ❌ BLOCKED | Persistencia vectorial bloqueada |
| TEST-016 | ❌ BLOCKED | Búsqueda vectorial bloqueada |
| TEST-017 | ❌ BLOCKED | Top-K bloqueado |
| TEST-019 | ❌ BLOCKED | RAG completo bloqueado (sin datos persistidos) |

---

## ⛔ OPERACIONES PROHIBIDAS

Durante auditoría, backup, o cualquier operación que no tenga una solicitud explícita:

### Prohibido en deployments

```shell
az cognitiveservices account deployment create ...   # ⛔ PROHIBIDO
az cognitiveservices account deployment update ...   # ⛔ PROHIBIDO
az cognitiveservices account deployment delete ...   # ⛔ PROHIBIDO
```

### Deployments protegidos (NO MODIFICAR)

| Deployment | Razón |
|------------|-------|
| `sii-supervisor-gpt-4o-mini` | Pertenece al sistema SII, no al RAG |
| `ur-depei-gpt-5` | Propósito desconocido, requiere investigación |
| `ur-rag-gpt-5-6-luna` | LLM RAG confirmado, no cambiar sin solicitud |
| `ur-rag-embedding-3-large` | Embeddings RAG, no cambiar sin solicitud |

### Atributos protegidos en deployments

```
SKU            ← NO CAMBIAR
capacity       ← NO CAMBIAR
modelo         ← NO CAMBIAR
versión        ← NO CAMBIAR
deployment name ← NO CAMBIAR
```

### Excepción

La única excepción es si existe una **solicitud explícita y aprobada**
para modificar atributos específicos, con justificación documentada y
plan de rollback.

---

## ❌ ERRORES CONOCIDOS

### E001 — dimensions=1024 → 404 DeploymentNotFound

```
POST /openai/v1/embeddings
Body: { model: "ur-rag-embedding-3-large", input: "...", dimensions: 1024 }
→ HTTP 404: {"error":{"code":"DeploymentNotFound",...}}
```

**Causa:** El deployment `ur-rag-embedding-3-large` (modelo base version "1")
no soporta el parámetro `dimensions` del cuerpo de la solicitud.

**Solución:** No enviar `dimensions` en el body. El deployment retorna 3072
dimensiones por defecto.

### E002 — Azure Identity → 401 Unauthorized

```
POST /openai/v1/embeddings
Auth: Bearer token (de analiticaur@urosario.edu.co)
→ HTTP 401: Access denied due to invalid subscription key...
```

**Causa:** `analiticaur@urosario.edu.co` no tiene el rol
`Cognitive Services OpenAI User` asignado en el AI Resource.

**Solución:** Asignar el rol (si está autorizado) o usar API key para testing.

### E003 — RG incorrecto en documentación

```
Error común: Usar RG-Datamining-SII2.0-Dev para Modelo-IA-UR
→ El recurso no se encuentra
```

**Causa:** Documentación y scripts antiguos usaban el RG incorrecto.

**Solución:** Usar siempre `RG-Datamining-IA-UR` para Modelo-IA-UR.

### E004 — Puerto PostgreSQL 5432 timeout

```
ConnectionError: WinError 121 (timed out) connecting to supersetdev:5432
```

**Causa:** Firewall de red corporativo bloquea el puerto 5432. Solo IP
`201.234.181.230` está autorizada en el firewall del servidor.

**Solución:** Agregar regla de firewall para la IP actual, o usar
Azure CLI (`az postgres flexible-server execute`) si está disponible.

### E005 — deployment vs model name en clientes

El SDK de `openai.AsyncOpenAI` con `base_url` personalizado usa el
parámetro `model` en el body de la solicitud. Para Foundry/AIServices,
este debe ser el **nombre del deployment**, no el nombre del modelo.

```
✅ model: "ur-rag-embedding-3-large"  ← nombre del deployment
❌ model: "text-embedding-3-large"     ← nombre del modelo (NO funciona)
```

### E006 — El parámetro `input` debe ser string, no array

Para Foundry/AIServices, el parámetro `input` en embeddings debe ser
un string plano, no un array de strings:

```
✅ input: "Universidad del Rosario"
❌ input: ["Universidad del Rosario"]  ← falla en algunos deployments (404)

---

## 📋 REGLAS PARA FUTURAS AUTOMATIZACIONES

### Regla 1: Descubrimiento dinámico

El script `respaldo-azure-rag-institucional.ps1` (cuando se cree) **DEBE**
descubrir dinámicamente:

- subscription
- tenant
- resource group del AI Resource
- AI Resource name
- endpoint
- Foundry project
- deployments
- modelos
- versiones
- SKU
- capacity

No debe confiar exclusivamente en defaults hardcodeados. Los defaults
pueden existir como fallback, pero deben validarse contra Azure.

### Regla 2: No asumir dimensiones

La dimensión del embedding **no debe hardcodearse** como 1024.
Debe obtenerse mediante prueba real contra el deployment:

```python
POST /openai/v1/embeddings
Body: { model: "ur-rag-embedding-3-large", input: "test" }
→ len(data[0].embedding) = 3072  # dimensión REAL
```

### Regla 3: Separar Foundry de PostgreSQL

Esta skill es exclusiva de Azure AI Foundry.
La configuración PostgreSQL (BD, pgvector, tablas, índices) se tratará
en una skill separada (a crear).

### Regla 4: Validar antes de usar

Cada deployment de Foundry debe validarse en 3 niveles antes de
considerarse "disponible para RAG":

1. Azure metadata (CLI)
2. Autenticación (HTTP status)
3. Inferencia real (resultados semánticos)

### Regla 5: API key solo testing

Las API keys de Modelo-IA-UR deben usarse solo para:
- Testing controlado
- Desarrollo local temporal
- Validación de conectividad

**NUNCA** en producción, **NUNCA** en repositorio.

### Regla 6: No corregir infraestructura desde esta skill

Esta skill es exclusivamente de documentación y auditoría.
No ejecuta:
- Cambios de RBAC
- Creación de deployments
- Modificación de PostgreSQL
- Creación de scripts de backup

---

## 📚 LECCIONES APRENDIDAS

### Lección 1 — Resource Group equivocado

El AI Resource Modelo-IA-UR estaba documentado como parte de
`RG-Datamining-SII2.0-Dev`, pero realmente está en `RG-Datamining-IA-UR`.

**Lección:** Siempre verificar el Resource Group real de cada recurso
mediante `az <resource> show` antes de asumir su ubicación.

### Lección 2 — Deployment ≠ Modelo

El deployment `ur-rag-embedding-3-large` se llama distinto al modelo
subyacente (`text-embedding-3-large`). No asumir que el nombre del
deployment coincide con el nombre del modelo.

**Lección:** Usar `az cognitiveservices account deployment list` para
obtener el mapeo deployment → modelo.

### Lección 3 — dimensions param no universal

Aunque `text-embedding-3-large` soporta `dimensions` en OpenAI.com,
el deployment Foundry específico (`ur-rag-embedding-3-large`, version "1")
NO lo soporta.

**Lección:** La capacidad de un modelo en OpenAI.com no garantiza
la misma capacidad en un deployment Foundry. Probar siempre contra
el deployment real.

### Lección 4 — RBAC data plane vs management plane

Azure CLI funciona (`az cognitiveservices account ...`), pero la
inferencia directa falla con Azure Identity porque requiere el rol
`Cognitive Services OpenAI User` en el data plane.

**Lección:** Azure CLI accede al management plane (control de recursos).
La inferencia accede al data plane. Roles diferentes.

### Lección 5 — API key funciona, RBAC no

La API key de Modelo-IA-UR funciona para todas las operaciones.
Azure Identity con `analiticaur@urosario.edu.co` no tiene permisos
data plane.

**Lección:** Para usuarios sin rol data plane, la API key es el
mecanismo de autenticación disponible. Para producción, Managed Identity.

### Lección 6 — Foundry endpoint NO reemplaza AI Resource endpoint

Foundry Project no expone su propio endpoint de inferencia.
El endpoint de llamadas API es siempre el del AI Resource asociado.

**Lección:** No confundir Foundry Project endpoint (gestión) con
AI Resource endpoint (inferencia). Son diferentes.

### Lección 7 — String vs Array en input de embeddings

Algunos deployments Foundry requieren `input` como string plano,
no como array de strings.

**Lección:** Probar ambos formatos. Si `input: ["texto"]` falla,
probar `input: "texto"`.

---

## 🔗 DEPENDENCIAS ENTRE SKILLS

```
rag-azure-urosario-architecture         ← Arquitectura general del proyecto
└── rag-azure-foundry-urosario           ← ESTA SKILL (Azure AI Foundry)
    └── rag-azure-urosario-configuration-lessons  ← Lecciones de configuración
        └── (futura) rag-azure-postgresql-urosario  ← PostgreSQL + pgvector
```

---

## 🚀 APLICABLE A

- Operaciones con Azure AI Foundry
- Auditorías de conectividad Foundry
- Integración de deployments Foundry en el RAG
- Validación de embeddings y chat
- Configuración de autenticación Foundry
- Diagnóstico de errores de inferencia
- Onboarding de nuevos desarrolladores al ecosistema Foundry
- Creación futura de scripts de backup y automatización

---

**Skill:** rag-azure-foundry-urosario  \
**Versión:** 1.0  \
**Generado:** 2026-01-09  \
**Basado en:** Auditoría real con TEST-001 a TEST-019  \
**Status:** ACTIVO  \
**Reutilizable:** Sí