# MATRIZ DE VARIABLES DE ENTORNO — ALINEACIÓN .env.sample

**Proyecto:** RAG Institucional Universidad del Rosario  
**Fecha:** 2026-08-31  
**Propósito:** Matriz de variables antes/después para alineación con arquitectura real  
**Contexto:** PostgreSQL Azure (supersetdev) + BD rag_institucional  

---

## LEYENDA

- **VAR:** Nombre de variable de entorno
- **ARCHIVO:** Dónde se usa en el código
- **TIPO:** Uso type (Obligatoria / Opcional / Condicional)
- **ACTUAL:** Valor en .env.sample actual
- **PROPUESTO (Local):** Para desarrollo local con PostgreSQL local
- **PROPUESTO (Azure):** Para ejecución contra PostgreSQL Azure
- **MOTIVO:** Razón del cambio

---

## SECCIÓN 1: POSTGRESQL — VARIABLES CRÍTICAS

### Variable 1: POSTGRES_HOST

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_HOST |
| **Archivo** | postgres_engine.py línea 57, 61 |
| **Tipo** | Obligatoria |
| **Actual** | `localhost` |
| **Propuesto (Local)** | `localhost` |
| **Propuesto (Azure)** | `supersetdev.postgres.database.azure.com` |
| **Motivo** | Auto-detecta si es Azure por suffix ".database.azure.com". Actual está optimizado para devcontainer/local. Azure requiere FQDN real. |
| **Código** | `if host.endswith(".database.azure.com"):` → Activa autenticación Azure |

**Decisión:** Proponer EJEMPLO comentado de ambas opciones

---

### Variable 2: POSTGRES_USERNAME

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_USERNAME |
| **Archivo** | postgres_engine.py línea 62 |
| **Tipo** | Obligatoria |
| **Actual** | `admin` |
| **Propuesto (Local)** | `admin` |
| **Propuesto (Azure)** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | Para Azure, el usuario de BD RAG debe verificarse en supersetdev. No es `admin` (ese es el rol de sistema). |
| **Nota** | PostgreSQL Azure requiere usuario específico con permisos limitados a rag_institucional |

**Decisión:** Usar placeholder + documentación

---

### Variable 3: POSTGRES_DATABASE

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_DATABASE |
| **Archivo** | postgres_engine.py línea 63 |
| **Tipo** | Obligatoria ⚠️ CRÍTICA |
| **Actual** | `postgres` |
| **Propuesto (Local)** | `rag_institucional` |
| **Propuesto (Azure)** | `rag_institucional` |
| **Motivo** | ⛔ CRÍTICO: Actual usa BD sistema "postgres". Debe cambiar SIEMPRE a "rag_institucional" para AMBOS contextos. NUNCA debe ser "superset". |
| **Riesgo** | Usar "postgres" o "superset" causa pérdida de datos o interferencia con Superset |

**Decisión:** ✅ CAMBIAR OBLIGATORIAMENTE a `rag_institucional`

---

### Variable 4: POSTGRES_PASSWORD

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_PASSWORD |
| **Archivo** | postgres_engine.py línea 64 |
| **Tipo** | Opcional (vacío para Azure Identity) |
| **Actual** | `postgres` |
| **Propuesto (Local)** | `postgres` (para devcontainer) |
| **Propuesto (Azure)** | vacío `""` (usar Azure Identity/Managed Identity) |
| **Motivo** | Local: devcontainer usa contraseña. Azure: NUNCA guardar contraseñas en .env, usar Azure Identity. |
| **Seguridad** | Credential en .env = riesgo crítico |

**Decisión:** Documentar diferencia local vs Azure + ADVERTENCIA

---

### Variable 5: POSTGRES_SSL

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_SSL |
| **Archivo** | postgres_engine.py línea 65 |
| **Tipo** | Opcional |
| **Actual** | `disable` |
| **Propuesto (Local)** | `disable` (localhost no requiere SSL) |
| **Propuesto (Azure)** | `require` (Azure requiere SSL obligatoriamente) |
| **Motivo** | Azure PostgreSQL enforces SSL. Local devcontainer puede ser inseguro para desarrollo. |
| **Regla** | Si `.database.azure.com` en HOST → SIEMPRE `require` |

**Decisión:** ✅ CAMBIAR a `require` para Azure, documentar local

---

### Variable 6: POSTGRES_PORT

| Aspecto | Detalle |
|---------|---------|
| **Variable** | POSTGRES_PORT |
| **Archivo** | NO USADO en código actual |
| **Tipo** | Opcional (code doesn't reference it) |
| **Actual** | NO EXISTE en .env.sample |
| **Propuesto** | Documentar solo (5432 es default) |
| **Motivo** | Código no lo usa, pero útil para documentación |

**Decisión:** Documentar como reference solamente

---

## SECCIÓN 2: OPENAI — VARIABLES DE BACKEND

### Variable 7: OPENAI_CHAT_HOST

| Aspecto | Detalle |
|---------|---------|
| **Variable** | OPENAI_CHAT_HOST |
| **Archivo** | dependencies.py línea 43, openai_clients.py línea 16 |
| **Tipo** | Obligatoria |
| **Actual** | `azure` |
| **Propuesto (Local)** | `azure` (o `ollama`, `openaicom`) |
| **Propuesto (Azure)** | `azure` |
| **Motivo** | Selector de backend. Puede ser: azure, openaicom, ollama. Actual es correcto. |
| **Código** | `if OPENAI_CHAT_HOST == "azure":` → carga config Azure OpenAI |

**Decisión:** Mantener `azure` como default, comentar alternativas

---

### Variable 8: OPENAI_EMBED_HOST

| Aspecto | Detalle |
|---------|---------|
| **Variable** | OPENAI_EMBED_HOST |
| **Archivo** | dependencies.py línea 42, openai_clients.py línea 64 |
| **Tipo** | Obligatoria |
| **Actual** | `azure` |
| **Propuesto** | `azure` |
| **Motivo** | Selector de backend para embeddings. Debe coincidir con CHAT_HOST en la mayoría de casos. |

**Decisión:** Mantener `azure`

---

## SECCIÓN 3: AZURE OPENAI — VARIABLES DE ENDPOINT

### Variable 9: AZURE_OPENAI_ENDPOINT

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_ENDPOINT |
| **Archivo** | openai_clients.py línea 18, 66 (os.environ, OBLIGATORIA) |
| **Tipo** | Obligatoria (si OPENAI_CHAT_HOST=azure) |
| **Actual** | `https://YOUR-AZURE-OPENAI-SERVICE-NAME.openai.azure.com` |
| **Propuesto (Local)** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Propuesto (Azure)** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | ⚠️ CRÍTICO: Actual es placeholder. Debe ser endpoint real de Modelo-IA-UR o Azure OpenAI. NO puede ejecutarse sin valor real. |
| **Nota** | Modelo-IA-UR es AIServices multiservicio. CONFIRMAR que tiene chat + embeddings. |
| **Riesgo** | Usar placeholder causará error en runtime. Fase 3 debe verificar. |

**Decisión:** Usar `<CONFIRMAR_EN_AZURE>` + documentación sobre Modelo-IA-UR

---

### Variable 10: AZURE_OPENAI_CHAT_DEPLOYMENT

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_CHAT_DEPLOYMENT |
| **Archivo** | openai_clients.py línea 19 (os.environ, OBLIGATORIA) |
| **Tipo** | Obligatoria (si OPENAI_CHAT_HOST=azure) |
| **Actual** | `gpt-5.4` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | ⚠️ CRÍTICO: "gpt-5.4" es asumido pero puede NO existir en Modelo-IA-UR. Nombre del deployment en Azure OpenAI. |
| **Nota** | Deployment ≠ model. Azure requiere nombre de deployment específico. |

**Decisión:** Usar `<CONFIRMAR_EN_AZURE>` + documentación

---

### Variable 11: AZURE_OPENAI_CHAT_MODEL

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_CHAT_MODEL |
| **Archivo** | dependencies.py línea 61 (default="gpt-5.4" si no definido) |
| **Tipo** | Opcional (con default) |
| **Actual** | `gpt-5.4` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | Similar a DEPLOYMENT. Puede que no exista. Código tiene default "gpt-5.4" si no está en .env. |

**Decisión:** Placeholder + documentación

---

### Variable 12: AZURE_OPENAI_EMBED_DEPLOYMENT

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EMBED_DEPLOYMENT |
| **Archivo** | openai_clients.py línea 67 (os.environ, OBLIGATORIA) |
| **Tipo** | Obligatoria (si OPENAI_EMBED_HOST=azure) |
| **Actual** | `text-embedding-3-large` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | ⚠️ CRÍTICO: Deployment de embeddings. Puede no existir en Modelo-IA-UR. |

**Decisión:** Placeholder + documentación

---

### Variable 13: AZURE_OPENAI_EMBED_MODEL

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EMBED_MODEL |
| **Archivo** | dependencies.py línea 46 (default="text-embedding-3-large") |
| **Tipo** | Opcional (con default) |
| **Actual** | `text-embedding-3-large` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | Modelo de embeddings. Default en código si no en .env. |

**Decisión:** Placeholder + documentación

---

### Variable 14: AZURE_OPENAI_EMBED_DIMENSIONS

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EMBED_DIMENSIONS |
| **Archivo** | dependencies.py línea 47 (default=1024) |
| **Tipo** | Opcional (con default) |
| **Actual** | `1024` |
| **Propuesto** | `1024` (asumir válido) |
| **Motivo** | Dimensiones de vector de embedding. 1024 es estándar para text-embedding-3-large. |

**Decisión:** Mantener 1024

---

### Variable 15: AZURE_OPENAI_EMBEDDING_COLUMN

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EMBEDDING_COLUMN |
| **Archivo** | dependencies.py línea 48 (default="embedding_3l") |
| **Tipo** | Opcional (con default) |
| **Actual** | `embedding_3l` |
| **Propuesto** | `embedding_3l` |
| **Motivo** | Nombre de columna en BD donde guardar embeddings. Puede cambiar si modelo cambia. |

**Decisión:** Mantener valor actual, documentar que es nombre de columna

---

### Variable 16: AZURE_OPENAI_EVAL_DEPLOYMENT

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EVAL_DEPLOYMENT |
| **Archivo** | .env.sample línea 22 |
| **Tipo** | Opcional (para evaluación) |
| **Actual** | `gpt-4` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | Deployment para evaluación de RAG. Probablemente no sea crítico para MVP. |

**Decisión:** Placeholder + documentación (opcional)

---

### Variable 17: AZURE_OPENAI_EVAL_MODEL

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_EVAL_MODEL |
| **Archivo** | .env.sample línea 23 |
| **Tipo** | Opcional |
| **Actual** | `gpt-4` |
| **Propuesto** | `<CONFIRMAR_EN_AZURE>` (placeholder) |
| **Motivo** | Para evaluación. Puede dejarse vacío para MVP. |

**Decisión:** Placeholder + documentación (opcional)

---

## SECCIÓN 4: AUTENTICACIÓN AZURE

### Variable 18: AZURE_TENANT_ID

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_TENANT_ID |
| **Archivo** | dependencies.py línea 93, postgres_engine.py (parámetro) |
| **Tipo** | Condicional (recomendado para Azure) |
| **Actual** | vacío `""` |
| **Propuesto** | `ae525757-89ba-4d30-a2f7-49796ef8c604` |
| **Motivo** | Tenant ID de Universidad del Rosario. Necesario para AzureDeveloperCliCredential. No es secreto (es info pública). |
| **Seguridad** | Tenant ID NO es secreto, es identificador de organización |

**Decisión:** ✅ CAMBIAR a valor real + documentar

---

### Variable 19: AZURE_OPENAI_KEY

| Aspecto | Detalle |
|---------|---------|
| **Variable** | AZURE_OPENAI_KEY |
| **Archivo** | openai_clients.py línea 20, 68 |
| **Tipo** | Opcional (alternativa a Azure Identity) |
| **Actual** | vacío `""` |
| **Propuesto** | vacío `""` (usar Azure Identity en lugar de key) |
| **Motivo** | ⚠️ NUNCA guardar API keys en .env. Usar Azure Identity/Managed Identity en su lugar. Key-based auth solo para testing local. |
| **Seguridad** | Credencial en .env = riesgo crítico |

**Decisión:** Mantener vacío + ADVERTENCIA sobre seguridad

---

### Variable 20: APP_IDENTITY_ID

| Aspecto | Detalle |
|---------|---------|
| **Variable** | APP_IDENTITY_ID |
| **Archivo** | dependencies.py línea 84 |
| **Tipo** | Opcional |
| **Actual** | NO EXISTE en .env.sample |
| **Propuesto** | No agregar a .env.sample (es para Container Apps) |
| **Motivo** | Variable para especificar identidad de app. Solo relevante en Container Apps, no en desarrollo local. |

**Decisión:** No incluir en .env.sample

---

## SECCIÓN 5: ALTERNATIVAS (OPENAI.COM)

### Variable 21: OPENAICOM_KEY

| Aspecto | Detalle |
|---------|---------|
| **Variable** | OPENAICOM_KEY |
| **Archivo** | openai_clients.py línea 53 |
| **Tipo** | Condicional (si OPENAI_CHAT_HOST=openaicom) |
| **Actual** | `YOUR-OPENAI-API-KEY` |
| **Propuesto** | Comentar (NO es backend por defecto) |
| **Motivo** | Backend alternativo. Comentar porque default es Azure. |

**Decisión:** Dejar comentado como ejemplo

---

### Variables 22-25: OPENAICOM_CHAT_MODEL, OPENAICOM_EMBED_MODEL, etc.

| Aspecto | Detalle |
|---------|---------|
| **Variables** | OPENAICOM_* (4 variables) |
| **Propuesto** | Comentadas como ejemplo |
| **Motivo** | Backend alternativo |

**Decisión:** Dejar comentadas

---

## SECCIÓN 6: ALTERNATIVAS (OLLAMA)

### Variables 26-29: OLLAMA_* (4 variables)

| Aspecto | Detalle |
|---------|---------|
| **Variables** | OLLAMA_ENDPOINT, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL, OLLAMA_EMBEDDING_COLUMN |
| **Propuesto** | Comentadas como ejemplo |
| **Motivo** | Backend alternativo para desarrollo local |

**Decisión:** Dejar comentadas

---

## SECCIÓN 7: APLICACIÓN

### Variable 30: RUNNING_IN_PRODUCTION

| Aspecto | Detalle |
|---------|---------|
| **Variable** | RUNNING_IN_PRODUCTION |
| **Archivo** | __init__.py línea 55 |
| **Tipo** | Opcional |
| **Actual** | NO EXISTE en .env.sample |
| **Propuesto** | Agregar = `false` para desarrollo |
| **Motivo** | Flag para comportamiento de producción vs desarrollo |

**Decisión:** Agregar como documentación

---

### Variable 31: APPLICATIONINSIGHTS_CONNECTION_STRING

| Aspecto | Detalle |
|---------|---------|
| **Variable** | APPLICATIONINSIGHTS_CONNECTION_STRING |
| **Archivo** | __init__.py línea 48, 67 |
| **Tipo** | Opcional (para Azure Monitor) |
| **Actual** | NO EXISTE en .env.sample |
| **Propuesto** | Documentar (vacío para desarrollo local) |
| **Motivo** | Connection string a Application Insights. Solo en Azure. |

**Decisión:** Documentar como opcional (para Azure)

---

## RESUMEN: CAMBIOS PROPUESTOS

| ID | Variable | Cambio | Razón | Riesgo |
|----|----------|--------|-------|--------|
| 3 | POSTGRES_DATABASE | `postgres` → `rag_institucional` | ⛔ CRÍTICO | Alto si no se cambia |
| 5 | POSTGRES_SSL | `disable` → `require` (si Azure) | SSL obligatorio en Azure | Conexión fallará en Azure |
| 9 | AZURE_OPENAI_ENDPOINT | Placeholder `<CONFIRMAR>` | No confirmado | Fase 3 verificación |
| 10 | AZURE_OPENAI_CHAT_DEPLOYMENT | Placeholder `<CONFIRMAR>` | No confirmado | Fase 3 verificación |
| 12 | AZURE_OPENAI_EMBED_DEPLOYMENT | Placeholder `<CONFIRMAR>` | No confirmado | Fase 3 verificación |
| 18 | AZURE_TENANT_ID | `""` → `ae525757-...` | Necesario para Entra ID | No causa error, recomendado |

**Cambios críticos:** 3  
**Cambios recomendados:** 1  
**Cambios de documentación:** Múltiples  

---

## DECISIONES PENDIENTES (FASE 3)

- ¿Modelo-IA-UR tiene deployments de chat + embeddings?
- ¿Cuál es el endpoint real de Modelo-IA-UR o Azure OpenAI?
- ¿Cuáles son los nombres de deployments en Azure?
- ¿Qué usuario de BD debe usarse para rag_institucional en Azure?

---

**Matriz:** Análisis completo de 31 variables  
**Fecha:** 2026-08-31  
**Status:** PROPUESTA LISTA PARA REVISIÓN
