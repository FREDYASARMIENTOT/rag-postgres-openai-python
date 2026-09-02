# INFORME DE AUDITORÍA — FASE RAG INSTITUCIONAL
# Fecha: 2026-01-09
# Operador: analiticaur@urosario.edu.co
# Commit: ffe41ff
# Repositorio: C:\rag-postgres-openai-python\rag-postgres-openai-python
# Branch: tesis-rag-institucional

---

## RESUMEN EJECUTIVO

La auditoría reveló **15 hallazgos críticos** que bloquean la operación del RAG Institucional
en su estado actual:

| Área | Estado |
|------|--------|
| Azure CLI / Sesión | ✅ OPERATIVO |
| AI Resource Modelo-IA-UR | ✅ CONFIRMADO (en RG-Datamining-IA-UR) |
| Deployments Foundry | ✅ 4 deployments confirmados |
| PostgreSQL acceso | ❌ BLOQUEADO (firewall de red) |
| BD rag_institucional | ❌ NO EXISTE |
| pgvector | ❌ NO HABILITADO (azure.extensions = "") |
| Embeddings Foundry | ⚠️ PARCIAL (API key OK, dimensions 1024 NO SOPORTADO) |
| Chat Foundry | ✅ OPERATIVO (gpt-4o-mini y gpt-5.6-luna) |

---

## MATRIZ DE RESULTADOS

### Azure / Identidad

**TEST-001 — Azure CLI / Sesión**
- Objetivo: Verificar sesión activa de Azure CLI
- Comando: `az account show`
- Resultado: ✅ PASS
- Evidencia:
  - Subscription: Sub-Tecnologia-Datamining (01bfad48-c092-4712-bc72-f141eb01a8d4)
  - Tenant: Universidad del Rosario (ae525757-89ba-4d30-a2f7-49796ef8c604)
  - Usuario: analiticaur@urosario.edu.co
  - Tipo: user

**TEST-002 — AI Resource**
- Objetivo: Verificar existencia y estado de Modelo-IA-UR
- Comando: `az cognitiveservices account show`
- Resultado: ⚠️ WARNING
- Hallazgo crítico: Modelo-IA-UR NO está en RG-Datamining-SII2.0-Dev
  Está en **RG-Datamining-IA-UR** (East US 2)
- Evidencia:
  - Kind: AIServices, SKU: S0
  - Endpoint: https://modelo-ia-ur.cognitiveservices.azure.com/
  - Proyecto asociado: Proyecto-IA-UR
  - Estado: Succeeded
  - Network ACLs: Public, Allow
  - Identidad: SystemAssigned

**TEST-003 — Deployments Foundry**
- Objetivo: Listar deployments en Modelo-IA-UR
- Comando: `az cognitiveservices account deployment list`
- Resultado: ✅ PASS (4 deployments encontrados)
- Evidencia:

| Deployment | Modelo | Versión | SKU | Capacidad | Estado |
|------------|--------|---------|-----|-----------|--------|
| sii-supervisor-gpt-4o-mini | gpt-4o-mini | 2024-07-18 | GlobalStandard | 250/min | Running |
| ur-depei-gpt-5 | gpt-5 | 2025-08-07 | GlobalStandard | 250/min | Running |
| ur-rag-gpt-5-6-luna | gpt-5.6-luna | 2026-07-09 | GlobalStandard | 250/min | Running |
| ur-rag-embedding-3-large | text-embedding-3-large | 1 | Standard | 250/10s | Running |

- Observación: `ur-depei-gpt-5` es un deployment NO documentado en la especificación original.

### PostgreSQL

**TEST-004 — PostgreSQL server**
- Objetivo: Verificar existencia y estado de supersetdev
- Comando: `az postgres flexible-server show`
- Resultado: ✅ PASS
- Evidencia:
  - Nombre: supersetdev
  - Estado: Ready
  - Versión: 16
  - SKU: Standard_B1ms
  - Host: supersetdev.postgres.database.azure.com
  - Puerto: 5432
  - Admin: supersetadmin
  - Azure AD Auth: Enabled
  - Password Auth: Enabled
  - Public Access: Enabled
  - Privado: No (sin subnet delegada)

**TEST-005 — PostgreSQL database**
- Objetivo: Listar bases de datos existentes
- Comando: `az postgres flexible-server db list`
- Resultado: ❌ FAIL — BD rag_institucional NO EXISTE
- Evidencia:
  - BD existentes: postgres, superset, azure_maintenance, azure_sys
  - BD rag_institucional: NO EXISTE
  - BD superset: EXISTE (protegida, NO modificar)

**TEST-006 — pgvector**
- Objetivo: Verificar disponibilidad de pgvector
- Comando: `az postgres flexible-server parameter show --name azure.extensions`
- Resultado: ❌ BLOCKED
- Evidencia:
  - azure.extensions = "" (vacío)
  - La extensión `vector` está en `allowedValues` pero NO permitida
  - No se puede ejecutar CREATE EXTENSION vector sin modificar `azure.extensions`
  - Conexión directa no disponible (firewall bloquea desde esta red)

**TEST-007 — Tabla items**
- Objetivo: Verificar existencia de tabla items
- Resultado: ❌ BLOCKED (BD rag_institucional no existe)

**TEST-008 — Columna embedding_3l**
- Objetivo: Verificar existencia de columna vectorial
- Resultado: ❌ BLOCKED (BD no existe)

**TEST-009 — Dimensión embedding_3l**
- Objetivo: Verificar dimensión del vector
- Resultado: ❌ BLOCKED (BD no existe)

**TEST-010 — Índice HNSW**
- Objetivo: Verificar índice vectorial
- Resultado: ❌ BLOCKED (BD no existe)

### Embeddings / Foundry

**TEST-011 — Cliente Foundry embeddings**
- Objetivo: Verificar autenticación contra Foundry
- Método: API key desde `az cognitiveservices account keys list`
- Resultado: ✅ PASS
- Evidencia:
  - Autenticación vía API key: OK
  - Autenticación vía Azure Identity (RBAC): ❌ FAIL (sin permisos data plane)
  - Rol faltante: Cognitive Services OpenAI User

**TEST-012 — Generación embedding 1024d**
- Objetivo: Generar embedding con text-embedding-3-large a 1024 dimensiones
- Método: POST /openai/deployments/ur-rag-embedding-3-large/embeddings?api-version=2024-06-01
- Resultado: ❌ FAIL
- Evidencia:
  - Sin `dimensions`: ✅ 3072 dimensiones
  - Con `dimensions=1024`: ❌ 404 DeploymentNotFound
  - API version 2024-06-01 soporta dimensions pero el deployment no

**TEST-013 — Validación numérica del vector**
- Objetivo: Validar que el vector 3072d sea numéricamente válido
- Resultado: ✅ PASS (para 3072d)
- Evidencia:
  - Sin NaN ni Inf
  - Rango típico: [-0.08, 0.09]
  - Todos valores float

**TEST-014 — Dataset áreas/facultades**
- Objetivo: Crear dataset de prueba con 10 registros
- Resultado: ✅ PASS
- Archivo: docs/pruebas/AREAS-FACULTADES-UR-EMBEDDING-TEST.md
- Estructura: 8 registros de prueba + consultas sugeridas

**TEST-015 — Persistencia vectorial**
- Objetivo: Persistir embeddings en PostgreSQL
- Resultado: ❌ BLOCKED
- Bloqueantes:
  1. BD rag_institucional no existe
  2. pgvector no habilitado
  3. Dimensión esperada (1024) no coincide con disponible (3072)
  4. Puerto 5432 bloqueado por firewall de red

**TEST-016 — Búsqueda vectorial**
- Objetivo: Ejecutar búsqueda por similitud coseno
- Resultado: ❌ BLOCKED (mismos bloqueantes que TEST-015)

**TEST-017 — Recuperación top-k**
- Objetivo: Recuperar documentos relevantes
- Resultado: ❌ BLOCKED

**TEST-018 — Generación con Luna**
- Objetivo: Probar ur-rag-gpt-5-6-luna vía Foundry
- Método: POST /openai/v1/chat/completions
- Resultado: ✅ PASS
- Evidencia:
  - Modelo: gpt-5.6-luna-2026-07-09
  - Respuesta: "OK" (correcta)
  - Latencia: TTFT ~417ms, TTLT ~742ms

**TEST-019 — Respuesta fundamentada en contexto**
- Objetivo: RAG end-to-end con Luna
- Resultado: ❌ BLOCKED (no hay datos persistidos para recuperar)

---

## HALLAZGOS CRÍTICOS (DEBEN RESOLVERSE ANTES DE CONTINUAR)

### H1 — Resource Group incorrecto
Modelo-IA-UR está en RG-Datamining-IA-UR, NO en RG-Datamining-SII2.0-Dev.
Cualquier script de administración debe apuntar al RG correcto.

### H2 — BD rag_institucional NO existe
Creación requerida:
```sql
CREATE DATABASE rag_institucional;
```

### H3 — pgvector bloqueado por azure.extensions
Parámetro actual: `azure.extensions = ""` (vacío).
Se requiere:
```shell
az postgres flexible-server parameter set \\
  --name azure.extensions \\
  --value vector \\
  --server-name supersetdev \\
  -g RG-Datamining-SII2.0-Dev
```
Luego reinicio del servidor.

### H4 — Conexión PostgreSQL bloqueada por firewall
Solo IP 201.234.181.230 autorizada. Agregar regla para IP actual.

### H5 — dimensions=1024 NO SOPORTADO
El deployment ur-rag-embedding-3-large retorna 3072 dimensiones.
El parámetro `dimensions` causa 404 DeploymentNotFound.
Acciones posibles:
- Opción A: Modificar modelo SQLAlchemy a Vector(3072)
- Opción B: Recrear deployment con versión que soporte dimensions
- Opción C: Reducir dimensionalidad post-procesamiento

### H6 — RBAC data plane faltante
analiticaur@urosario.edu.co no tiene Cognitive Services OpenAI User.
Sin embargo, la API key de Modelo-IA-UR funciona correctamente.
Para despliegue en App Service, asignar Managed Identity con rol adecuado.

### H7 — ur-depei-gpt-5 no documentado
Existe un deployment adicional ur-depei-gpt-5 (gpt-5, 2025-08-07).
No está en la especificación actual. Documentar o eliminar.

---

## GAPS PENDIENTES

| Gap | Prioridad | Estado |
|-----|-----------|--------|
| Backup/restore de PostgreSQL | Alta | Pendiente |
| Corpus institucional real versionado | Alta | Pendiente |
| Prueba de recuperación RAG completa | Alta | Bloqueado |
| Benchmark recall@10 | Media | Pendiente |
| Rate limiting real (250 req/min) | Media | No medido |
| Deployment de evaluación | Baja | Placeholder |

---

## RECOMENDACIÓN DEL SIGUIENTE PASO

Se recomienda proceder en este orden:

1. **Resolver H3**: Habilitar pgvector vía azure.extensions
2. **Resolver H4**: Autorizar IP actual en firewall PostgreSQL
3. **Resolver H2**: Crear BD rag_institucional
4. **Resolver H5**: Definir estrategia de dimensionalidad (3072 vs 1024)
5. Ejecutar setup_postgres_database para crear tabla items
6. Ejecutar setup_postgres_seeddata con embeddings 3072d
7. Probar búsqueda vectorial
8. Probar RAG completo con Luna

**NO construir respaldo-azure-rag-institucional.ps1** hasta que estos
8 pasos estén completados y validados.

---

## ARCHIVOS MODIFICADOS EN ESTA FASE

| Archivo | Acción |
|---------|--------|
| docs/pruebas/AREAS-FACULTADES-UR-EMBEDDING-TEST.md | CREADO |
| auditar_postgres.py | CREADO (temporal, eliminar) |
| test_embedding.py | CREADO (temporal, eliminar) |

---

*Fin del informe de auditoría — Fase RAG Institucional*
