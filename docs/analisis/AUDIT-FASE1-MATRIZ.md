# AUDITORÍA FASE 1 — MATRIZ DE DECISIÓN DE RECURSOS

**Fecha:** 2026-08-31  
**Suscripción:** Sub-Tecnologia-Datamining  
**Tenant:** Universidad del Rosario  
**RG Destino:** RG-RAG-Urosario (eastus)  
**Zona objetivo:** eastus (mismo que RG destino)

---

## MATRIZ: RECURSO | TEMPLATE CREA | YA EXISTE | REUTILIZABLE | NUEVO NECESARIO | COSTO/IMPACTO

| Nº | RECURSO | TEMPLATE CREA | YA EXISTE | REUTILIZABLE | DECISIÓN | COSTO/IMPACTO | NOTAS |
|---|---------|---------------|-----------|--------------|----------|---|---------|
| 1 | **PostgreSQL Flexible Server** | ✅ SÍ | ✅ SÍ (supersetdev) | ⚠️ PARCIAL | 🔴 REUTILIZAR+NUEVA BD | BAJO | BD independiente `rag_institucional` en supersetdev. NO modificar tablas existentes. pgvector debe habilitarse. |
| 2 | **BD PostgreSQL** | ✅ SÍ (postgres) | ✅ PARCIAL (superset) | ✅ SÍ | 🟢 CREAR NUEVA | BAJO | Crear BD `rag_institucional` en supersetdev. |
| 3 | **Extensión pgvector** | ❓ N/A | ⚠️ PARCIAL | ✅ SÍ | 🟢 HABILITAR | BAJO | Habilitar en `azure.extensions` del servidor supersetdev. |
| 4 | **Container Registry** | ✅ SÍ | ✅ SÍ | ✅ SÍ | 🟢 REUTILIZAR | MUY BAJO | Reutilizar `acriaurdev` (RG-Datamining-SII2.0-Dev, eastus2) O crear nuevo en RG-RAG-Urosario (eastus). |
| 5 | **Container Apps Environment** | ✅ SÍ | ❌ NO | ❌ NO | 🟡 CREAR NUEVO | MEDIO | Nuevo en RG-RAG-Urosario (eastus). |
| 6 | **Container App (Web)** | ✅ SÍ | ❌ NO | ❌ NO | 🟡 CREAR NUEVO | BAJO-MEDIO | Nuevo en RG-RAG-Urosario. |
| 7 | **Log Analytics Workspace** | ✅ SÍ | ✅ SÍ | ✅ SÍ | 🟢 REUTILIZAR | MUY BAJO | Reutilizar `workspace-EUS-01bfad48-*` en RG-Datamining-SII2.0-Dev (eastus). |
| 8 | **Application Insights** | ✅ SÍ | ✅ SÍ | ✅ SÍ | 🟢 REUTILIZAR | MUY BAJO | Reutilizar `AI-AS-SII2-Back` en RG-Datamining-SII2.0 O crear nuevo. |
| 9 | **Azure OpenAI** | ✅ SÍ (si flag=true) | ⚠️ PARCIAL | ❓ EVALUACIÓN | 🔴 DECISIÓN PENDIENTE | ALTO | `Modelo-IA-UR` es AIServices S0 multi-servicio, NO específicamente OpenAI. **Evaluar si suficiente o crear OpenAI dedicado.** |
| 10 | **Managed Identity** | ✅ SÍ | ✅ SÍ | ⚠️ PARCIAL | 🟡 CREAR NUEVA | BAJO | Crear Managed Identity para RAG en RG-RAG-Urosario. |
| 11 | **Resource Group** | ✅ SÍ | ✅ SÍ (RG-RAG-Urosario) | ✅ SÍ | 🟢 REUTILIZAR | CERO | RG-RAG-Urosario YA EXISTE en eastus. |
| 12 | **Storage Account** | ✅ SÍ (si USE_AI_PROJECT=true) | ❌ NO | ❌ NO | 🟡 CREAR SI AI_PROJECT | BAJO-MEDIO | Solo si se usa AI Project (default: false). Recomendación: NO crear si no es necesario. |
| 13 | **AI Project** | ✅ SÍ (si USE_AI_PROJECT=true) | ❌ NO | ❌ NO | 🟡 CREAR SI NECESARIO | BAJO | Solo si se usa (default: false). Recomendación: NO crear inicialmente. |

---

## RESUMEN EJECUTIVO

### ✅ REUTILIZAR (Costo 0, bajo impacto):
1. **PostgreSQL supersetdev** + nueva BD `rag_institucional`
2. **Log Analytics Workspace** existente
3. **Application Insights** existente (o crear nueva en RAG-RG)
4. **Container Registry** existente `acriaurdev` o nuevo
5. **RG-RAG-Urosario** (YA EXISTE)

### 🟡 CREAR NUEVO (Costo bajo-medio):
1. **Container Apps Environment** en RG-RAG-Urosario
2. **Container App** en RG-RAG-Urosario
3. **Managed Identity** en RG-RAG-Urosario
4. **Habilitar pgvector** en supersetdev

### 🔴 DECISIÓN PENDIENTE (Alto impacto):
1. **Azure OpenAI** - Evaluar si `Modelo-IA-UR` (AIServices S0) es suficiente o crear Azure OpenAI dedicado
   - Si reutiliza AIServices S0: Costo BAJO
   - Si crea Azure OpenAI nuevo: Costo ALTO (~$0.15-$2.00/hora según modelos)

### ❌ NO CREAR (Ahorro de costos):
1. **PostgreSQL NUEVO** (reutiliza supersetdev)
2. **Storage Account** (no es imprescindible)
3. **AI Project** (no es imprescindible)

---

## RECOMENDACIONES ARQUITECTÓNICAS

### OPCIÓN A (RECOMENDADA): Máximo Reutilización
```
RG-RAG-Urosario
├── Container Apps Environment (NUEVO)
├── Container App (NUEVO)
├── Managed Identity (NUEVO)
├── Application Insights (REUTILIZADO o NUEVO pequeño)
└── [USA] supersetdev.rag_institucional BD (NUEVA BD en servidor existente)
    └── pgvector (HABILITADO)

Recursos Compartidos:
├── supersetdev PostgreSQL (COMPARTIDO)
├── Log Analytics (REUTILIZADO)
├── Container Registry (REUTILIZADO acriaurdev)
└── Modelo-IA-UR AIServices S0 (REUTILIZADO)
    ⚠️ Si insuficiente: crear Azure OpenAI
```

**Costo Mensual Estimado:** $50-100 USD (solo Container Apps + PostgreSQL incremental)

### OPCIÓN B: Segregación Completa (No Recomendada)
Crear todos los recursos nuevos (PostgreSQL, OpenAI, Log Analytics, etc.)

**Costo Mensual Estimado:** $500-1500 USD

**Diferencia:** +$400-1400 USD/mes por duplicación innecesaria

---

## DECISIONES ARQUITECTÓNICAS FINALES RECOMENDADAS

### ✅ HACER:
1. ✅ **Reutilizar supersetdev como servidor PostgreSQL**
   - Crear BD independiente `rag_institucional`
   - No interfiere con `superset` existente
   - Ahorro: $50-100 USD/mes
   - Riesgo: BAJO (con separación de BD)
   - Firewall: Ya permite Azure Services

2. ✅ **Habilitar pgvector en supersetdev**
   - Parámetro `azure.extensions += vector`
   - Impacto: MUY BAJO
   - Precedentes: pg_cron, pg_stat_statements ya habilitados

3. ✅ **Reutilizar Log Analytics existente**
   - workspace-EUS-01bfad48-* disponible
   - Ahorro: $0 (ya facturable)

4. ✅ **Reutilizar Container Registry acriaurdev**
   - Ya en eastus2 con RG-Datamining-SII2.0-Dev
   - Alternativa: crear nuevo en RG-RAG-Urosario (eastus)
   - Recomendación: Reutilizar si posible

5. ✅ **Crear Container Apps Environment NUEVO en RG-RAG-Urosario**
   - Ubicación: eastus (mismo que RG)
   - Costo: ~$20-30 USD/mes

6. ✅ **Crear Managed Identity NUEVA para RAG**
   - Ubicación: RG-RAG-Urosario
   - Costo: $0 (incluida con servicios Azure)

7. ⚠️ **Evaluar Modelo-IA-UR (AIServices S0)**
   - Actual: AIServices multi-servicio S0
   - Limitaciones: Verificar capacidad, modelos disponibles, throughput
   - Decisión: Reutilizar si suficiente, crear Azure OpenAI si necesario
   - Impacto: CRÍTICO para RAG (embeddings + chat)

### ❌ NO HACER:
1. ❌ **NO crear PostgreSQL nuevo** (ahorra $50-100/mes)
2. ❌ **NO crear Log Analytics nuevo** (ahorra $20-50/mes)
3. ❌ **NO crear Storage Account** (ahorra $10-20/mes)
4. ❌ **NO crear AI Project** (no es esencial)

---

## MATRIZ DE RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|-----------|
| Superset y RAG comparten PostgreSQL | MEDIA | ALTO | Bases de datos separadas. Firewall dedicado. Monitoreo de conexiones. |
| pgvector causa degradación supersetdev | BAJA | MEDIO | Extensión es estable. Probar en pre-prod primero. |
| AIServices S0 insuficiente | MEDIA | ALTO | Crear Azure OpenAI si se detecta limitación. |
| Container Registry en eastus2 vs eastus | BAJA | BAJO | Latencia menor si nuevo registro en eastus. |
| Identidad compartida (Managed Identity) | BAJA | BAJO | Crear identidad separada para RAG. |

---

## PRÓXIMOS PASOS (FASE 2)

Una vez aprobada esta matriz, procederemos a:

1. **Verificar capacidad Azure OpenAI / Modelo-IA-UR**
   - Endpoints disponibles
   - Modelos desplegados (chat, embeddings)
   - Throughput
   - Decisión: Reutilizar o crear nuevo

2. **Plantilla Bicep Modificada**
   - Referencia a PostgreSQL existente en lugar de crear nuevo
   - Habilitar pgvector en parámetros
   - Reutilizar Log Analytics, App Insights, Container Registry
   - Crear solo: Container Apps, Managed Identity, Application Settings

3. **Scripts de Deploy Automatizado**
   - PowerShell para crear BD `rag_institucional`
   - Script para habilitar pgvector
   - Configuración RBAC (Managed Identity → PostgreSQL)

4. **Validación Pre-Deploy**
   - Verificar firewall rules (si es necesario)
   - Probar conectividad supersetdev desde Container Apps
   - Probar pgvector en base RAG

---

## CONCLUSIÓN

**Se recomienda OPCIÓN A: Máxima Reutilización**

✅ **Ahorro mensual:** ~$400-500 USD vs. crear nuevos recursos  
✅ **Riesgos:** Bajos con separación de BD  
✅ **Complejidad:** Media (integración con servidores existentes)  
✅ **Mantenimiento:** Centralizado en supersetdev  

**Estado:** 🟢 LISTO PARA APROBACIÓN

---

*Documento generado por Auditoría Fase 1*  
*Arquitecto: GitHub Copilot (Claude Haiku 4.5)*  
*Fecha: 2026-08-31*
