# RAG Institucional Universidad del Rosario — Architecture Skill

**Status:** Skill reusable para contexto arquitectónico permanente  
**Versión:** 2.0  
**Fecha:** 2026-09-01  
**Proyecto:** RAG Institucional UR  
**Rama:** tesis-rag-institucional

---

## 🧩 ESTADO DEL PROYECTO

### Fase 3.2 — Refactorización del RAG Compartido ✅ COMPLETADA (2026-09-01)

**Commit:** `bcb5641` — `[REFACTORIZACIÓN] Fortalecer arquitectura del RAG institucional compartido`

**Cambios realizados:**

| Área | Archivos | Descripción |
|------|----------|-------------|
| SQL Security | `postgres_searcher.py` | Whitelists `COLUMNAS_FILTRO_PERMITIDAS`, `OPERADORES_FILTRO_PERMITIDOS` |
| Arquitectura | `postgres_models.py` | Documentación completa, HNSW params, `__tablename__` restaurado |
| Embeddings | `embeddings.py` | `MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES`, validación |
| pgvector | `postgres_engine.py` | `verify_pgvector_available()`, `verify_pgvector_created()` (read-only) |
| Config | `dependencies.py` | Docstring completos, type hints |
| Tests | `tests/` (7 files) | 38 unit tests + 2 azure, fixtures compartidas, `--run-azure` |
| Docs | `docs/ARCHITECTURA-RAG.md` | Documento completo de arquitectura |
| Lecciones | `docs/LESSONS-LEARNED.md` | 6 nuevas lecciones |
| Bicep | `infra/REUTILIZACION-BICEP.md` | Guía de reutilización (sin desplegar) |
| Scripts | `scripts/validate-azure-prequisites.sh` | Validación dry-run |

**Validación:** 38/38 unit tests PASSED, 2 azure SKIPPED correctamente.

### Fase 4/5 — Arquitectura Operativa Foundry + RAG 🔜

**Dirección arquitectónica:**
- Microsoft Foundry como plano central de IA
- PostgreSQL como plano de conocimiento
- FastAPI como plano de orquestación RAG
- Container Apps como plano de ejecución
- Entra ID / Managed Identity como plano de identidad

**Bloqueantes actuales:**
- No hay deployment de embeddings confirmado en Modelo-IA-UR
- pgvector no habilitado en supersetdev
- BD rag_institucional no creada

---

## 📋 CONTEXTO ARQUITECTÓNICO APROBADO

### Decisión Central: Reutilizar PostgreSQL Existente

Este proyecto **NO crea infraestructura duplicada**.

#### PostgreSQL Existente
- **Servidor:** `supersetdev`
- **Resource Group:** RG-Datamining-SII2.0-Dev
- **Región:** East US 2
- **Versión:** PostgreSQL 16.14
- **SKU:** Standard_B1ms (Burstable)
- **Storage:** 32 GB
- **Status:** Ready
- **FQDN:** supersetdev.postgres.database.azure.com

#### Base de Datos Superset (INTOCABLE)
```
Servidor: supersetdev
BD: superset
Propósito: Aplicación Superset existente
Estado: PRODUCCIÓN
Modificación: PROHIBIDA
```

#### Nueva Base de Datos RAG (SEPARADA)
```
Servidor: supersetdev (REUTILIZADO)
BD: rag_institucional (NUEVA)
Propósito: RAG institucional Universidad del Rosario
Esquemas: documentos, embeddings, metadata
Extensiones: pgvector (pendiente de habilitar)
Estado: En planificación
```

### Azure Environment

- **Suscripción:** Sub-Tecnologia-Datamining (01bfad48-c092-4712-bc72-f141eb01a8d4)
- **Tenant:** Universidad del Rosario (ae525757-89ba-4d30-a2f7-49796ef8c604)
- **User:** analiticaur@urosario.edu.co
- **RG Destino:** RG-RAG-Urosario (eastus)

### Python Environment

- **Versión:** 3.12.10
- **.venv Location:** `D:\environments\rag-postgres-openai-python\.venv\`
- **Python Executable:** `D:\environments\rag-postgres-openai-python\.venv\Scripts\python.exe`
- **Proyecto:** `C:\rag-postgres-openai-python\rag-postgres-openai-python`
- **Nota:** Usar .venv existente, NO crear uno nuevo

---

## 🏗️ ARQUITECTURA OBJETIVO

```
┌──────────────────────────────────────────────────────┐
│         RG-RAG-Urosario (eastus)                    │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Container Apps Environment (CREAR)             │ │
│  │  │                                               │ │
│  │  └─ Container App (CREAR)                        │ │
│  │     │                                            │ │
│  │     ├─ Managed Identity RAG (CREAR)              │ │
│  │     │                                            │ │
│  │     └─ Env Variables                             │ │
│  │        ├ POSTGRES_HOST: supersetdev...           │ │
│  │        ├ POSTGRES_DATABASE: rag_institucional    │ │
│  │        ├ POSTGRES_USERNAME: <MI>                 │ │
│  │        └ AZURE_OPENAI_ENDPOINT: (Modelo-IA-UR)  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  [REUTILIZAR] Log Analytics, App Insights           │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  SHARED (RG-Datamining-SII2.0-Dev, eastus2)         │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  supersetdev PostgreSQL Flexible Server v16     │ │
│  │  │                                               │ │
│  │  ├─ DB: superset (EXISTENTE, INTACTA)           │ │
│  │  │                                               │ │
│  │  └─ DB: rag_institucional (NUEVA)                │ │
│  │     ├─ pgvector extension (PENDIENTE)            │ │
│  │     ├─ Schemas RAG                               │ │
│  │     └─ Tablas: documentos, chunks, embeddings    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  Shared Services:                                   │
│  ├─ Log Analytics workspace                         │
│  ├─ Application Insights                            │
│  ├─ Container Registry (acriaurdev)                 │
│  └─ Modelo-IA-UR AIServices S0 (EVALUAR)            │
└──────────────────────────────────────────────────────┘
```

---

## ✅ DECISIONES ARQUITECTÓNICAS APROBADAS

### 1. PostgreSQL
- ✅ **REUTILIZAR** `supersetdev` en East US 2
- ✅ **CREAR BD NUEVA** `rag_institucional` (separada)
- ✅ **NO modificar** BD `superset` existente
- ✅ **Justificación:** Ahorro de costos, reutilización de infraestructura

### 2. Log Analytics & Application Insights
- ✅ **REUTILIZAR** existentes si posible
- ✅ **Justificación:** Costo cero, monitoreo centralizado

### 3. Container Registry
- ✅ **REUTILIZAR** `acriaurdev` o crear nuevo en eastus si necesario
- ✅ **Justificación:** Compartir imagen RAG

### 4. Container Apps Environment
- ✅ **CREAR NUEVO** en RG-RAG-Urosario (eastus)
- ✅ **Justificación:** Aislamiento de aplicación RAG

### 5. Managed Identity
- ✅ **CREAR NUEVA** para RAG en RG-RAG-Urosario
- ✅ **Justificación:** Autenticación segura sin credenciales

### 6. Azure OpenAI / Modelo-IA-UR
- ⚠️ **EVALUAR** Modelo-IA-UR (AIServices S0)
- ⚠️ **DECISIÓN PENDIENTE:** Reutilizar vs. crear Azure OpenAI dedicado
- ⚠️ **Justificación:** Modelo-IA-UR es multiservicio, NO específicamente OpenAI

---

## 🔒 RESTRICCIONES Y PROHIBICIONES

### ESTA FASE (2): AUDITORÍA PURA
```
❌ NO ejecutar `azd up`
❌ NO ejecutar `az deployment group create`
❌ NO ejecutar `az postgres flexible-server parameter set`
❌ NO ejecutar `az postgres flexible-server db create`
❌ NO crear BD `rag_institucional` todavía
❌ NO habilitar pgvector todavía
❌ NO modificar PostgreSQL
❌ NO cambiar firewall rules
❌ NO cambiar RBAC
❌ NO crear Container Apps
❌ NO crear Managed Identities
❌ NO crear Azure OpenAI
❌ NO modificar BD `superset`
❌ NO cambiar Python version
❌ NO crear .venv nuevo

✅ SÍ: Azure CLI lectura (list, show, get-value)
✅ SÍ: Análisis de repositorio
✅ SÍ: Documentación y planificación
✅ SÍ: Creación de Skills y planes
```

### SEPARACIÓN SUPERSET / RAG
```
❌ NO tocar tablas de superset
❌ NO modificar schemas de superset
❌ NO cambiar usuarios/roles de superset
❌ NO ejecutar migraciones en superset
❌ NO habilitar extensiones que afecten superset
❌ NO cambiar performance de superset

✅ SÍ: BD independiente rag_institucional
✅ SÍ: Usuarios RBAC separados para RAG
✅ SÍ: Backups independientes
✅ SÍ: Monitoreo independiente
```

### pgvector
```
❌ NO habilitar sin aprobación explícita
❌ NO asumir que está disponible
❌ NO asumir que funciona sin validación
❌ NO modificar sin plan de rollback

⏳ REQUIERE:
1. Presentar: impacto, riesgo, rollback plan
2. Mostrar: comando exacto
3. Validar: efecto esperado
4. ESPERAR: aprobación explícita
5. EJECUTAR: solo con confirmación
```

---

## 📊 MATRIZ DE REUTILIZACIÓN

| Recurso | Template Crea | Ya Existe | Decisión | Costo Incremental |
|---------|---------------|-----------|----------|------------------|
| PostgreSQL | ✅ Sí | ✅ supersetdev | REUTILIZAR | $0 |
| Log Analytics | ✅ Sí | ✅ Múltiples | REUTILIZAR | $0 |
| App Insights | ✅ Sí | ✅ Múltiples | REUTILIZAR | $0 |
| Container Registry | ✅ Sí | ✅ acriaurdev | REUTILIZAR | $0 |
| Container Apps Env | ✅ Sí | ❌ No | CREAR | $20-30/mes |
| Managed Identity | ✅ Sí | ⚠️ Múltiples | CREAR NUEVA | $0 |
| BD rag_institucional | N/A | ❌ No | CREAR | $5-10/mes |
| pgvector | N/A | ⚠️ No habilitado | HABILITAR | $0 |
| Azure OpenAI | ✅ Sí (si flag) | ⚠️ Modelo-IA-UR | EVALUAR | $150-300/mes |
| Storage Account | ✅ Sí (si flag) | ❌ No | NO CREAR | $0 |
| AI Project | ✅ Sí (si flag) | ❌ No | NO CREAR | $0 |

**Costo Total Estimado:** $25-40 USD/mes (solo recurso nuevos imprescindibles)  
**Ahorro vs. Template:** $475-1460 USD/mes

---

## 🔀 PROTOCOLO DE CAMBIOS

Todo cambio a infraestructura requiere aprobación explícita.

### Paso 1: MOSTRAR
```
Archivo: ___
Línea: ___
Configuración actual: ___
Cambio propuesto: ___
```

### Paso 2: EXPLICAR
```
Impacto: ___
Riesgo: ___
Reversibilidad: ___
Plan de rollback: ___
Validación post-cambio: ___
```

### Paso 3: VALIDAR
```
Comando exacto: ___
Parámetros: ___
Efecto esperado: ___
Verificación: ___
```

### Paso 4: ESPERAR
```
⏳ Aprobación explícita
```

### Paso 5: EJECUTAR
```
✅ Con confirmación escrita
```

---

## 🎯 PATRÓN: NO DESTRUCTIVO

**Regla de Oro:** Si un cambio puede afectar `superset`, requiere aprobación.

**Preguntas antes de cualquier comando:**

1. ¿Afecta BD `superset`?
2. ¿Modifica extensiones del servidor?
3. ¿Cambia reglas de firewall?
4. ¿Afecta usuarios existentes?
5. ¿Es reversible?

Si alguna respuesta es "sí", MOSTRAR → EXPLICAR → VALIDAR → ESPERAR → EJECUTAR.

---

## 💰 RESTRICCIONES DE COSTOS

1. **No crear si existe reutilizable** — Prioridad máxima
2. **Minimizar recursos nuevos** — Solo lo necesario
3. **Documentar todo costo** — Transparencia
4. **Comparar vs. creación nueva** — Justificar
5. **Reutilización sostenible** — Largo plazo

**Objetivo:** Mantener costo operacional < $100 USD/mes

---

## 🔗 DEPENDENCIAS

RAG depende de:

```
Container App (web)
  ├─ Managed Identity RAG ← autenticación
  ├─ PostgreSQL supersetdev ← datos
  │   └─ BD rag_institucional ← almacenamiento RAG
  │       └─ pgvector ← búsqueda semántica
  ├─ Modelo-IA-UR / Azure OpenAI ← embeddings + chat
  │   └─ Validar modelos disponibles
  ├─ Log Analytics ← logging centralizado
  └─ Application Insights ← observabilidad
```

**Validación pre-deploy:**
- [ ] PostgreSQL accesible desde Container Apps
- [ ] pgvector funcional en rag_institucional
- [ ] Modelo-IA-UR tiene capacidad
- [ ] Managed Identity tiene RBAC en PostgreSQL
- [ ] Log Analytics conectado
- [ ] App Insights conectado

---

## 📋 CHECKLIST: REGLAS DE ORO

- [ ] ✅ AUDITAR antes de desplegar
- [ ] ✅ NO CREAR si REUTILIZABLE
- [ ] ✅ SEPARAR datos (superset vs. RAG)
- [ ] ✅ NO MODIFICAR superset
- [ ] ✅ SOLO LECTURA durante auditoría
- [ ] ✅ APROBACIÓN para cambios irreversibles
- [ ] ✅ DOCUMENTAR decisiones
- [ ] ✅ PLAN ROLLBACK para cada cambio
- [ ] ✅ VALIDAR región y dependencias
- [ ] ✅ NO DUPLICAR infraestructura
- [ ] ✅ PRIORIZAR costos
- [ ] ✅ PROTOCOLO NO-DESTRUCTIVO

---

## 📚 REFERENCIAS

- [AUDIT-FASE1-MATRIZ.md](../../AUDIT-FASE1-MATRIZ.md) — Análisis detallado
- [AUDIT-FASE1-RESUMEN.md](../../AUDIT-FASE1-RESUMEN.md) — Resumen ejecutivo
- [docs/LESSONS-LEARNED.md](../LESSONS-LEARNED.md) — Lecciones del proyecto
- [AGENTS.md](../../AGENTS.md) — Instrucciones para agentes
- [azure.yaml](../../azure.yaml) — Configuración azd
- [infra/main.bicep](../../infra/main.bicep) — Template (requiere reparación)

---

## 🚀 APLICABLE A

- Desarrollo iterativo del RAG
- Futuras integraciones
- Expansión de BD
- Escalado de Container Apps
- Auditorías de seguridad
- Optimización de costos
- Onboarding de equipos nuevas

---

**Skill:** rag-azure-urosario-architecture  
**Versión:** 1.0  
**Generado:** 2026-08-31  
**Status:** ACTIVO  
**Reutilizable:** Sí
