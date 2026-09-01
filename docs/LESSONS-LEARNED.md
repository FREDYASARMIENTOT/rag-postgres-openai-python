# Lecciones Aprendidas — RAG Institucional Universidad del Rosario

**Proyecto:** RAG Institucional  
**Fecha:** 2026-08-31  
**Fase:** 1 y 2 — Auditoría y Alineación Arquitectónica  
**Status:** DOCUMENTADO PARA FUTURAS ITERACIONES

---

## 1. ❌ No Crear PostgreSQL Nuevo Cuando Existe Uno Reutilizable

**Aprendizaje:**
El template Bicep original intenta crear un nuevo PostgreSQL Flexible Server automáticamente.

**Realidad observada:**
- Ya existe un servidor `supersetdev` en RG-Datamining-SII2.0-Dev
- PostgreSQL 16, SKU Standard_B1ms, 32GB storage
- Perfectamente reutilizable para el RAG
- Crear uno nuevo duplicaría costos (~$50-100 USD/mes)

**Decisión:**
✅ REUTILIZAR `supersetdev`

**Lección:**
- No asumir que "nueva aplicación = nuevo recurso"
- Auditar qué existe antes de ejecutar IaC
- Comparar costo de reutilización vs. creación
- Template puede no reflejar optimalidad de costos

---

## 2. ✅ Separar Base de Datos RAG de BD Existente

**Aprendizaje:**
La BD `superset` (aplicación existente) debe mantenerse INTACTA.

**Solución arquitectónica:**
```
supersetdev (PostgreSQL Server)
├── superset (BD existente, INTOCABLE)
└── rag_institucional (BD nueva, separada)
    ├── schemas RAG
    ├── tablas de chunks
    ├── embeddings
    ├── metadata documental
    └── índices vectoriales
```

**Lección:**
- Separación lógica mediante BD independiente = aislamiento de datos
- Mismo servidor = costos bajos
- Diferente BD = diferente ciclo de vida del RAG
- Facilita: backups independientes, RBAC separado, escalado independiente

---

## 3. 🔐 No Modificar BD Existente Durante Auditoría

**Aprendizaje:**
Superset tiene tablas, usuarios, permisos y configuración específica.

**Restricción aprendida:**
- ❌ NO modificar tablas de `superset`
- ❌ NO modificar schemas
- ❌ NO modificar usuarios/roles Superset
- ❌ NO modificar extensiones que Superset use
- ❌ NO ejecutar migraciones destructivas

**Lección:**
- Auditoría debe ser NO-DESTRUCTIVA
- Leer antes de escribir
- Validar impacto potencial
- Compartir infraestructura ≠ interferir con aplicaciones existentes

---

## 4. 🔍 Auditar Azure Antes de Ejecutar IaC

**Aprendizaje:**
El template menciona recursos específicos, pero la realidad de Azure es diferente.

**Discrepancias encontradas:**
1. Template crea PostgreSQL nuevo → Ya existe supersetdev
2. Template crea Log Analytics nuevo → Existen 2 workspaces reutilizables
3. Template crea App Insights nuevo → Existen 6 instancias reutilizables
4. Template crea ACR nuevo → Existen 4 registries reutilizables
5. Template asume Azure OpenAI → Solo existe Modelo-IA-UR (multiservicio)

**Lección:**
- `azd up` es irreversible; auditar ANTES es crítico
- Usar Azure CLI para inventariar:
  - `az resource-group list`
  - `az postgres flexible-server list`
  - `az cognitiveservices account list`
  - `az monitor log-analytics workspace list`
  - `az acr list`
  - `az containerapp list`
- Comparar TEMPLATE vs. REALIDAD AZURE

---

## 5. 📋 No Asumir que Template Refleja Estado Real de Azure

**Aprendizaje:**
Un template bien diseñado ≠ ambiente óptimo real.

**Ejemplos:**
- Template crea `postgres` como BD default
- Realidad: superset usa la BD `superset` específicamente
- Template crea psotgres 15
- Realidad: supersetdev está en postgres 16

**Lección:**
- Template es plantilla, no inventario
- Ejecutar comandos `show` y `list` de Azure
- Verificar real configuration actual
- Actualizar template para reflejar reutilización

---

## 6. ✅ Verificar Realmente azure.extensions Antes de Afirmar Estado

**Aprendizaje:**
No se debe asumir que pgvector esté "disponible" solo porque existe en PostgreSQL upstream.

**Hallazgo real:**
```
azure.extensions: ""  (vacío, NO habilitado)
```

**Antes de habilitar pgvector:**
1. Solicitar aprobación explícita
2. Documentar impacto potencial
3. Plan de rollback si falla
4. Validación post-enable

**Lección:**
- Leer estado real: `az postgres flexible-server parameter show`
- No asumir; verificar
- Extensiones en PostgreSQL ≠ habilitadas en Azure PG
- Cambios de extensión pueden afectar todas las BDs en el servidor

---

## 7. ❌ No Ejecutar Comandos de Escritura Durante Auditoría

**Aprendizaje:**
Fase de auditoría = LECTURA ÚNICAMENTE.

**Prohibición de ESTA FASE:**
- ❌ `azd up`
- ❌ `az deployment group create`
- ❌ `az postgres flexible-server parameter set`
- ❌ `az postgres flexible-server db create`
- ❌ `az containerapp create`
- ❌ `az identity create`

**Permitido:**
- ✅ `az ... list`
- ✅ `az ... show`
- ✅ `az ... get-value`

**Lección:**
- Separar FASE AUDITORÍA de FASE DEPLOY
- No ejecutar cambios infraestructura hasta tener aprobación completa
- Un comando de escritura accidental puede destruir el proyecto
- Usar modo `--dry-run` o `--what-if` cuando esté disponible

---

## 8. ❌ No Crear Entorno Python Nuevo si Existe Uno Funcional

**Aprendizaje:**
Existe `D:\environments\rag-postgres-openai-python\.venv\` completamente funcional.

**Antes:**
```powershell
# ❌ INCORRECTO
python -m venv .venv
```

**Realidad:**
```
D:\environments\rag-postgres-openai-python\.venv\Scripts\python.exe
Python 3.12.10
Todas las dependencias ya instaladas
```

**Lección:**
- Verificar .venv existente antes de crear uno nuevo
- Reutilizar si es posible
- Diferencia entre PATH y .venv en proyecto
- Documentar ubicación real de Python para el equipo

---

## 9. 📊 Diferenciar Azure AI Services de Azure OpenAI

**Aprendizaje:**
Existen dos servicios diferentes en Azure que pueden parecer similares.

**Modelo-IA-UR actual:**
```
kind: "AIServices"  (multiservicio, genérico)
SKU: S0
Region: eastus2
Status: Succeeded
```

**Azure OpenAI específico:**
```
kind: "OpenAI"  (específico para GPT models)
Desplegamentos de modelos separados
Endpoint específico de OpenAI
```

**Hallazgo:**
- NO existe Azure OpenAI específico en la suscripción
- `Modelo-IA-UR` es AIServices (puede soportar múltiples APIs)

**Lección:**
- AIServices ≠ OpenAI (aunque AIServices puede incluir OpenAI)
- Verificar documentación de SKU S0 para saber qué está disponible
- Si RAG requiere OpenAI específico, crear recurso dedicado
- No asumir; verificar mediante portal o API

---

## 10. 💰 Priorizar Reutilización de Infraestructura para Controlar Costos

**Aprendizaje:**
Cada recurso nuevo tiene costo incremental.

**Comparativa:**
```
OPCIÓN A (Reutilizar):        $30-50 USD/mes
OPCIÓN B (Crear todo nuevo):  $500-1500 USD/mes
Diferencia:                   +$5600-17400 USD/año
```

**Recursos reutilizables verificados:**
- ✅ PostgreSQL supersetdev
- ✅ Log Analytics workspace
- ✅ Application Insights
- ✅ Container Registry
- ✅ Managed Identities (reutilizar patrón)

**Lección:**
- No crear automáticamente porque template lo hace
- Comparar costo vs. beneficio
- Reutilización = más sostenible
- Documentar decisión de costo para futuro

---

## 11. ✅ Validar Región, Resource Group y Dependencias Antes de Desplegar

**Aprendizaje:**
Las ubicaciones incorrectas causan problemas de latencia y conectividad.

**Validaciones realizadas:**
```
RG-RAG-Urosario: eastus        (destino RAG)
supersetdev:     eastus2       (PostgreSQL existente)
Modelo-IA-UR:    eastus2       (AI Services)
Container Apps:  eastus        (planificado)
```

**Impacto:**
- RAG Container Apps en eastus
- Conectará a PostgreSQL en eastus2 (latencia ~1-5ms, aceptable)
- Reutilizar ACR puede estar en eastus2 (usar eastus si posible)

**Lección:**
- Mapear regiones para todas las dependencias
- Considerar latencia en arquitectura
- Puede haber restricciones de disponibilidad de modelo
- Documentar por qué se elige cada región

---

## 12. ✅ Toda Modificación Irreversible Requiere Aprobación Explícita

**Aprendizaje:**
Cambios a PostgreSQL, BD, extensiones, firewall son potencialmente destructivos.

**Protocolo establecido:**
1. MOSTRAR: archivo, línea, configuración actual
2. EXPLICAR: cambio propuesto, impacto, riesgo
3. VALIDAR: plan de rollback
4. ESPERAR: aprobación explícita
5. EJECUTAR: solo con confirmación

**Cambios que requieren aprobación explícita:**
- ✅ Habilitar pgvector
- ✅ Crear BD rag_institucional
- ✅ Modificar firewall rules
- ✅ Configurar RBAC
- ✅ Crear Managed Identity
- ✅ Container Apps Environment
- ✅ Deployar Container App

**Lección:**
- NO asumir; PREGUNTAR
- Documentar aprobación
- Crear trail de decisiones
- Reversibilidad es riesgo

---

## 13. 🔗 Documentar Dependencias Entre Servicios

**Aprendizaje:**
RAG tiene dependencias no triviales.

**Cadena de dependencias:**
```
Container App (web)
  ├─ Managed Identity RAG
  ├─ PostgreSQL supersetdev
  │   └─ BD rag_institucional
  │       └─ pgvector extension
  ├─ Modelo-IA-UR (AIServices S0)
  │   └─ Embeddings + Chat models
  ├─ Log Analytics (monitoreo)
  └─ Application Insights (observabilidad)
```

**Lección:**
- Mapear dependencias completas antes de deploy
- Validar que todo esté en su lugar
- Plan de validación post-deploy
- Si una dependencia falla, saber qué revisar

---

## 14. 📝 Mantener Matriz de Decisión de Recursos

**Aprendizaje:**
Decisiones arquitectónicas deben documentarse con matriz clara.

**Formato útil:**
```
RECURSO | TEMPLATE CREA | YA EXISTE | REUTILIZABLE | DECISIÓN | COSTO
```

**Beneficios:**
- Transparencia de decisiones
- Facilita auditoría futura
- Justifica costos
- Facilita explicar por qué NO se crea X recurso

**Lección:**
- No dejar decisiones implícitas
- Matriz explícita = aprobación más fácil
- Facilita onboarding de nuevo personal
- Documenta por qué proyecto es así

---

## 15. 🎯 Plan de FASE: Auditoría → Planificación → Aprobación → Deploy

**Aprendizaje:**
Un proyecto complejo requiere separar fases claramente.

**Fases de este proyecto:**
1. **FASE 1:** Auditoría (Azure CLI, inventario, no cambios)
2. **FASE 2:** Alineación y Planificación (análisis, propuestas, Skills)
3. **FASE 3:** Aprobación Explícita (revisión de cambios propuestos)
4. **FASE 4:** Deploy No-Destructivo (PostgreSQL + BD + pgvector)
5. **FASE 5:** Deploy de Aplicación (Container Apps)

**Lección:**
- No saltar fases
- Cada fase tiene salida clara
- Aprobación entre fases
- Rollback plan documentado
- Ciencia de datos requiere rigor

---

## RESUMEN EJECUTIVO: LECCIONES CRÍTICAS

| # | LECCIÓN | APLICAR |
|---|---------|---------|
| 1 | No crear recursos si existen reutilizables | ✅ REUTILIZAR PostgreSQL supersetdev |
| 2 | Separar datos RAG de datos existentes | ✅ BD `rag_institucional` separada |
| 3 | No modificar datos existentes | ✅ BD `superset` INTACTA |
| 4 | Auditar Azure antes de IaC | ✅ Auditoría FASE 1 completada |
| 5 | Verificar estado real, no asumir | ✅ azure.extensions verificado real |
| 6 | No ejecutar escritura durante auditoría | ✅ Solo lectura FASE 2 |
| 7 | Reutilizar entorno Python | ✅ Usar .venv existente |
| 8 | Diferenciar AI Services de OpenAI | ✅ Evaluando Modelo-IA-UR |
| 9 | Priorizar reutilización de costos | ✅ -$5600-17400 USD/año |
| 10 | Validar región y dependencias | ✅ Mapa de regiones hecho |
| 11 | Aprobación para cambios irreversibles | ✅ Protocolo establecido |
| 12 | Documentar dependencias | ✅ Cadena mapeada |
| 13 | Matriz de decisión explícita | ✅ AUDIT-FASE1-MATRIZ.md |
| 14 | Plan de fases clara | ✅ FASE 1-5 definidas |
---

## 16. 🔒 Validar Filtros SQL con Listas Blancas (NUEVA)

**Aprendizaje:**
El agente LLM (AdvancedRAGChat) genera filtros SQL dinámicamente con columnas,
operadores y valores controlados indirectamente por el usuario.

**Riesgo identificado:**
- `build_filter_clause()` original interpola directamente `{filter.column}`, `{filter.comparison_operator}`, `{filter.value}`.
- Sin validación, un agente comprometido o prompt injection podría inyectar:
  `{"column": "price; DROP TABLE items; --", "comparison_operator": ">", "value": 0}`.

**Solución implementada (Fase 3.2):**
```python
COLUMNAS_FILTRO_PERMITIDAS = frozenset({"price", "brand", "type", "name"})
OPERADORES_FILTRO_PERMITIDOS = frozenset({">", "<", ">=", "<=", "=", "!="})
```
- Nombres de columna validados contra whitelist.
- Operadores validados contra whitelist.
- Valores string escapados (comillas simples duplicadas).
- Filtros no válidos omitidos silenciosamente (fail-safe).

**Lección:**
- No confiar en que el LLM generará SQL seguro.
- Siempre validar entrada del agente contra whitelists.
- Documentar el riesgo residual (embedding_column no validada por whitelist).

---

## 17. 📝 Documentar Arquitectura en ARCHITECTURA-RAG.md (NUEVA)

**Aprendizaje:**
No existía un documento centralizado de arquitectura. La información estaba
distribuida en múltiples archivos de código y documentación.

**Solución implementada (Fase 3.2):**
Creación de `docs/ARCHITECTURA-RAG.md` con:
- Componentes y sus responsabilidades.
- Flujo de datos request-response.
- Seguridad (SQL, autenticación, secretos).
- PostgreSQL + pgvector (arquitectura objetivo y estado actual).
- Azure AI (Modelo-IA-UR confirmado y pendientes).
- Multi-agente (diseño actual y futuro).
- Costos y límites.

**Lección:**
- Documentación de arquitectura debe ser mantenible y reflejar estado REAL.
- Separar lo confirmado de lo pendiente.
- Incluir costos y riesgos.

---

## 18. 🧪 Clasificar Tests por Tipo (UNIT / INTEGRATION / AZURE) (NUEVA)

**Aprendizaje:**
Los tests anteriores no distinguían entre pruebas unitarias, de integración
y que requieren Azure real. Esto dificultaba la ejecución en CI/CD.

**Solución implementada (Fase 3.2):**
- Marcadores pytest: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.azure`.
- Configuración en `conftest.py` con opción `--run-azure`.
- Tests Azure saltados por defecto con mensaje claro del estado actual.

**Lección:**
- Clasificar tests desde el inicio.
- Tests Azure deben reflejar el estado real de los recursos.
- No simular falsamente que una prueba de integración pasó.

---

## 19. 🔧 Separar Embeddings en Capa Configurable (NUEVA)

**Aprendizaje:**
La función `compute_text_embedding()` original usaba nombres de variables
cortos (`q`, `embed_model`) y no validaba adecuadamente qué modelos
soportan el parámetro `dimensions`.

**Solución implementada (Fase 3.2):**
- Renombrado de parámetros a español descriptivo (`texto_consulta`, `modelo_embedding`).
- `MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES` como frozenset.
- Validación explícita con error claro si faltan dimensiones.
- Documentación del requisito pendiente de modelo de embeddings en Modelo-IA-UR.

**Lección:**
- La capa de embeddings debe ser explícitamente configurable.
- No inventar deployments que no existen.
- Documentar requisitos pendientes como tal.

---

## 20. 🚫 Validar pgvector Sin Modificar PostgreSQL (NUEVA)

**Aprendizaje:**
Necesitamos detectar si pgvector está disponible sin modificar la BD.

**Solución implementada (Fase 3.2):**
- `verify_pgvector_available()`: consulta `pg_available_extensions` (solo lectura).
- `verify_pgvector_created()`: consulta `pg_extension` (solo lectura).
- Advertencia graceful en `register_vector` si falla.

**Lección:**
- La validación debe ser NO-DESTRUCTIVA.
- Separar detección de habilitación.
- La aplicación debe funcionar sin pgvector (fallback a full-text search).

---

## 21. 🗑️ Consolidar Archivos Duplicados (NUEVA)

**Aprendizaje:**
Existían `.env.sample` y `.env.sample.aligned` con información duplicada
y divergente (español vs inglés).

**Solución implementada (Fase 3.2):**
- Verificar contenido único de ambos.
- `.env.sample` contiene la información más completa y actualizada.
- `.env.sample.aligned` eliminado (consolidado en `.env.sample`).
- Valores confirmados actualizados en `.env.sample`.

**Lección:**
- Comparar contenido antes de eliminar.
- Identificar información única.
- Documentar la consolidación.
- Mantener un solo archivo de referencia.

---

## RESUMEN DE LECCIONES (ACTUALIZADO FASE 3.2)

| # | LECCIÓN | APLICACIÓN |
|---|---------|------------|
| 1 | No crear recursos si existen reutilizables | ✅ REUTILIZAR supersetdev |
| 2 | Separar datos RAG de datos existentes | ✅ BD `rag_institucional` separada |
| 3 | No modificar datos existentes | ✅ BD `superset` INTACTA |
| 4 | Auditar Azure antes de IaC | ✅ Auditoría FASE 1-2 completada |
| 5 | Verificar estado real, no asumir | ✅ Configuraciones verificadas |
| 16 | **Validar filtros SQL con whitelists** | ✅ **NUEVA** Fase 3.2 |
| 17 | **Documentar arquitectura centralizada** | ✅ **NUEVA** ARCHITECTURA-RAG.md |
| 18 | **Clasificar tests (UNIT/INTEGRATION/AZURE)** | ✅ **NUEVA** conftest.py |
| 19 | **Separar embeddings en capa configurable** | ✅ **NUEVA** Fase 3.2 |
| 20 | **Validar pgvector sin modificar BD** | ✅ **NUEVA** verificación read-only |
| 21 | **Consolidar archivos duplicados** | ✅ **NUEVA** .env.sample único |

---

**Documento:** LESSONS-LEARNED.md  
**Actualizado:** 2026-01-09 (Fase 3.2)  
**Status:** ✅ DOCUMENTADO PARA FUTURAS ITERACIONES
| 15 | Rigor en arquitectura cloud | ✅ Todo documentado |

---

## APLICACIÓN FUTURA

Estas lecciones se aplicarán a:
1. Desarrollo futuro del RAG
2. Migraciones de datos
3. Escalado de infraestructura
4. Auditorías de seguridad
5. Optimización de costos
6. Onboarding de equipos nuevas

---

**Documento:** LESSONS-LEARNED.md  
**Generado:** 2026-08-31  
**Status:** DOCUMENTADO PARA FUTURAS ITERACIONES  
**Arquitecto:** GitHub Copilot
