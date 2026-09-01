# FASE 2.5 — ALINEACIÓN DE CONFIGURACIÓN + LESSONS LEARNED

**Proyecto:** RAG Institucional Universidad del Rosario  
**Fecha:** 2026-08-31  
**Status:** ANÁLISIS COMPLETADO — ESPERANDO APROBACIÓN  
**Próximo:** FASE 3 — Validación de Azure AI + Preparación de Deploy

---

## 📋 RESUMEN EJECUTIVO

### ✅ Análisis Completado
- ✅ Inspección de `.env.sample` actual
- ✅ Análisis de código Python (postgres_engine.py, openai_clients.py, dependencies.py)
- ✅ Identificación de inconsistencias entre template y arquitectura real
- ✅ Creación de `.env.sample.aligned` (propuesta)
- ✅ Creación de Skill de Lecciones Aprendidas (configuración)

### 🔍 Hallazgos Críticos
1. ❌ `.env.sample` usa `POSTGRES_DATABASE=postgres` (INCORRECTO)
2. ❌ `.env.sample` usa `POSTGRES_HOST=localhost` (INCORRECTO para producción)
3. ⚠️ `.env.sample` asume deployments Azure OpenAI específicos sin verificación
4. ⚠️ `.env.sample` no documenta BD RAG separada (`rag_institucional`)
5. ⚠️ Código soporta autenticación Azure Identity, pero .env.sample no lo muestra

### ✅ Solución Propuesta
- Crear `.env.sample.aligned` con:
  - POSTGRES_DATABASE=rag_institucional
  - POSTGRES_HOST=supersetdev.postgres.database.azure.com
  - Placeholders para Azure OpenAI (sin asumir valores)
  - Documentación extensa sobre local vs. Azure
  - Ejemplos de múltiples backends (Azure, OpenAI.com, Ollama)
  - Advertencias sobre no guardar credenciales

---

## 1️⃣ INSPECCIÓN: .env.sample ACTUAL

### Estado Actual
```
# Use these values to connect to the local database from within the devcontainer
POSTGRES_HOST=localhost
POSTGRES_USERNAME=admin
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=postgres
POSTGRES_SSL=disable

OPENAI_CHAT_HOST=azure
OPENAI_EMBED_HOST=azure
AZURE_OPENAI_ENDPOINT=https://YOUR-AZURE-OPENAI-SERVICE-NAME.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.4
AZURE_OPENAI_CHAT_MODEL=gpt-5.4
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBED_MODEL=text-embedding-3-large
...
```

### Problemas Identificados

| Problema | Línea | Valor Actual | Valor Correcto | Impacto |
|----------|-------|--------------|-----------------|---------|
| BD incorrecta | `POSTGRES_DATABASE` | `postgres` | `rag_institucional` | CRÍTICO |
| Host local | `POSTGRES_HOST` | `localhost` | `supersetdev.postgres...` | ALTO |
| Asume deployments | `AZURE_OPENAI_CHAT_DEPLOYMENT` | `gpt-5.4` | `<CONFIRMAR>` | ALTO |
| Sin documentación | N/A | No documen BD RAG | Explicar separación | MEDIO |
| No muestra Azure ID | N/A | No menciona | Documentar opción | MEDIO |

---

## 2️⃣ ANÁLISIS: CÓDIGO PYTHON

### postgres_engine.py — Autenticación

**Detección automática Azure:**
```python
if host.endswith(".database.azure.com"):
    token_based_password = True
    # Usa Azure Identity
else:
    # Usa password
```

**Conclusión:** Código SOPORTA AMBOS (local + Azure)

### Flujo de Autenticación Azure

1. **Password-based** (para testing):
   ```
   POSTGRES_PASSWORD=<actual_password>
   ```

2. **Azure Developer CLI** (desarrollo local):
   ```python
   azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
   ```

3. **Managed Identity** (producción):
   ```python
   azure_credential = ManagedIdentityCredential()
   ```

**Conclusión:** Código FLEXIBLE pero .env.sample NO documenta esto

### openai_clients.py — Múltiples Backends

Código soporta:
1. **Azure OpenAI**
   ```
   OPENAI_CHAT_HOST=azure
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_KEY=... (opcional)
   # O Azure Identity si .key está vacío
   ```

2. **OpenAI.com**
   ```
   OPENAI_CHAT_HOST=openaicom
   OPENAICOM_KEY=...
   ```

3. **Ollama (local)**
   ```
   OPENAI_CHAT_HOST=ollama
   OLLAMA_ENDPOINT=...
   ```

**Conclusión:** .env.sample DEBERÍA documentar todas las opciones

### dependencies.py — Defaults

Código usa patterns:
```python
openai_embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL") or "text-embedding-3-large"
openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT") or "gpt-5.4"
```

**Problema:** Asume valores específicos que pueden NO existir en Modelo-IA-UR

**Conclusión:** Defaults son "hardcoded" en código, NO deben estar en .env.sample

---

## 3️⃣ IDENTIFICACIÓN: INCONSISTENCIAS

### Inconsistencia #1: POSTGRES_DATABASE

**Actual:**
```
POSTGRES_DATABASE=postgres
```

**Problema:**
- `postgres` es base de sistema
- Código será inutilizable sin tablas RAG
- No refleja arquitectura (rag_institucional separada)

**Alineación Requerida:**
```
POSTGRES_DATABASE=rag_institucional
```

**Por qué:** Arquitectura aprobada define BD separada de `superset`

---

### Inconsistencia #2: POSTGRES_HOST + POSTGRES_SSL

**Actual:**
```
POSTGRES_HOST=localhost
POSTGRES_SSL=disable
```

**Problema:**
- No refleja configuración productiva (supersetdev)
- Azure requiere SSL
- Confunde a desarrolladores sobre configuración real

**Alineación Requerida:**
```
# Opción A: Producción (Azure)
POSTGRES_HOST=supersetdev.postgres.database.azure.com
POSTGRES_SSL=require

# Opción B: Desarrollo local (devcontainer)
POSTGRES_HOST=localhost
POSTGRES_SSL=disable
```

**Por qué:** Necesita ejemplos de AMBOS contextos

---

### Inconsistencia #3: Azure OpenAI Deployments

**Actual:**
```
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.4
AZURE_OPENAI_CHAT_MODEL=gpt-5.4
```

**Problema:**
- `gpt-5.4` es un PLACEHOLDER del template original
- Modelo-IA-UR puede NO tener este deployment
- Ejecutar sin verificación causará error en producción

**Alineación Requerida:**
```
AZURE_OPENAI_CHAT_DEPLOYMENT=<CONFIRMAR_CHAT_DEPLOYMENT_NAME>
AZURE_OPENAI_CHAT_MODEL=<CONFIRMAR_CHAT_MODEL_NAME>
```

**Por qué:** Fuerza verificación manual antes de usar

---

### Inconsistencia #4: Documentación sobre BD Separada

**Actual:** 
- Sin mención de que `superset` es intocable
- Sin mención de que `rag_institucional` es nueva

**Alineación Requerida:**
```
# =====================================================
# PostgreSQL — EXISTING AZURE FLEXIBLE SERVER
# =====================================================
# Servidor: supersetdev.postgres.database.azure.com
# BD Superset (INTOCABLE): superset
# BD RAG (NUEVA): rag_institucional
#
# REGLA CRÍTICA:
# - NUNCA usar POSTGRES_DATABASE=superset
# - SIEMPRE usar POSTGRES_DATABASE=rag_institucional
# =====================================================
```

**Por qué:** Previene modificación accidental de datos productivos

---

### Inconsistencia #5: Autenticación Azure Identity

**Actual:**
- No menciona Azure Developer CLI
- No menciona Managed Identity
- Solo muestra AZURE_OPENAI_KEY

**Alineación Requerida:**
```
# Authentication options:
# 1. Password (dev/testing only)
POSTGRES_PASSWORD=<PASSWORD>

# 2. Azure Developer CLI (local dev - preferred)
POSTGRES_PASSWORD=  # Leave empty
AZURE_TENANT_ID=ae525757-89ba-4d30-a2f7-49796ef8c604
# Run: azd auth login

# 3. Managed Identity (production)
POSTGRES_PASSWORD=  # Leave empty
# Container App will use Managed Identity
```

**Por qué:** Documen las formas seguras de autenticación

---

## 4️⃣ PROPUESTA: .env.sample.aligned

### Ubicación
```
c:\rag-postgres-openai-python\rag-postgres-openai-python\.env.sample.aligned
```

### Cambios Principales

1. **PostgreSQL:**
   ```
   POSTGRES_HOST=supersetdev.postgres.database.azure.com (con comentario de local)
   POSTGRES_DATABASE=rag_institucional (con advertencia sobre superset)
   POSTGRES_SSL=require (con comentario de local)
   ```

2. **Azure OpenAI:**
   ```
   AZURE_OPENAI_ENDPOINT=<CONFIRMAR_...> (placeholder, no valor)
   AZURE_OPENAI_CHAT_DEPLOYMENT=<CONFIRMAR_...> (placeholder)
   AZURE_OPENAI_CHAT_MODEL=<CONFIRMAR_...> (placeholder)
   ```

3. **Documentación:**
   - Secciones extendidas por backend
   - Ejemplos comentados para local, Azure, Ollama
   - Advertencias sobre seguridad
   - Notas sobre autenticación

4. **Backends Alternativos:**
   - Azure OpenAI (configurado como default)
   - OpenAI.com (ejemplo comentado)
   - Ollama local (ejemplo comentado)

### Ventajas

| Ventaja | Beneficio |
|---------|-----------|
| BD correcta | Previene daños a superset |
| Placeholders | Obliga verificación manual |
| Documentación extensa | Guía a desarrolladores |
| Múltiples backends | Flexible para desarrollo |
| Sin credenciales | Seguridad mejorada |
| Ejemplos de ambos contextos | Útil para local y Azure |

---

## 5️⃣ LECCIONES APRENDIDAS DOCUMENTADAS

### Skill Creada
```
.cline/skills/rag-azure-urosario-configuration-lessons/SKILL.md
```

### 12 Lecciones Documentadas

1. ✅ PostgreSQL — Seleccionar BD correcta (rag_institucional)
2. ✅ POSTGRES_HOST — Local vs. Azure
3. ✅ Autenticación PostgreSQL — 3 opciones
4. ✅ Azure OpenAI — Verificar antes de asumir
5. ✅ PostgreSQL SSL — Requerido para Azure
6. ✅ No hardcodear credenciales en .env.sample
7. ✅ pgvector — No asumir que está habilitado
8. ✅ Variables de entorno — Soportar múltiples backends
9. ✅ Parametrizadas con defaults — No requerir todo
10. ✅ Tenant ID — Necesario para Azure Identity
11. ✅ Documentación en .env.sample — Crítica
12. ✅ Actualizar .env.sample — Cuando cambia arquitectura

### Matriz de Configuración (en Skill)

Tabla que documenta:
- Qué variables son requeridas vs. opcionales
- Diferencias entre local y Azure
- Si son placeholder o valores reales
- Notas importantes por variable

---

## 6️⃣ ARCHIVOS GENERADOS FASE 2.5

### 1. `.env.sample.aligned`
- Propuesta de .env.sample actualizado
- Alineado con arquitectura real
- Documentado extensivamente

### 2. Skill de Configuración
- `.cline/skills/rag-azure-urosario-configuration-lessons/SKILL.md`
- 12 lecciones aprendidas
- Matriz de configuración
- Checklist de alineación

### 3. Este Documento
- Análisis completo FASE 2.5
- Hallazgos y propuestas
- Riesgos y mitigaciones

---

## ⚠️ RIESGOS IDENTIFICADOS

### Riesgo 1: CRÍTICO — Usar POSTGRES_DATABASE=superset

| Aspecto | Evaluación |
|---------|-----------|
| **Probabilidad** | MEDIA (si accidental) |
| **Impacto** | CRÍTICO (destruye datos Superset) |
| **Reversibilidad** | PARCIAL (backups existentes) |
| **Mitigación** | Documentar AMPLIAMENTE en .env.sample |

**Plan de Mitigación:**
1. ✅ .env.sample.aligned documenta esto como ERROR
2. ✅ Skill contiene lección sobre este riesgo
3. ✅ Código podría validar en startup (futuro)

### Riesgo 2: ALTO — Azure OpenAI Deployments Inexistentes

| Aspecto | Evaluación |
|---------|-----------|
| **Probabilidad** | ALTA (sin verificación de Modelo-IA-UR) |
| **Impacto** | ALTO (RAG no funciona) |
| **Reversibilidad** | SÍ (reconfiguración) |
| **Mitigación** | Usar placeholders que oblig  verificación |

**Plan de Mitigación:**
1. ✅ .env.sample.aligned usa `<CONFIRMAR_...>`
2. ✅ Fase 3 requiere verificación de Modelo-IA-UR
3. ✅ Validación pre-deploy checklist (futura)

### Riesgo 3: MEDIO — Credenciales en Git

| Aspecto | Evaluación |
|---------|-----------|
| **Probabilidad** | BAJA (si se siguen reglas) |
| **Impacto** | CRÍTICO (compromiso de seguridad) |
| **Reversibilidad** | NO (Git history inmortal) |
| **Mitigación** | Documentar prohibición clara |

**Plan de Mitigación:**
1. ✅ .env.sample.aligned advierte NO guardar credenciales
2. ✅ Skill #6 documenta regla de oro
3. ✅ Comentarios en setup scripts (futuro)

### Riesgo 4: MEDIO — pgvector Aún No Habilitado

| Aspecto | Evaluación |
|---------|-----------|
| **Probabilidad** | MEDIA (si se olvida) |
| **Impacto** | ALTO (embeddings fallan) |
| **Reversibilidad** | SÍ (habilitar después) |
| **Mitigación** | Documentar estado actual |

**Plan de Mitigación:**
1. ✅ .env.sample.aligned documenta "NOT YET ENABLED"
2. ✅ Skill #7 explica por qué no asumir
3. ✅ Plan de habilitación en Fase 3

---

## 📊 CHECKLIST: ALINEACIÓN COMPLETADA

- [x] ✅ Inspección .env.sample actual completada
- [x] ✅ Análisis código Python completado
- [x] ✅ postgres_engine.py: autenticación verificada
- [x] ✅ openai_clients.py: backends múltiples verificados
- [x] ✅ dependencies.py: variables de entorno identificadas
- [x] ✅ Inconsistencias documentadas (5 encontradas)
- [x] ✅ .env.sample.aligned creado
- [x] ✅ Skill de lecciones aprendidas creado (12 lecciones)
- [x] ✅ Matriz de configuración documentada
- [x] ✅ Riesgos identificados y mitigaciones propuestas
- [x] ✅ Documentación de Fase 2.5 completada

---

## 🚀 PRÓXIMOS PASOS

### FASE 3: Validación Azure AI + Preparación de Deploy

**Tareas FASE 3:**
1. Verificar Modelo-IA-UR (endpoints, modelos, deployments)
2. Decidir: reutilizar Modelo-IA-UR vs. crear Azure OpenAI
3. Reparar template Bicep (NO crear PostgreSQL nuevo)
4. Adaptar scripts PostgreSQL para rag_institucional
5. Plan de habilitación pgvector (con aprobación)
6. Plan de RBAC seguro
7. Validación pre-deploy checklist

**Bloqueantes para FASE 3:**
- ⏳ Aprobación de .env.sample.aligned
- ⏳ Aprobación de cambios de configuración
- ⏳ Confirmación de que no habrá cambios a superset

---

## CAMBIOS PROPUESTOS — RESUMEN

### ❌ NO HACER (Nunca)
```
POSTGRES_DATABASE=superset        ← Destructivo
POSTGRES_PASSWORD=real_pass       ← Inseguro
AZURE_OPENAI_KEY=sk-...          ← Expone secretos
```

### ✅ CAMBIOS PROPUESTOS
```
.env.sample.aligned              ← Propuesta alineada
POSTGRES_DATABASE=rag_institucional
POSTGRES_HOST=supersetdev.postgres.database.azure.com
AZURE_OPENAI_ENDPOINT=<CONFIRMAR>  ← Placeholder
SKILL.md (configuración)         ← 12 lecciones
```

### 📋 VALIDACIONES REQUERIDAS
```
- [ ] ¿Aprueba .env.sample.aligned?
- [ ] ¿Aprueba cambios de configuración?
- [ ] ¿Confirma que superset NO será modificado?
- [ ] ¿Listo para FASE 3?
```

---

## CONCLUSIÓN

**FASE 2.5 COMPLETADA — ANÁLISIS DE CONFIGURACIÓN + LECCIONES APRENDIDAS**

✅ Análisis completo del repositorio y configuración  
✅ Inconsistencias identificadas y documentadas  
✅ Propuesta de .env.sample.aligned creada  
✅ Skill de lecciones aprendidas documentada  
✅ Riesgos identificados y mitigaciones propuestas  
✅ Listo para Fase 3 después de aprobación  

**Estado:** 🟢 ESPERANDO APROBACIÓN DE CAMBIOS DE CONFIGURACIÓN

---

**Documento:** FASE 2.5 Analysis — Configuration Alignment  
**Versión:** 1.0  
**Generado:** 2026-08-31  
**Status:** COMPLETADA — ESPERANDO APROBACIÓN  
**Próxima Fase:** FASE 3 — Validación Azure AI + Preparación de Deploy
