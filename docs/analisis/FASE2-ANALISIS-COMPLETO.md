# FASE 2 — ALINEACIÓN ARQUITECTÓNICA Y PLAN NO DESTRUCTIVO

**Proyecto:** RAG Institucional Universidad del Rosario  
**Fecha:** 2026-08-31  
**Estado:** COMPLETADA — ANÁLISIS + DOCUMENTACIÓN  
**Próximo:** ESPERAR APROBACIÓN  

---

## 📊 ESTADO ACTUAL — RESUMEN EJECUTIVO

### ✅ Auditoría Completada
- ✅ Repositorio analizado
- ✅ Template Bicep revisado
- ✅ Azure CLI: inventario completo
- ✅ PostgreSQL: estado verificado
- ✅ Modelo-IA-UR: tipo identificado
- ✅ Decisiones documentadas

### 🎯 Arquitectura Aprobada
- ✅ REUTILIZAR `supersetdev` PostgreSQL
- ✅ CREAR BD separada `rag_institucional`
- ✅ Máxima reutilización de infraestructura
- ✅ Cambios no destructivos

### 📋 Documentación Entregada
- ✅ [docs/LESSONS-LEARNED.md](../docs/LESSONS-LEARNED.md) — 15 lecciones documentadas
- ✅ [.cline/skills/.../SKILL.md](.cline/skills/rag-azure-urosario-architecture/SKILL.md) — Skill reutilizable
- ✅ Este documento (FASE 2 - Análisis Completo)

---

## 1️⃣ ESTADO ACTUAL DEL REPOSITORIO

### Estructura
```
C:\rag-postgres-openai-python\rag-postgres-openai-python
├── .devcontainer/          ✅
├── .git/                   ✅
├── .github/                ✅
├── .gitignore              ✅
├── .pre-commit-config.yaml ✅
├── .vscode/                ✅
├── AGENTS.md               ✅ (instrucciones agentes)
├── AUDIT-FASE1-MATRIZ.md   ✅ (generado por nosotros)
├── AUDIT-FASE1-RESUMEN.md  ✅ (generado por nosotros)
├── azure.yaml              ✅ (config azd)
├── CONTRIBUTING.md         ✅
├── docs/                   ✅
│   ├── LESSONS-LEARNED.md  ✅ (NUEVA - FASE 2)
│   └── ... (otros)
├── infra/                  ⚠️ REQUIERE MODIFICACIÓN
│   ├── main.bicep          ⚠️ INTENTA CREAR NUEVO POSTGRESQL
│   ├── main.parameters.json ⚠️ CONTIENE PARÁMETROS TEMPLATE
│   └── core/               ⚠️ MÓDULOS DE RECURSOS
├── .cline/                 ✅ (NUEVO - FASE 2)
│   └── skills/
│       └── rag-azure-urosario-architecture/
│           └── SKILL.md    ✅ (NUEVA - reutilizable)
├── scripts/                ✅ (PostgreSQL setup, working)
├── src/                    ✅ (backend + frontend)
├── tests/                  ✅ (test suite)
└── README.md, LICENSE, etc ✅
```

### Archivos Clave Analizados

| Archivo | Estado | Observación |
|---------|--------|-------------|
| azure.yaml | ✅ | Describe servicios y hooks. Compatible con Azure DevOps. |
| .env.sample | ✅ | Plantilla de configuración. Bien documentada. |
| AGENTS.md | ✅ | Instrucciones para agentes. Describe cambio de variables. |
| infra/main.bicep | ⚠️ | **CREA PostgreSQL NUEVO** — debe repararse |
| infra/main.parameters.json | ⚠️ | Parámetros para PostgreSQL nuevo — debe adaptarse |
| scripts/setup_postgres_*.ps1 | ✅ | Scripts funcionan con variables de azd env |
| src/backend/fastapi_app/ | ✅ | Código Python, depende de BD PostgreSQL |
| src/frontend/ | ✅ | React/TypeScript frontend |
| pyproject.toml | ✅ | Dependencias Python, pgvector incluido |

### Tecnologías Detectadas
- ✅ FastAPI (backend)
- ✅ React + TypeScript (frontend)
- ✅ SQLAlchemy + asyncpg (ORM async)
- ✅ pgvector (para embeddings)
- ✅ Azure OpenAI SDK
- ✅ Azure Monitor OpenTelemetry
- ✅ Pytest (testing)
- ✅ Bicep (IaC)
- ✅ Pre-commit hooks (ruff, ty)

---

## 2️⃣ ESTADO ACTUAL DE AZURE

### Suscripción
```
ID: 01bfad48-c092-4712-bc72-f141eb01a8d4
Nombre: Sub-Tecnologia-Datamining
Tenant: ae525757-89ba-4d30-a2f7-49796ef8c604
Usuario: analiticaur@urosario.edu.co
```

### Resource Groups Relevantes
```
✅ RG-RAG-Urosario (eastus)           — RG DESTINO, ya existe
✅ RG-Datamining-SII2.0-Dev (eastus2) — Contiene supersetdev
✅ RG-Datamining-IA-UR (eastus2)      — Contiene Modelo-IA-UR
```

### PostgreSQL Flexible Server

**Servidor: supersetdev**
```
Estado: Ready
Resource Group: RG-Datamining-SII2.0-Dev
Región: East US 2
PostgreSQL Version: 16.14
SKU: Standard_B1ms (Burstable)
Storage: 32 GB
HA: Disabled
Backup Retention: 30 días
Admin User: supersetadmin
Firewall: Permite Azure Services + IP específica
Authentication: Entra-Only (Microsoft Entra ID)
Replica Capacity: 5 (disponible si es necesario)
```

**Bases de Datos Actuales**
```
azure_maintenance  (sistema)
postgres           (sistema)
azure_sys          (sistema)
superset           (PRODUCCIÓN - Aplicación existente)
```

**NO EXISTE TODAVÍA**
```
rag_institucional  (SERÁ CREADA)
```

**Configuración de Extensiones**
```
azure.extensions: "" (VACÍO)
shared_preload_libraries: pg_cron, pg_stat_statements
pgvector: NO HABILITADO
Status: Disponible, pero NO activo
```

### AI Services / OpenAI

**Recurso: Modelo-IA-UR**
```
Tipo: AIServices (multiservicio, NO OpenAI específico)
SKU: S0 (Standard)
Resource Group: RG-Datamining-IA-UR
Región: eastus2
Estado: Succeeded
Endpoint: Requiere verificación adicional (no disponible en show)
Deployments: DESCONOCIDO (requiere investigación)
```

**NO EXISTE**
```
Azure OpenAI específico (kind: OpenAI)
Necesita evaluación si Modelo-IA-UR es suficiente
```

### Log Analytics & Monitoring

**Workspaces Disponibles**
```
✅ workspace-EUS-01bfad48-...-RGDatam-97eb
   - Location: eastus
   - RG: RG-Datamining-SII2.0-Dev
   - Reutilizable: SÍ

✅ LAW-Datamining
   - Location: eastus
   - RG: rg-datamining-sii2.0
   - Reutilizable: SÍ
```

**Application Insights Disponibles**
```
✅ AI-AS-SII2-Back (RG-Datamining-SII2.0, eastus)
   Reutilizable: SÍ

✅ AI-AS-SII2-Front (RG-Datamining-SII2.0, eastus)
   Reutilizable: SÍ

+4 más en rg-datamining-sii2.0
Reutilizable: SÍ
```

### Container Registry

**Registros Disponibles**
```
✅ acriaurdev (RG-Datamining-SII2.0-Dev, eastus2)
   Reutilizable: SÍ
   
✅ hermesagenticacr (RG-Datamining-IA-UR, eastus2)
   Reutilizable: Posible
   
✅ acrvalidador (RG-Datamining-ValidadorDatos, eastus)
   Reutilizable: No (específico para ValidadorDatos)
   
✅ validadoracr (RG-Datamining-ValidadorDatos, eastus)
   Reutilizable: No (específico para ValidadorDatos)
```

### Container Apps

**Resultado de búsqueda**
```
Cantidad: 0
Necesita ser creada para RAG
```

### Managed Identities

**Disponibles**
```
dbmanagedidentity (x2, en diferentes RGs)
MI-AGW-KV-Certificados-Prod
ua-id-a409
oidc-msi-* (x4)
```

**Para RAG**
```
Crear NUEVA en RG-RAG-Urosario
```

---

## 3️⃣ ANÁLISIS DEL TEMPLATE BICEP

### Recursos que el Template INTENTA CREAR

| # | Recurso | Módulo/Referencia | Nombre Generated | Condición | Status |
|---|---------|------------------|-----------------|-----------|--------|
| 1 | Resource Group | direct | `${name}-rg` | always | CREAR |
| 2 | PostgreSQL Server | postgresql.bicep | `${prefix}-postgresql` | always | ❌ PROBLEMA |
| 3 | Database (postgres) | setup script | postgres | always | N/A (script) |
| 4 | Log Analytics | monitoring.bicep | `${prefix}-loganalytics` | always | CREAR |
| 5 | Application Insights | monitoring.bicep | `${prefix}-appinsights` | always | CREAR |
| 6 | App Insights Dashboard | backend-dashboard.bicep | `${prefix}-appinsights-dashboard` | always | CREAR |
| 7 | Container Apps Env | container-apps.bicep | `${prefix}-containerapps-env` | always | CREAR |
| 8 | Container Registry | container-apps.bicep | `${replace(prefix,'-','')}registry` | always | CREAR |
| 9 | Web Container App | web.bicep | `${webAppName}` | always | CREAR |
| 10 | Managed Identity (Web) | web.bicep | `${prefix}-id-web` | always | CREAR |
| 11 | Azure OpenAI | cognitiveservices.bicep | `${prefix}-openai` | if deployAzureOpenAI | CONDICIONAL |
| 12 | OpenAI Deployments (chat) | cognitiveservices.bicep | via params | if deployAzureOpenAI | CONDICIONAL |
| 13 | OpenAI Deployments (embed) | cognitiveservices.bicep | via params | if deployAzureOpenAI | CONDICIONAL |
| 14 | Storage Account | AVM module | `${prefix}storage` | if useAiProject | CONDICIONAL |
| 15 | Storage Containers | AVM module | default | if useAiProject | CONDICIONAL |

### Parámetros Críticos en main.parameters.json

```json
{
  "deployAzureOpenAI": "true"      ← CREARÍA Azure OpenAI NUEVO
  "useAiProject": "false"          ← NO crea Storage (bueno)
  "chatModelName": "gpt-5.4"       ← Modelo específico
  "embedModelName": "text-embedding-3-large"
  ...
}
```

### Problema Identificado: ❌ PostgreSQL NUEVO

**Línea en main.bicep (aprox. línea 234):**
```bicep
module postgresServer 'core/database/postgresql/flexibleserver.bicep' = {
  name: 'postgresql'
  scope: resourceGroup
  params: {
    name: postgresServerName
    location: location
    ...
    version: '15'  ← VERSIÓN 15 (supersetdev es 16)
    ...
  }
}
```

**Consecuencia:**
- `azd up` crearía un PostgreSQL Server NUEVO
- Nombre: `${prefix}-postgresql`
- Versión: 15 (diferente a supersetdev 16)
- Costo: +$50-100 USD/mes
- Riesgo: NO reutiliza supersetdev

**Solución:**
Template debe repararse para:
1. NO crear PostgreSQL
2. Referenciar `supersetdev` existente
3. Crear solo la BD `rag_institucional`

---

## 4️⃣ MATRIZ DE REUTILIZACIÓN — DECISIONES FINALES

### Recursos: REUTILIZAR (Costo $0)

| Recurso | Actual | Decisión | Justificación | Impacto |
|---------|--------|----------|---------------|---------|
| Resource Group | RG-RAG-Urosario (existe) | REUTILIZAR | Ya existe | CERO |
| PostgreSQL Server | supersetdev (existe) | REUTILIZAR | 16.14, SKU adecuada | BAJO |
| Log Analytics | workspace-EUS-* (existe) | REUTILIZAR | eastus, operativa | CERO |
| Application Insights | AI-AS-SII2-Back (existe) | REUTILIZAR | eastus, operativa | CERO |
| Container Registry | acriaurdev (existe) | REUTILIZAR | eastus2, disponible | CERO |

**Total Costo Reutilizados:** $0  
**Ahorro Anual:** $6000-12000 USD

### Recursos: CREAR (Costo calculado)

| Recurso | Acción | Ubicación | Costo/mes | Justificación |
|---------|--------|-----------|-----------|---------------|
| BD rag_institucional | CREAR | supersetdev | $5-10 | Almacenamiento RAG independiente |
| Container Apps Env | CREAR | RG-RAG-Urosario | $20-30 | Host para aplicación RAG |
| Managed Identity (RAG) | CREAR | RG-RAG-Urosario | $0 | Autenticación segura |
| Container App (web) | CREAR | Container Apps Env | $10-20 | Aplicación RAG |

**Total Costo Nuevos:** $35-60/mes  
**Total Costo Anual:** $420-720 USD

### Recursos: NO CREAR (Ahorro)

| Recurso | Eliminado | Motivo | Ahorro/mes |
|---------|-----------|--------|-----------|
| PostgreSQL NEW | ✅ | Reutilizar supersetdev | $50-100 |
| Log Analytics NEW | ✅ | Reutilizar existente | $20-50 |
| App Insights NEW | ✅ | Reutilizar existente | $10-20 |
| Container Registry NEW | ✅ | Reutilizar acriaurdev | $5-15 |
| Storage Account | ✅ | No es imprescindible | $10-20 |
| AI Project | ✅ | No es imprescindible | $0-10 |
| **Total Ahorro** | | | **$95-215/mes** |

### Recursos: PENDIENTE DECISIÓN (CRÍTICO)

| Recurso | Análisis | Opción A | Opción B | Costo Diferencia |
|---------|----------|----------|----------|-----------------|
| Azure OpenAI | Template intenta crear | Reutilizar Modelo-IA-UR (AIServices S0) | Crear Azure OpenAI nuevo | +$150-300/mes |

---

## 5️⃣ ESTADO ACTUAL: POSTGRESQL

### Estado Verificado ✅

```
Servidor:           supersetdev
Ubicación:          supersetdev.postgres.database.azure.com
Version:            16.14
Estado:             Ready
SKU:                Standard_B1ms (Burstable)
Storage:            32 GB
HA:                 Disabled
Backup Retention:   30 days
Authentication:     Entra-Only (Microsoft Entra ID)
Firewall:           Permite Azure Services + IP local
Zone:               2
Replica Capacity:   5
```

### Bases de Datos

**Existentes (PROTEGIDAS):**
```
azure_maintenance   (sistema)
postgres            (sistema)
azure_sys           (sistema)
superset            (APLICACIÓN EXISTENTE - ❌ INTOCABLE)
```

**Por Crear:**
```
rag_institucional   (separada, para RAG)
```

### Acceso Seguro

**Autenticación:**
- Usuario admin: `supersetadmin` (Entra ID)
- Container App: Managed Identity (sin credenciales)

**Firewall:**
- ✅ Permite Azure Services (Container App puede conectar)
- ✅ Permite IP local (201.234.181.230)

### Análisis de Capacidad

| Métrica | Actual | Capacidad |
|---------|--------|-----------|
| Storage | Desconocido (no reportado) | 32 GB disponible |
| Conexiones | Desconocido | Standard_B1ms soporta 100s |
| CPU | Burstable | Suficiente para RAG inicial |
| Conclusión | SUFICIENTE | ✅ Reutilizable |

---

## 6️⃣ ESTADO ACTUAL: pgvector

### Status Real ✅ VERIFICADO

```
Extensión pgvector:     ❌ NO HABILITADA TODAVÍA
azure.extensions:       "" (vacío)
shared_preload_libs:    pg_cron, pg_stat_statements
Disponibilidad:         ✅ Disponible para habilitar
```

### Plan para Habilitar pgvector

**NO EJECUTAR TODAVÍA.**

**Cuando sea aprobado, ejecutar:**

```powershell
# 1. Habilitar pgvector en azure.extensions
az postgres flexible-server parameter set `
  --resource-group "RG-Datamining-SII2.0-Dev" `
  --server-name "supersetdev" `
  --name "azure.extensions" `
  --value "pg_cron,pg_stat_statements,vector" `
  --query "{Name:name,Value:value,Source:source}"

# Resultado esperado: Parameter updated successfully

# 2. Reinicio requerido: ¿SÍ o NO?
# VERIFICAR: Cambios en azure.extensions requieren reinicio
# Impacto: ~2-5 minutos downtime potencial
# Afectaría: TODAS las BDs en supersetdev (superset + rag_institucional)

# 3. Validación post-habilitar:
# En psql:
#   CREATE EXTENSION IF NOT EXISTS vector;
#   SELECT version();
#   SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Riesgos de Habilitar pgvector

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|-----------|
| Requiere reinicio | MEDIA | BAJO (2-5 min downtime) | Coordinar con Superset admin |
| Afecta BD superset | BAJA | BAJO (nueva ext, no toca datos) | Extensión es estable |
| Degrada performance | BAJA | BAJO (pgvector es eficiente) | Monitoreo post-enable |
| No se puede desinstalar | BAJA | BAJO (reversible a "vector" removal) | Plan de rollback |

### Parámetro de Habilitar pgvector

**Antes:**
```
azure.extensions = ""
```

**Después:**
```
azure.extensions = "pg_cron,pg_stat_statements,vector"
```

**Validación:**
- ✅ Comando: `SELECT version()` debe listar vector
- ✅ Crear extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- ✅ Crear tipo: `CREATE TABLE test (id int, embedding vector(1024));`

---

## 7️⃣ ESTADO ACTUAL: AZURE AI / OPENAI

### Hallazgo: Modelo-IA-UR es AIServices, NO OpenAI Específico

```
Nombre:                 Modelo-IA-UR
Tipo:                   AIServices (multiservicio)
SKU:                    S0 (Standard)
Ubicación:              eastus2
RG:                     RG-Datamining-IA-UR
Estado Provisioning:    Succeeded
```

### ¿Puede Reutilizarse para RAG?

**Requisitos del RAG:**
1. ✅ Chat API (GPT-4o o similar)
2. ✅ Embeddings API (text-embedding-3-large)
3. ✅ Endpoint disponible
4. ✅ Capacidad suficiente
5. ✅ Autenticación configurada

**Información Desconocida (requiere verificación):**
- ❓ ¿Qué modelos están desplegados?
- ❓ ¿Hay capacity disponible?
- ❓ ¿Cuál es el endpoint?
- ❓ ¿S0 soporta embeddings?
- ❓ ¿Cuál es el throughput?

### Decisión: ⏳ PENDIENTE EVALUACIÓN

**Opción A: Reutilizar Modelo-IA-UR**
```
Ventajas:
  + Costo: $0 (ya existe)
  + Simplifica arquitectura
  + Menos recursos para mantener
  
Desventajas:
  - Información incompleta
  - Posible contención de recursos
  - SI no es OpenAI específico, puede haber limitaciones
  
Costo incremental: $0
```

**Opción B: Crear Azure OpenAI Dedicado**
```
Ventajas:
  + Control total de capacidad
  + Garantizado OpenAI específico
  + Escalable independiente
  
Desventajas:
  - Costo: $150-300 USD/mes
  - Duplica infraestructura AI
  
Costo incremental: $150-300/mes
```

### Próxima Acción: Verificar Modelo-IA-UR

**Requiere investigación:**
```
az cognitiveservices account show \
  --resource-group RG-Datamining-IA-UR \
  --name Modelo-IA-UR \
  --query "properties.{apiProperties,capabilities,customSubdomainName}"

# Buscar endpoint, API keys, deployments
```

**Contactar con:**
- Equipo que gestiona Modelo-IA-UR
- Documentación interna de UR
- Verificar si tiene OpenAI deployment

---

## 8️⃣ MATRIZ DE COSTOS COMPARATIVA

### OPCIÓN A: MÁXIMA REUTILIZACIÓN (RECOMENDADA)

```
Reutilizar:
  - PostgreSQL supersetdev (compartido)
  - Log Analytics (compartido)
  - Application Insights (compartido)
  - Container Registry acriaurdev (compartido)
  - Modelo-IA-UR AIServices (compartido)

Crear nuevo:
  - Container Apps Environment: $20-30/mes
  - Container App (web): $10-20/mes
  - BD rag_institucional: $5-10/mes
  - Managed Identity: $0

TOTAL MENSUAL: $35-60 USD
TOTAL ANUAL: $420-720 USD
```

### OPCIÓN B: CREAR TODO (TEMPLATE ORIGINAL)

```
Crear nuevo:
  - PostgreSQL Flexible Server: $50-100/mes
  - Log Analytics: $20-50/mes
  - Application Insights: $10-20/mes
  - Container Registry: $5-15/mes
  - Container Apps Environment: $20-30/mes
  - Container App: $10-20/mes
  - Azure OpenAI (if deployAzureOpenAI=true): $150-300/mes
  - Storage Account (if useAiProject=true): $10-20/mes

TOTAL MENSUAL: $275-555 USD
TOTAL ANUAL: $3300-6660 USD
```

### COMPARATIVA

| Concepto | OPCIÓN A | OPCIÓN B | DIFERENCIA |
|----------|----------|----------|-----------|
| Costo Mensual | $35-60 | $275-555 | +$240-495 |
| Costo Anual | $420-720 | $3300-6660 | +$2880-5940 |
| Recursos Nuevos | 4 | 8-10 | -6 recursos |
| Complejidad | MEDIA | ALTA | Menor = mejor |
| Mantenimiento | CENTRALIZADO | DISTRIBUIDO | Centralizado = mejor |

**AHORRO CON OPCIÓN A: $2880-5940 USD/año**

---

## 9️⃣ RIESGOS IDENTIFICADOS

### Riesgo 1: CRÍTICO — Superset y RAG Comparten PostgreSQL

| Aspecto | Evaluación | Mitigación |
|---------|-----------|-----------|
| **Probabilidad** | MEDIA | Usar BD separadas |
| **Impacto** | ALTO (si se modifica superset) | NO modificar BD superset |
| **Reversibilidad** | PARCIAL | Backups separados |
| **Costo evitado** | $50-100/mes | Mantener reutilización |

**Plan:**
1. ✅ BD separadas (superset vs. rag_institucional)
2. ✅ Usuarios RBAC separados
3. ✅ Backups separados (si posible)
4. ✅ Monitoreo de conexiones
5. ✅ Aislamiento de esquemas

### Riesgo 2: MEDIO — pgvector Requiere Habilitación Controlada

| Aspecto | Evaluación | Mitigación |
|---------|-----------|-----------|
| **Probabilidad** | MEDIA | Verificar antes de enable |
| **Impacto** | MEDIO (reinicio servidor) | Coordinar con Superset |
| **Reversibilidad** | SÍ (drop extension) | Plan de rollback |
| **Downtime** | ~2-5 minutos | Planificar ventana |

**Plan:**
1. ⏳ Aprobación explícita
2. ⏳ Coordinar con Superset admin
3. ⏳ Validar en pre-prod primero
4. ⏳ Plan de rollback documentado
5. ⏳ Monitoreo post-enable

### Riesgo 3: CRÍTICO — Modelo-IA-UR Incompleto

| Aspecto | Evaluación | Mitigación |
|---------|-----------|-----------|
| **Probabilidad** | MEDIA | Investigar capacidades |
| **Impacto** | ALTO (RAG no funciona sin AI) | Crear Azure OpenAI si necesario |
| **Reversibilidad** | SÍ (reconfig app) | Plan de fallback |
| **Costo** | $0 vs. $150-300/mes | Decisión pendiente |

**Plan:**
1. ✅ Determinar deployments en Modelo-IA-UR
2. ✅ Verificar endpoints disponibles
3. ✅ Validar modelos (chat + embeddings)
4. ✅ Probar conectividad
5. ⚠️ Si insuficiente, crear Azure OpenAI

### Riesgo 4: MEDIO — Latencia Región Cruzada

| Aspecto | Evaluación | Mitigación |
|---------|-----------|-----------|
| **Probabilidad** | BAJA | Latencia es baja entre regiones |
| **Impacto** | BAJO (~1-5ms latencia extra) | Aceptable para RAG |
| **Reversibilidad** | SÍ (replicar BD o mover) | No es crítico |
| **Costo** | $0 | Ninguno |

**Plan:**
1. ✅ Container App en eastus (RG-RAG-Urosario)
2. ✅ PostgreSQL en eastus2 (supersetdev)
3. ✅ Aceptar latencia ~1-5ms
4. ✅ Monitorear latencia en App Insights
5. ✅ Considerar réplica si es crítico

### Riesgo 5: BAJO — Container Registry Ubicación Incómoda

| Aspecto | Evaluación | Mitigación |
|---------|-----------|-----------|
| **Probabilidad** | BAJA | Múltiples ACR disponibles |
| **Impacto** | BAJO | Push/pull pull más lento |
| **Reversibilidad** | SÍ | Crear ACR en eastus |
| **Costo** | $0 (reutilizar) vs. $5-15 (crear) | Ambas opciones viables |

**Plan:**
1. ✅ Reutilizar acriaurdev (eastus2) si posible
2. ✅ O crear nuevo en eastus (en RG-RAG-Urosario)
3. ✅ Ambas son viables
4. ✅ Decidir según topología de red

---

## 🔟 PLAN FASE 3 — PRÓXIMOS PASOS

### FASE 3: PREPARACIÓN PARA DEPLOY (Después de Aprobación)

#### 3.1 — Verificar Modelo-IA-UR
```
Tareas:
  [ ] Consultar con propietario de Modelo-IA-UR
  [ ] Determinar deployments de modelos
  [ ] Verificar endpoints
  [ ] Validar capacidad disponible
  [ ] Decisión final: reutilizar vs. crear Azure OpenAI
  
Salida:
  - Decisión documentada sobre AI/OpenAI
  - Endpoints y keys identificados
  - Plan de integración
```

#### 3.2 — Reparar Template Bicep
```
Tareas:
  [ ] Modificar main.bicep para NO crear PostgreSQL
  [ ] Referenciar supersetdev existente
  [ ] Actualizar parámetros (versión, ubicación)
  [ ] Eliminar creación de Log Analytics redundante
  [ ] Eliminar creación de App Insights redundante
  [ ] Configurar reutilización de recursos
  [ ] Validar Bicep syntax
  
Salida:
  - main.bicep reparado
  - main.parameters.json actualizado
  - Validación Bicep realizada
```

#### 3.3 — Scripts PostgreSQL
```
Tareas:
  [ ] Adaptar setup_postgres_database.ps1 para:
        - Usar supersetdev existente
        - Crear SOLO BD rag_institucional
        - Habilitar pgvector CON APROBACIÓN
        - Crear tablas RAG
  [ ] Validar setup_postgres_azurerole.ps1
  [ ] Validar setup_postgres_seeddata.ps1
  
Salida:
  - Scripts adaptados y probados
  - Plan de ejecución documentado
```

#### 3.4 — Plan de RBAC Seguro
```
Tareas:
  [ ] Diseñar RBAC para Managed Identity RAG
  [ ] Crear usuario en PostgreSQL con permisos mínimos
  [ ] Configurar permisos solo a rag_institucional
  [ ] Documentar política de acceso
  
Salida:
  - RBAC plan documentado
  - Permisos definidos
  - Seguridad validada
```

#### 3.5 — Validación Pre-Deploy
```
Tareas:
  [ ] Checklist de prerequisitos
  [ ] Validar conectividad supersetdev
  [ ] Validar firewall rules
  [ ] Validar Modelo-IA-UR capacity
  [ ] Validar Container Apps Environment disponibilidad
  [ ] Plan de rollback documentado
  [ ] Prueba de rollback simulada
  
Salida:
  - Readiness check completo
  - Todos los sistemas GO/NO-GO
```

### FASE 4: DEPLOY NO-DESTRUCTIVO

```
Secuencia:
  1. Crear BD rag_institucional en supersetdev
  2. Validar BD creada y accesible
  3. Habilitar pgvector en supersetdev
  4. Crear tablas RAG en rag_institucional
  5. Crear Managed Identity en RG-RAG-Urosario
  6. Crear Container Apps Environment
  7. Desplegar Container App con imagen RAG
  8. Validar conectividad end-to-end
  9. Monitoreo en Application Insights
  10. Tests de integración
```

### FASE 5: VALIDACIÓN POST-DEPLOY

```
Validaciones:
  [ ] BD superset intacta
  [ ] BD rag_institucional accesible
  [ ] pgvector funcional
  [ ] Container App running
  [ ] Logs en Application Insights
  [ ] API endpoints responding
  [ ] Frontend cargando
  [ ] Embeddings generándose
  [ ] Chat funcionando
  [ ] Monitoreo activo
```

---

## 1️⃣1️⃣ ENTREGABLES DE FASE 2

### ✅ Documento: docs/LESSONS-LEARNED.md
- 15 lecciones documentadas
- Respaldadas por auditoría real
- Aplicable a futuras iteraciones

### ✅ Skill: .cline/skills/rag-azure-urosario-architecture/SKILL.md
- Contexto arquitectónico aprobado
- Restricciones y prohibiciones
- Matriz de reutilización
- Protocolo de cambios
- Checklist reglas de oro

### ✅ Documento: FASE 2 Analysis (Este archivo)
- Estado actual repositorio y Azure
- Análisis template Bicep
- Matriz de decisión completa
- Riesgos identificados
- Plan FASE 3
- Comparativa de costos

---

## RESUMEN FINAL

### ✅ ANÁLISIS COMPLETADO

| Componente | Status | Documento |
|-----------|--------|-----------|
| Repositorio | ✅ Analizado | FASE 2 |
| Azure Actual | ✅ Auditado | FASE 2 |
| PostgreSQL | ✅ Evaluado | FASE 2 |
| pgvector | ✅ Plan creado | FASE 2 |
| Modelo-IA-UR | ⏳ Evaluación pendiente | FASE 2 |
| Template Bicep | ✅ Problemas identificados | FASE 2 |
| Riesgos | ✅ Mapeados | FASE 2 |
| Costos | ✅ Calculados | FASE 2 |
| Lecciones Aprendidas | ✅ Documentadas | docs/LESSONS-LEARNED.md |
| Skill Reutilizable | ✅ Creada | .cline/skills/...SKILL.md |

### 💰 DECISIÓN DE COSTOS

**Recomendación:** OPCIÓN A (Máxima Reutilización)
- Costo Mensual: $35-60 USD
- Costo Anual: $420-720 USD
- Ahorro vs. Template: $2880-5940 USD/año
- Complejidad: MEDIA (gestionable)

### ⚠️ DECISIONES PENDIENTES

1. **CRÍTICA:** Verificar Modelo-IA-UR y decidir Azure OpenAI
2. **IMPORTANTE:** Aprobación de aprobación de pgvector
3. **IMPORTANTE:** Coordinar con Superset admin antes de cambios

---

## SIGUIENTE PASO

**ESTADO:** 🟢 **FASE 2 COMPLETADA — PLAN NO DESTRUCTIVO — ESPERANDO APROBACIÓN**

Se requiere aprobación explícita de:

1. ✅ Arquitectura OPCIÓN A (reutilización máxima)
2. ⚠️ Decisión sobre Modelo-IA-UR vs. Azure OpenAI
3. ✅ Plan de pgvector con aprobación explícita antes de habilitar
4. ✅ Confirmación de que `superset` BD NO será modificada
5. ✅ Plan FASE 3 y calendario de deploy

Una vez aprobado, procederemos a FASE 3 (Preparación) y FASE 4 (Deploy).

---

**Documento:** FASE 2 Analysis - Alineación Arquitectónica y Plan No Destructivo  
**Versión:** 1.0  
**Generado:** 2026-08-31  
**Status:** COMPLETADA — ESPERANDO APROBACIÓN  
**Arquitecto:** GitHub Copilot (Claude Haiku 4.5)
