# PROPUESTA DE CAMBIOS — .env.sample ALINEACIÓN

**Proyecto:** RAG Institucional Universidad del Rosario  
**Fecha:** 2026-08-31  
**Documento:** Propuesta de cambios basada en MATRIZ-VARIABLES-ENTORNO.md  
**Status:** LISTO PARA IMPLEMENTACIÓN (pendiente aprobación)  

---

## RESUMEN EJECUTIVO

Basándome en la matriz de 31 variables de entorno, se proponen los siguientes cambios al archivo `.env.sample`:

### Cambios Críticos (DEBEN implementarse)
1. ✅ POSTGRES_DATABASE: `postgres` → `rag_institucional`
2. ✅ POSTGRES_SSL: `disable` → `require` (cuando es Azure)
3. ✅ AZURE_TENANT_ID: vacío → `ae525757-89ba-4d30-a2f7-49796ef8c604`

### Cambios de Placeholder (Por verificación en Fase 3)
4. ⚠️ AZURE_OPENAI_ENDPOINT: `https://YOUR-...` → `<CONFIRMAR_EN_AZURE>`
5. ⚠️ AZURE_OPENAI_CHAT_DEPLOYMENT: `gpt-5.4` → `<CONFIRMAR_EN_AZURE>`
6. ⚠️ AZURE_OPENAI_CHAT_MODEL: `gpt-5.4` → `<CONFIRMAR_EN_AZURE>`
7. ⚠️ AZURE_OPENAI_EMBED_DEPLOYMENT: `text-embedding-3-large` → `<CONFIRMAR_EN_AZURE>`
8. ⚠️ AZURE_OPENAI_EMBED_MODEL: `text-embedding-3-large` → `<CONFIRMAR_EN_AZURE>`

### Cambios de Documentación
9. 📝 Agregar sección: "NOTAS SOBRE MODELO-IA-UR"
10. 📝 Agregar sección: "DESARROLLO LOCAL vs AZURE"
11. 📝 Documentar NUNCA usar POSTGRES_DATABASE=superset
12. 📝 Documentar NUNCA guardar credenciales en .env

---

## CAMBIO 1: POSTGRES_DATABASE (CRÍTICO)

### Ubicación
Línea 5 del `.env.sample` actual

### Actual
```ini
POSTGRES_DATABASE=postgres
```

### Propuesto
```ini
# Base de datos lógica del RAG Institucional UR.
# ⚠️ CRÍTICO: NUNCA usar "superset" (pertenece a Superset, DB intacta)
# ⚠️ CRÍTICO: NUNCA usar "postgres" (BD de sistema)
# ✅ SIEMPRE usar "rag_institucional" (BD exclusiva del RAG)
POSTGRES_DATABASE=rag_institucional
```

### Justificación
- Cambio OBLIGATORIO
- Actual (`postgres`) usa base de sistema
- Propuesto (`rag_institucional`) aísla datos RAG
- Previene modificación accidental de Superset
- Aplica a AMBOS: desarrollo local y Azure

### Riesgo de no cambiar
⛔ **CRÍTICO:** El código creará tablas en BD `postgres` del sistema,
lo que podría romper PostgreSQL o interferir con otras aplicaciones.

---

## CAMBIO 2: POSTGRES_SSL (CONDICIONAL)

### Ubicación
Línea 7 del `.env.sample` actual

### Actual
```ini
POSTGRES_SSL=disable
```

### Propuesto (Desarrollo Local)
```ini
# Para desarrollo local con PostgreSQL en Docker/devcontainer
# PostgreSQL local en devcontainer permite sin SSL:
POSTGRES_SSL=disable
```

### Propuesto (Azure)
```ini
# Para ejecución contra Azure PostgreSQL Flexible Server
# Azure REQUIERE SSL/TLS obligatoriamente:
POSTGRES_SSL=require
```

### Justificación
- Local: PostgreSQL en Docker puede funcionar sin SSL
- Azure: PostgreSQL Flexible Server requiere SSL
- Código auto-detecta contexto por `if host.endswith(".database.azure.com")`

### Riesgo de no cambiar
⚠️ **ALTO:** Conexión a Azure PostgreSQL fallará si POSTGRES_SSL=disable
porque Azure rechaza conexiones no-SSL.

---

## CAMBIO 3: POSTGRES_USERNAME (VERIFICACIÓN)

### Ubicación
Línea 3 del `.env.sample` actual

### Actual
```ini
POSTGRES_USERNAME=admin
```

### Nota
- Para desarrollo local: `admin` es correcto (user por defecto en devcontainer)
- Para Azure: usuario de BD RAG debe verificarse en Fase 3
- Probablemente sea un usuario específico, no `admin`

### Propuesto
**NO CAMBIAR TODAVÍA** (mantener `admin` con documentación)

---

## CAMBIO 4: AZURE_TENANT_ID (IMPORTANTE)

### Ubicación
Línea 23 del `.env.sample` actual

### Actual
```ini
AZURE_TENANT_ID=
```

### Propuesto
```ini
# Tenant ID de Universidad del Rosario
# Necesario para autenticación Azure Identity con PostgreSQL
# Este valor NO es secreto (es identificador público de la org)
AZURE_TENANT_ID=ae525757-89ba-4d30-a2f7-49796ef8c604
```

### Justificación
- Tenant ID necesario para `AzureDeveloperCliCredential`
- NO es secreto (es info pública de organización)
- Mejora developer experience (evita errores de autenticación)
- Aplicable a desarrollo local con `azd auth login`

### Riesgo de no cambiar
⚠️ **MEDIO:** Sin tenant ID, autenticación Azure Identity puede ser ambigua
si usuario tiene múltiples tenants.

---

## CAMBIO 5-8: AZURE OPENAI DEPLOYMENTS (PLACEHOLDERS)

### Ubicación
Líneas 14-18 del `.env.sample` actual

### Actual
```ini
AZURE_OPENAI_ENDPOINT=https://YOUR-AZURE-OPENAI-SERVICE-NAME.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.4
AZURE_OPENAI_CHAT_MODEL=gpt-5.4
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-large
```

### Propuesto
```ini
# ⚠️ VERIFICACIÓN REQUERIDA EN FASE 3:
# Modelo-IA-UR es un recurso Azure AI Services (multiservicio).
# Verificar que contiene deployments de chat Y embeddings.
# NO asumir valores sin verificación.
#
# Valores actuales (gpt-5.4, text-embedding-3-large) son PLACEHOLDERS
# y pueden NO existir en Modelo-IA-UR.
#
# Fase 3 debe:
# 1. Verificar endpoint real de Modelo-IA-UR
# 2. Listar deployments disponibles
# 3. Confirmar nombres de chat + embeddings
# 4. Confirmar dimensiones de embeddings
# 5. Decidir: reutilizar Modelo-IA-UR vs crear Azure OpenAI dedicado

AZURE_OPENAI_ENDPOINT=<CONFIRMAR_EN_AZURE>
AZURE_OPENAI_CHAT_DEPLOYMENT=<CONFIRMAR_EN_AZURE>
AZURE_OPENAI_CHAT_MODEL=<CONFIRMAR_EN_AZURE>
AZURE_OPENAI_EMBED_DEPLOYMENT=<CONFIRMAR_EN_AZURE>
AZURE_OPENAI_EMBED_MODEL=<CONFIRMAR_EN_AZURE>
```

### Justificación
- Actual contiene placeholders sin verificación real
- Ejecutar con valores asumidos causará errores en runtime
- Modelo-IA-UR es multiservicio, requiere verificación
- Placeholders `<CONFIRMAR_EN_AZURE>` obliga verificación manual

### Riesgo de no cambiar
⛔ **CRÍTICO:** Código intentará usar `gpt-5.4` y `text-embedding-3-large`
si existen en Modelo-IA-UR. Si NO existen, las llamadas a OpenAI fallarán
en runtime con error de deployment no encontrado.

---

## CAMBIO 9: AZURE_OPENAI_KEY (SEGURIDAD)

### Ubicación
Línea 24 del `.env.sample` actual

### Actual
```ini
AZURE_OPENAI_KEY=
```

### Propuesto (Mantener, con documentación mejorada)
```ini
# SEGURIDAD: Autenticación para Azure OpenAI
#
# Opciones disponibles (en orden de preferencia):
#
# 1. RECOMENDADO — Azure Identity (Managed Identity en Azure)
#    - En desarrollo local: `azd auth login` con AzureDeveloperCliCredential
#    - En Container Apps: Managed Identity automático
#    - NUNCA guardar AZURE_OPENAI_KEY en .env en este caso
#    - Dejar vacío:
#      AZURE_OPENAI_KEY=
#
# 2. TESTING SOLAMENTE — API Key-based authentication
#    - NUNCA usar en producción
#    - NUNCA commitear keys reales en Git
#    - Para testing local, usar Azure Key Vault en lugar de .env
#    - Si usa: AZURE_OPENAI_KEY=sk-proj-xxxxxxx
#
# Para desarrollo local preferir opción 1 (Azure Identity)

AZURE_OPENAI_KEY=
```

### Justificación
- Mantener vacío porque código soporta Azure Identity
- Documentar que NUNCA guardar keys reales en .env
- Documentar preferencia por Azure Identity
- Advertencia sobre seguridad

---

## CAMBIOS DE ESTRUCTURA Y DOCUMENTACIÓN

### Nueva Sección: "DESARROLLO LOCAL vs AZURE"

Agregar sección con instrucciones claras:

```ini
# =====================================================================
# DESARROLLO LOCAL vs AZURE — CONFIGURACIÓN
# =====================================================================
#
# Para DESARROLLO LOCAL (Docker + devcontainer):
#   POSTGRES_HOST=localhost
#   POSTGRES_DATABASE=rag_institucional
#   POSTGRES_SSL=disable
#   POSTGRES_PASSWORD=postgres
#   OPENAI_CHAT_HOST=azure | openaicom | ollama
#   Ejecutar: azd auth login (si usa Azure)
#
# Para EJECUCIÓN EN AZURE (Container Apps):
#   POSTGRES_HOST=supersetdev.postgres.database.azure.com
#   POSTGRES_DATABASE=rag_institucional
#   POSTGRES_SSL=require
#   POSTGRES_PASSWORD=  (usar Managed Identity)
#   OPENAI_CHAT_HOST=azure
#   AZURE_OPENAI_ENDPOINT=<verificado en Fase 3>
#   AZURE_OPENAI_CHAT_DEPLOYMENT=<verificado en Fase 3>
#   AZURE_OPENAI_EMBED_DEPLOYMENT=<verificado en Fase 3>
#   Managed Identity automático en Container Apps
#
# =====================================================================
```

### Nueva Sección: "MODELO-IA-UR — VERIFICACIÓN REQUERIDA"

```ini
# =====================================================================
# MODELO-IA-UR — VERIFICACIÓN REQUERIDA FASE 3
# =====================================================================
#
# Modelo-IA-UR es un recurso Azure AI Services (multiservicio).
#
# DIFERENCIA IMPORTANTE:
# - Azure OpenAI dedicado: Servicio específico solo para OpenAI
# - Azure AI Services: Servicio multiservicio que PUEDE contener OpenAI
#
# Antes de usar Modelo-IA-UR, VERIFICAR:
# 1. ¿Tiene deployment de chat model (ej: gpt-4, gpt-3.5-turbo)?
# 2. ¿Tiene deployment de embeddings model (ej: text-embedding-3-large)?
# 3. ¿Cuál es el endpoint URL?
# 4. ¿Cuál es el nombre del deployment?
# 5. ¿Cuál es el modelo asociado a cada deployment?
#
# Ejecutar en Azure CLI:
#   az cognitiveservices account show \
#     --resource-group RG-Datamining-IA-UR \
#     --name Modelo-IA-UR \
#     --query "kind,properties"
#
# DECISIÓN ARQUITECTÓNICA PENDIENTE (Fase 3):
# - OPCIÓN A: Reutilizar Modelo-IA-UR (si tiene chat + embeddings)
# - OPCIÓN B: Crear Azure OpenAI dedicado (si Modelo-IA-UR insuficiente)
#
# =====================================================================
```

---

## ESTRUCTURA PROPUESTA DE NUEVO .env.sample

```
1. Encabezado explicativo
2. Sección: PostgreSQL (con examples local + Azure)
3. Sección: Azure OpenAI (con placeholders y documentación)
4. Sección: Autenticación Azure
5. Sección: Desarrollo Local vs Azure
6. Sección: Modelo-IA-UR — Verificación
7. Sección: Alternativas (OpenAI.com, Ollama)
8. Sección: Aplicación (logging, monitoring)
9. Sección: Notas de Seguridad
10. Sección: Referencias (documentación, skills)
```

---

## VALIDACIONES A REALIZAR DESPUÉS DE CAMBIO

1. ✅ Verificar que `.env.sample` no contiene credenciales reales
2. ✅ Verificar que `.env.sample` documenta claramente local vs Azure
3. ✅ Verificar que placeholders `<CONFIRMAR_EN_AZURE>` están presente
4. ✅ Verificar que POSTGRES_DATABASE siempre es `rag_institucional`
5. ✅ Verificar que no existe mención de POSTGRES_DATABASE=superset
6. ✅ Verificar que AZURE_TENANT_ID tiene valor correcto
7. ✅ Verificar que AZURE_OPENAI_KEY está vacío (recomienda Azure Identity)

---

## RIESGOS IDENTIFICADOS

### Riesgo 1: Cambiar POSTGRES_DATABASE sin ejecutar setup
- **Probabilidad:** Media (si alguien copia .env.sample)
- **Impacto:** Alto (tablas se crean en BD equivocada)
- **Mitigación:** Documentación clara + validación en startup

### Riesgo 2: Azure deployments no confirmados
- **Probabilidad:** Alta (sin verificación Fase 3)
- **Impacto:** Alto (RAG no funciona)
- **Mitigación:** Placeholders oblig verificación manual

### Riesgo 3: POSTGRES_SSL=disable en Azure
- **Probabilidad:** Baja (si se sigue documentación)
- **Impacto:** Alto (conexión rechazada)
- **Mitigación:** Ejemplos claros para cada contexto

### Riesgo 4: Credenciales en Git
- **Probabilidad:** Baja (si se siguen reglas)
- **Impacto:** Crítico (compromiso seguridad)
- **Mitigación:** Documentación de NUNCA guardar keys

---

## CHECKLIST PRE-IMPLEMENTACIÓN

- [ ] ¿Matriz de variables revisada?
- [ ] ¿Cambios propuestos aprobados?
- [ ] ¿Se entiende la estructura nuevo .env.sample?
- [ ] ¿Se conocen los placeholders `<CONFIRMAR_EN_AZURE>`?
- [ ] ¿Se entiende diferencia local vs Azure?
- [ ] ¿Se entiende que POSTGRES_DATABASE debe ser rag_institucional?

---

## PRÓXIMOS PASOS

1. ✅ Mostrar matriz de variables (hecho)
2. ✅ Mostrar propuestas de cambios (este documento)
3. ⏳ IMPLEMENTAR cambios en `.env.sample`
4. ⏳ Mostrar diff completo
5. ⏳ Validaciones no destructivas
6. ⏳ Proponer commit message
7. ⏳ ESPERAR APROBACIÓN PARA PUSH

---

**Propuesta:** Completa y lista para implementación  
**Versión:** 1.0  
**Status:** LISTO PARA APROBACIÓN  
**Generado:** 2026-08-31
