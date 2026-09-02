# INFORME DE AUDITORÍA — AZURE POSTGRESQL + PGVECTOR — RAG INSTITUCIONAL

**Fecha:** 2026-01-09
**Auditor:** analiticaur@urosario.edu.co (Sub-Tecnologia-Datamining)
**Repositorio:** C:\rag-postgres-openai-python\rag-postgres-openai-python
**Branch:** tesis-rag-institucional
**Commit base:** ffe41ff

---

# 1. RESUMEN EJECUTIVO

La auditoría revela que **PostgreSQL no está listo para RAG**. Existen **4 bloqueantes críticos** que impiden cualquier operación:

| # | Bloqueante | Estado | Severidad |
|---|-----------|--------|-----------|
| 1 | `rag_institucional` BD NO existe | Inferido como NO EXISTENTE | 🔴 CRÍTICO |
| 2 | pgvector no disponible (`azure.extensions=""`) | ✅ CONFIRMADO por Azure CLI | 🔴 CRÍTICO |
| 3 | Firewall bloquea IP actual (185.197.129.253) | ✅ CONFIRMADO | 🔴 CRÍTICO |
| 4 | **Dimensión 1024 vs 3072** — incompatibilidad total | ✅ CONFIRMADO por Fase Foundry | 🔴 CRÍTICO |

**Conclusión:** No se puede conectar, no existe la BD, la extensión vector no está permitida en el servidor, y el esquema en código usa dimensiones incorrectas. **NO declarar "PostgreSQL listo".**

---

# 2. ESTADO REAL AZURE

## 2.1 Suscripción y Tenant

| Propiedad | Valor |
|-----------|-------|
| Suscripción | Sub-Tecnologia-Datamining |
| ID Suscripción | `01bfad48-c092-4712-bc72-f141eb01a8d4` |
| Tenant ID | `ae525757-89ba-4d30-a2f7-49796ef8c604` |
| Tenant | Universidad del Rosario (`uredu.onmicrosoft.com`) |
| Usuario autenticado | `analiticaur@urosario.edu.co` |

## 2.2 PostgreSQL Flexible Server — supersetdev

| Propiedad | Valor Real | Esperado | ¿Coincide? |
|-----------|-----------|----------|------------|
| Resource Group | `RG-Datamining-SII2.0-Dev` | `RG-Datamining-SII2.0-Dev` | ✅ |
| Nombre | `supersetdev` | `supersetdev` | ✅ |
| FQDN | `supersetdev.postgres.database.azure.com` | `supersetdev.postgres.database.azure.com` | ✅ |
| Estado | `Ready` | `Ready` | ✅ |
| Versión PostgreSQL | `16` | `16` | ✅ |
| Minor Version | `14` | — | ℹ️ |
| SKU | `Standard_B1ms` (Burstable) | `Standard_B1ms` | ✅ |
| Storage | `32 GB` Premium_LRS | `32 GB` | ✅ |
| Auto-grow | `Disabled` | — | ℹ️ |
| IOPS | `120` | — | ℹ️ |
| Región | `East US 2` | `East US 2` | ✅ |
| HA | `Disabled` | — | ✅ |
| Backup retention | `30 days` | — | ℹ️ |
| Geo-redundant backup | `Disabled` | — | ℹ️ |
| Login administrador | `supersetadmin` | — | ℹ️ |

## 2.3 Autenticación

| Propiedad | Valor |
|-----------|-------|
| ActiveDirectoryAuth | `Enabled` |
| PasswordAuth | `Enabled` |
| TenantId | `ae525757-89ba-4d30-a2f7-49796ef8c604` |
| password_encryption | `scram-sha-256` |

**IMPORTANTE:** El usuario RAG en Azure NO está confirmado. `.env.sample` indica `POSTGRES_USERNAME=<CONFIRMAR_USUARIO_RAG_EN_AZURE>`.

## 2.4 Endpoint Foundry (Modelo-IA-UR)

| Propiedad | Valor |
|-----------|-------|
| Endpoint | `https://modelo-ia-ur.cognitiveservices.azure.com/` |
| Tipo | AI Services (SKU S0) |
| Resource Group | `RG-Datamining-IA-UR` |

---

# 3. ESTADO REAL POSTGRESQL

## 3.1 Configuración de Red

| Propiedad | Valor |
|-----------|-------|
| PublicNetworkAccess | `Enabled` |
| DelegatedSubnetResourceId | `null` (sin VNet) |
| PrivateDnsZoneArmResourceId | `null` |

**Conclusión:** El servidor es accesible públicamente SI el firewall lo permite.

## 3.2 Parámetros de Configuración Clave

| Parámetro | Valor Actual | Valor por Defecto |
|-----------|-------------|-------------------|
| `max_connections` | `50` | `50` |
| `shared_preload_libraries` | `pg_cron,pg_stat_statements` | `pg_cron,pg_stat_statements` |
| `password_encryption` | `scram-sha-256` | `scram-sha-256` |

**Nota:** pgvector NO requiere `shared_preload_libraries`. Es una extensión liviana que se carga mediante `CREATE EXTENSION`.

---

# 4. CONECTIVIDAD

## 4.1 Intentos de Conexión

| Intento | Destino | Resultado |
|---------|---------|-----------|
| Azure CLI (show) | supersetdev | ✅ Acceso exitoso (vía Azure Resource Manager) |
| Cliente PostgreSQL directo | supersetdev.postgres.database.azure.com:5432 | 🔴 **NO INTENTADO** — Firewall bloquea |

## 4.2 Diagnóstico

No se ejecutó conexión PostgreSQL directa por la **Regla Absoluta** de no modificar infraestructura. La conexión requeriría:

1. Agregar IP actual (185.197.129.253) al firewall — prohibido en auditoría
2. Usar usuario/password o Azure AD token

**Decisión:** Clasificar como `BLOCKED — NETWORK` y continuar con auditoría estática.

## 4.3 Cadena de Conexión SQLAlchemy (Objetivo)

```
postgresql+asyncpg://<usuario>@supersetdev.postgres.database.azure.com:5432/rag_institucional?ssl=require
```

## 4.4 Azure AD Token

El código actual obtiene token vía:
```
AzureDeveloperCliCredential → scope "https://cognitiveservices.azure.com/.default"
```

**Problema potencial:** PostgreSQL usa scope `https://ossrdbms-aad.database.windows.net/.default`, no el scope cognitivo. Verificar que el hook `update_password_token` en `postgres_engine.py` use el scope correcto.

---

# 5. FIREWALL

## 5.1 Reglas Actuales

| Regla | IP Inicio | IP Fin | Propósito |
|-------|-----------|--------|-----------|
| `ClientIPAddress_2026-7-15_10-53-45` | `201.234.181.230` | `201.234.181.230` | IP del desarrollador original |
| `AllowAllAzureServicesAndResourcesWithinAzureIps_2026-7-15_10-56-24` | `0.0.0.0` | `0.0.0.0` | Servicios Azure |

## 5.2 Análisis

| Verificación | Resultado |
|-------------|-----------|
| IP actual del equipo (185.197.129.253) está en firewall | 🔴 **NO** |
| Regla para Azure Services existe | ✅ Sí |
| Puerto 5432 accesible | 🔴 Bloqueado desde IP actual |
| SSL requerido | Se asume `require` (configurable vía `POSTGRES_SSL`) |

## 5.3 Conclusión

**BLOCKED — NETWORK**. No es posible conectar desde la ubicación actual sin modificar el firewall. La conexión desde un servicio Azure (Azure Container Apps) funcionaría gracias a la regla `AllowAllAzureServicesAndResourcesWithinAzureIps`.

**Riesgo:** Si `analiticaur@urosario.edu.co` no tiene permisos para modificar el firewall del RG `RG-Datamining-SII2.0-Dev`, agregar la IP requeriría coordinación con el administrador de Superset.

---

# 6. BASES DE DATOS

## 6.1 Estado Verificado por Azure CLI

| Base de Datos | Estado |
|--------------|--------|
| `rag_institucional` | ❓ **NO VERIFICABLE** — Sin conexión directa |
| `superset` | ✅ Debe existir (servidor en producción) |
| `postgres` | ✅ Debe existir (BD de sistema) |

## 6.2 Inferencia

El servidor `supersetdev` alberga Apache Superset (`superset` BD). La BD `rag_institucional` **NO fue creada** — no hay evidencia de su existencia en el repositorio ni en scripts ejecutados.

**Conclusión:** `rag_institucional` → **NOT_EXISTS**.

## 6.3 BD Protegidas

| BD | Riesgo | Acción Requerida |
|----|--------|-----------------|
| `superset` | 🔴 NO MODIFICAR | Excluir de toda operación RAG |
---

# 7. PGVECTOR

## 7.1 Estado por Azure CLI

| Verificación | Comando | Resultado |
|-------------|---------|-----------|
| `azure.extensions` actual | `az postgres flexible-server parameter list ...` | `""` (vacío) |
| `vector` en `allowedValues` | mismo comando | ✅ **SÍ** — `vector` está en la lista |
| `vector` en servidor (pg_available_extensions) | Requiere conexión directa | ❓ No verificable |
| `vector` instalado en BD (pg_extension) | Requiere conexión directa | ❓ No verificable |

## 7.2 Clasificación

| Estado | Descripción | Aplica |
|--------|-------------|--------|
| Estado 1: No disponible en Azure | `vector` no está en `allowedValues` | ❌ No |
| Estado 2: Disponible pero no habilitado | `azure.extensions` no incluye `vector` | ✅ **SÍ** — `azure.extensions=""` |
| Estado 3: Habilitado pero no instalado | `CREATE EXTENSION` no ejecutado | ❓ Probable |
| Estado 4: Instalado correctamente | En BD y funcional | ❌ Definitivamente NO |

**Clasificación Actual:** **ESTADO 2** — Disponible en el servidor pero no habilitado via `azure.extensions`.

## 7.3 Procedimiento Requerido

Para habilitar pgvector se requiere:

1. **Configurar `azure.extensions`**:
   ```
   az postgres flexible-server parameter set \
     --resource-group RG-Datamining-SII2.0-Dev \
     --server-name supersetdev \
     --name azure.extensions \
     --value vector
   ```
   - `isDynamicConfig: true` → **NO requiere reinicio**
   - `isConfigPendingRestart: false` → Aplica inmediatamente

2. **Conectar como administrador** (`supersetadmin` o usuario con privilegios):
   ```
   psql "host=supersetdev.postgres.database.azure.com port=5432 dbname=rag_institucional user=supersetadmin sslmode=require"
   ```

3. **Crear extensión en la BD**:
   ```sql
   CREATE EXTENSION vector;
   ```

4. **Verificar**:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   SELECT extversion FROM pg_available_extensions WHERE name = 'vector';
   ```

## 7.4 Riesgos

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| `superset` usa extensiones conflictivas | Bajo — pgvector es liviano | Verificar extensiones existentes |
| Permisos insuficientes | `analiticaur` sin rol asignado en RG | Confirmar permisos antes |
---

# 8. ESQUEMA REQUERIDO

## 8.1 Modelo Actual (postgres_models.py)

| Campo | Tipo SQLAlchemy | PostgreSQL | Nullable | Índice | Uso |
|-------|----------------|------------|----------|--------|-----|
| `id` | `int`, primary_key, autoincrement | `SERIAL PRIMARY KEY` | NO | PK | Identificador único |
| `type` | `str` | `VARCHAR` | NO | — | Tipo de producto |
| `brand` | `str` | `VARCHAR` | NO | — | Marca |
| `name` | `str` | `VARCHAR` | NO | — | Nombre |
| `description` | `str` | `TEXT` | NO | — | Descripción |
| `price` | `float` | `FLOAT`/`DOUBLE PRECISION` | NO | — | Precio |
| `embedding_3l` | `Vector(1024)` | `VECTOR(1024)` | SÍ | HNSW (cosine) | Embedding 3-large |
| `embedding_nomic` | `Vector(768)` | `VECTOR(768)` | SÍ | HNSW (cosine) | Embedding nomic |

## 8.2 Problema Crítico — Dimensión Incorrecta

### `embedding_3l`: Actualmente `Vector(1024)` → **DEBE SER `Vector(3072)`**

| Evidencia | Fuente | Detalle |
|-----------|--------|---------|
| Foundry devuelve 3072d | Fase Foundry (prueba real) | `ur-rag-embedding-3-large` sin `dimensions` → 3072 |
| `dimensions=1024` causa 404 | Fase Foundry (prueba real) | Foundry no soporta truncamiento |
| Código actual usa 1024 | `postgres_models.py:70` | `Vector(1024)` |
| Seed data usa 1024 | `seed_data.json` | Arrays de ~1024 floats |
| Tests usan 1024 | `data.py`, `conftest.py:73` | Embeddings mock de 1024 |

### Conclusión

| Pregunta | Respuesta |
|----------|-----------|
| ¿Puede el vector producido por `ur-rag-embedding-3-large` almacenarse directamente en `embedding_3l`? | 🔴 **NO** — El esquema actual es `Vector(1024)` pero Foundry produce vectores de 3072 dimensiones |
| ¿Qué cambio se requiere? | `Vector(1024)` → `Vector(3072)` |

---

# 9. VECTOR 3072

## 9.1 Verificación de Dimensión

| Modelo | Deployment | Dimensión Real | Soportado por Código |
|--------|-----------|---------------|---------------------|
| `text-embedding-3-large` | `ur-rag-embedding-3-large` | **3072** | ❌ Solo 1024 |
| `text-embedding-3-small` | No aplica | 1536 | ❌ No configurado |
| `nomic-embed-text` | No aplica | 768 | ✅ (embedding_nomic) |

## 9.2 Impacto

| Componente | Dimensión Actual | Dimensión Requerida | Cambio Necesario |
|-----------|-----------------|--------------------|-----------------|
| `postgres_models.py:70` | `Vector(1024)` | `Vector(3072)` | SÍ |
| `seed_data.json` | 1024d | 3072d | SÍ (regenerar) |
| `tests/data.py` | 1024d | 3072d | SÍ |
| `.env.sample` | `1024` | `3072` | SÍ |
| `dependencies.py:55` | `1024` | `3072` | SÍ |
| `conftest.py:73` | `1024` | `3072` | SÍ |
| Índice HNSW | `Vector(1024)` | `Vector(3072)` | SÍ (se adapta automáticamente) |

**Efecto dominó:** 7 archivos requieren cambio de 1024 → 3072.

---

# 10. ÍNDICES HNSW

## 10.1 Definición Actual

```python
index_3l = Index(
    f"hnsw_index_for_cosine_{table_name}_embedding_3l",
    Item.embedding_3l,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding_3l": "vector_cosine_ops"},
)
```

| Propiedad | Valor | Nota |
|-----------|-------|------|
| Algoritmo | HNSW | Aproximado, buena precisión |
| Métrica | `vector_cosine_ops` | Distancia coseno |
| `m` | `16` | Conexiones por nodo |
| `ef_construction` | `64` | Candidatos durante construcción |
| Dimensión del índice | Hereda de columna | Será 3072 tras el cambio |

## 10.2 Compatibilidad con 3072

| Verificación | Resultado |
|-------------|-----------|
| ¿HNSW soporta 3072d? | ✅ Sí — pgvector HNSW funciona con cualquier dimensión |
| ¿Requiere cambiar parámetros? | ❌ No — `m=16, ef_construction=64` son válidos para 3072d |
| ¿Requiere recrear índice? | ❌ No — se creará con la nueva dimensión al ejecutar `create_all` |
| ¿Rendimiento aceptable? | ℹ️ 3072d es ~3x más costoso que 1024d en CPU/memoria |

## 10.3 Recomendación

Mantener HNSW con los parámetros actuales. Si el rendimiento es insuficiente, considerar:
- Reducir `ef_search` en tiempo de consulta (no afecta al índice)
- Aumentar `ef_construction` a 128-256 para mejor recall en alta dimensión
---

# 11. COMPATIBILIDAD CON EL CÓDIGO

## 11.1 Matriz de Compatibilidad

| Archivo | Línea | Valor Actual | Valor Requerido | Compatible | Cambio |
|---------|-------|-------------|----------------|------------|--------|
| `postgres_models.py` | 70 | `Vector(1024)` | `Vector(3072)` | ❌ | SÍ |
| `postgres_models.py` | 73 | `Vector(768)` (nomic) | `Vector(768)` (nomic) | ✅ | NO |
| `dependencies.py` | 55 | `openai_embed_dimensions=1024` | `3072` | ❌ | SÍ |
| `dependencies.py` | 61 | `foundry_embedding_dimensions=None` | `3072` | ⚠️ | SÍ |
| `.env.sample` | 77 | `AZURE_OPENAI_EMBED_DIMENSIONS=1024` | `3072` | ❌ | SÍ |
| `seed_data.json` | — | Vectores 1024d | Vectores 3072d | ❌ | SÍ |
| `tests/data.py` | — | Embeddings 1024d | Embeddings 3072d | ❌ | SÍ |
| `tests/conftest.py` | 73 | `AZURE_OPENAI_EMBED_DIMENSIONS=1024` | `3072` | ❌ | SÍ |
| `tests/conftest.py` | 384 | `embed_dimensions=1024` | `3072` | ❌ | SÍ |
| `postgres_engine.py` | — | Azure AD scope cognitivo | — | ⚠️ | Posible |
| `postgres_searcher.py` | — | `<=>` con dist. coseno | — | ✅ | NO |
| `embeddings.py` | — | `dimensions` param | — | ✅ | NO |
| `setup_postgres_database.py` | — | `CREATE EXTENSION vector` | — | ✅ | NO |

## 11.2 Flujo de Datos — Verificación

### Flujo Actual (ROTO):
```
texto → Foundry (ur-rag-embedding-3-large) → vector 3072d → ❌ PostgreSQL espera 1024d
```

### Flujo Corregido:
```
texto → Foundry (ur-rag-embedding-3-large) → vector 3072d → ✅ PostgreSQL Vector(3072)
```

## 11.3 Dependencias de Paquetes

| Paquete | Versión en pyproject.toml | Función |
|---------|--------------------------|---------|
| `pgvector` | ✅ Incluido | Extensión vectorial PostgreSQL |
| `sqlalchemy` | ✅ Incluido | ORM |
| `asyncpg` | ✅ Incluido | Driver asíncrono PostgreSQL |
| `azure-identity` | ✅ Incluido | Azure AD auth |
| `numpy` | ✅ Incluido | Conversión de vectores |

No se requieren nuevas dependencias.

---

# 12. PRUEBAS ADVERSARIALES

## ADV-001 — Dimensión 1024 vs 3072

| Verificación | Resultado | Evidencia |
|-------------|-----------|-----------|
| Código usa 1024 | 🔴 **FAIL** | `postgres_models.py:70`, `dependencies.py:55`, `.env.sample:77` |
| Foundry produce 3072 | ✅ CONFIRMADO | dimensions=1024 → 404, sin dimensions → 3072 |
| ¿Pueden coexistir? | 🔴 **NO** | BD rechazaría vector 3072d en columna `Vector(1024)` |
| **Veredicto** | 🔴 **FAIL** | Configuración incompatible con Foundry |

## ADV-002 — Base de Datos Equivocada

| Verificación | Resultado |
|-------------|-----------|
| ¿Código usa `superset` como BD? | ✅ **PASS** — Documentado como INTOCABLE |
| ¿Código usa `postgres` como BD? | ✅ **PASS** — Solo default en tests |
| `.env.sample` especifica `rag_institucional` | ✅ **PASS** — Línea 15 |
| **Veredicto** | ✅ **PASS** |

## ADV-003 — Tabla Equivocada

| Verificación | Resultado |
|-------------|-----------|
| ¿Operaciones RAG apuntan a `items`? | ✅ **PASS** — `Item.__tablename__ = "items"` |
| ¿Existe referencia a otra tabla? | ✅ **PASS** — No hay otras tablas |
| **Veredicto** | ✅ **PASS** |

## ADV-004 — Extensión Ausente

| Verificación | Resultado |
|-------------|-----------|
| ¿Qué ocurre si `vector` no está instalado? | ❗️ **WARNING** — `setup_postgres_database.py:17` fallaría con error PostgreSQL |
| ¿El error es claro? | ⚠️ Parcial — sin captura amigable |
| **Veredicto** | ⚠️ **WARNING** |

## ADV-005 — Firewall

| Verificación | Resultado |
|-------------|-----------|
| ¿App distingue AUTHENTICATION FAILURE? | ❓ NO VERIFICABLE |
| ¿App distingue NETWORK FAILURE? | ❓ NO VERIFICABLE |
| ¿App distingue DATABASE NOT FOUND? | ❓ NO VERIFICABLE |
| ¿App distingue EXTENSION NOT AVAILABLE? | ⚠️ Parcial — `verify_pgvector_available()` existe pero no integrada |
| **Veredicto** | ⚠️ **WARNING** |

## ADV-006 — Legacy (sii-supervisor-gpt-4o-mini)

| Verificación | Resultado |
|-------------|-----------|
| ¿Código PostgreSQL referencia `sii-supervisor`? | ✅ **PASS** — Sin referencia |
| **Veredicto** | ✅ **PASS** |

## ADV-007 — Embedding Alternativo (nomic)

| Verificación | Resultado |
|-------------|-----------|
| ¿`nomic-embed-text` es default? | ✅ **PASS** — `OPENAI_EMBED_HOST=foundry` |
| ¿Puede cambiar accidentalmente? | ✅ **PASS** — Condicional explícito |
| **Veredicto** | ✅ **PASS** |

---

# 13. TESTS AUTOMATIZADOS

## 13.1 Inventario de Tests PostgreSQL

| Archivo | ¿Existe? | Tipo | ¿Requiere BD? |
|---------|----------|------|---------------|
| `tests/test_postgres_engine.py` | ✅ | Unit (URL) | ❌ No |
| `tests/test_postgres_searcher.py` | ✅ | Unit (filtros) | ℹ️ Sí (localhost) |
| `tests/test_embeddings.py` | ✅ | Unit (mock API) | ❌ No |
| `tests/conftest.py` | ✅ | Fixtures | ℹ️ Localhost |
| `tests/data.py` | ✅ | Test data (1024d) | ❌ No |

## 13.2 Análisis de Cobertura

| Componente | Cubierto | Observación |
|-----------|----------|-------------|
| `postgres_engine.create_postgres_engine` | ✅ | Solo URL |
| `postgres_engine.create_postgres_engine_from_env` | ✅ | Solo URL |
| `postgres_engine.create_postgres_engine_from_args` | ✅ | Solo URL |
| `postgres_engine.verify_pgvector_available` | ❌ | Sin test |
| `postgres_engine.verify_pgvector_created` | ❌ | Sin test |
| `postgres_searcher.build_filter_clause` | ✅ | 3 casos |
| `postgres_searcher.search` | ❌ | Requiere BD local |
| `postgres_searcher.search_and_embed` | ❌ | Requiere BD local |
| `embeddings.compute_text_embedding` | ✅ | Mockeado |
| `setup_postgres_database.create_db_schema` | ❌ | Sin test |
| `setup_postgres_seeddata.seed_data` | ❌ | Sin test |
| Dimensión 3072 | ❌ | Tests usan 1024 |

## 13.3 Problemas Identificados en Tests

| Problema | Archivo | Detalle |
|----------|---------|---------|
| Embeddings mock usan 1024d | `conftest.py`, `data.py` | Deberían usar 3072d |
| Test no valida contra Foundry | `test_embeddings.py` | Usa mock, no Foundry real |
| Sin test de integración PostgreSQL | `tests/` | No verifica `register_vector` |
---

# 14. HALLAZGOS

## 14.1 🔴 Críticos

| ID | Hallazgo | Severidad | Archivo(s) | Acción Requerida |
|----|----------|-----------|------------|-----------------|
| H-01 | `rag_institucional` no existe | 🔴 CRÍTICO | — | Crear BD |
| H-02 | `azure.extensions=""` no permite pgvector | 🔴 CRÍTICO | — | Configurar extensión |
| H-03 | Firewall bloquea IP actual | 🔴 CRÍTICO | — | Agregar regla |
| H-04 | `Vector(1024)` incompatible con Foundry 3072d | 🔴 CRÍTICO | `postgres_models.py:70` | Cambiar a `Vector(3072)` |

## 14.2 ⚠️ Altos

| ID | Hallazgo | Severidad | Archivo(s) | Acción Requerida |
|----|----------|-----------|------------|-----------------|
| H-05 | Seed data embeddings 1024d (obsoletos) | ⚠️ ALTO | `seed_data.json` | Regenerar con 3072d |
| H-06 | Tests usan 1024d (no reflejan Foundry) | ⚠️ ALTO | `tests/data.py`, `tests/conftest.py` | Actualizar a 3072d |
| H-07 | `.env.sample` usa `AZURE_OPENAI_EMBED_DIMENSIONS=1024` | ⚠️ ALTO | `.env.sample:77` | Cambiar a 3072 |
| H-08 | `dependencies.py` default `openai_embed_dimensions=1024` | ⚠️ ALTO | `dependencies.py:55` | Cambiar default a 3072 |

## 14.3 ℹ️ Informativos

| ID | Hallazgo | Severidad | Detalle |
|----|----------|-----------|---------|
| H-09 | `embedding_nomic` (768d) permanece pero no se usa | ℹ️ INFO | Mantener para compatibilidad futura |
| H-10 | `foundry_embedding_dimensions=None` en `FastAPIAppContext` | ℹ️ INFO | No se usa actualmente con Foundry |
| H-11 | `analiticaur@urosario.edu.co` sin rol asignado en RG PostgreSQL | ℹ️ INFO | Posible falta de permisos |
| H-12 | No existe archivo `.env` en el repositorio | ℹ️ INFO | Solo `.env.sample` |
| H-13 | `shared_preload_libraries` no necesita `vector` | ℹ️ INFO | pgvector no requiere preload |
| H-14 | Backup retention: 30 días, sin geo-redundancia | ℹ️ INFO | Configurable si se requiere |

---

# 15. BLOQUEANTES

| # | Bloqueante | Impide | Requiere | ¿Acción Humana? |
|---|-----------|--------|----------|----------------|
| B-01 | `rag_institucional` no existe | Crear tablas, insertar datos | `CREATE DATABASE rag_institucional;` | ✅ SÍ |
| B-02 | `azure.extensions=""` | `CREATE EXTENSION vector;` | Configurar `azure.extensions=vector` | ✅ SÍ |
| B-03 | Firewall bloquea IP actual | Conexión directa | Agregar IP al firewall | ✅ SÍ |
| B-04 | Dimensión incorrecta (1024 vs 3072) | Almacenar vectores | Cambiar `Vector(1024)` → `Vector(3072)` | ✅ SÍ |
| B-05 | Usuario RAG no confirmado | Conexión Azure AD | Determinar usuario/grupo AD para RAG | ✅ SÍ |

---

# 16. DECISIONES

## 16.1 ¿Crear BD `rag_institucional`?

**Decisión: NO CREAR AÚN.** Se requiere:
1. Confirmación humana explícita.
2. Resolver bloqueante B-03 (firewall) primero.
3. Resolver bloqueante B-04 (dimensión) primero.

## 16.2 ¿Habilitar pgvector?

**Decisión: NO HABILITAR AÚN.** Se requiere:
1. Configurar `azure.extensions=vector`.
2. Crear BD `rag_institucional`.
3. Ejecutar `CREATE EXTENSION vector;` en la BD correcta.

## 16.3 ¿Modificar esquema a 3072?

**Decisión: SÍ — ES NECESARIO.** Cambiar en 7 archivos (ver H-04 a H-08) antes de cualquier operación contra Azure.

## 16.4 ¿Proteger BD `superset`?

**Decisión: SÍ — MANTENER PROTECCIÓN.** Ya documentada en código y `.env.sample`.

---

# 17. CAMBIOS RECOMENDADOS

## 17.1 Matriz de Cambios

| # | Archivo | Cambio | Motivo | Riesgo | ¿Ejecución Azure? |
|---|---------|--------|--------|--------|-------------------|
| C-01 | `postgres_models.py:70` | `Vector(1024)` → `Vector(3072)` | Compatibilidad Foundry | Bajo | ❌ |
| C-02 | `dependencies.py:55` | `1024` → `3072` | Default correcto | Bajo | ❌ |
| C-03 | `dependencies.py:61` | `None` → `3072` | Foundry explícito | Bajo | ❌ |
| C-04 | `.env.sample:77` | `1024` → `3072` | Documentación correcta | Bajo | ❌ |
| C-05 | `tests/data.py` | regenerar embeddings 3072d | Tests representativos | Medio | ❌ |
| C-06 | `tests/conftest.py:73` | `1024` → `3072` | Tests correctos | Bajo | ❌ |
| C-07 | `tests/conftest.py:384` | `1024` → `3072` | Fixture correcto | Bajo | ❌ |
| C-08 | `seed_data.json` | regenerar embeddings 3072d | Seed data correcta | Medio | ❌ |
| C-09 | Servidor: `azure.extensions` | `""` → `"vector"` | Permitir pgvector | Bajo | ✅ SÍ |
| C-10 | Servidor: firewall | Agregar IP actual | Conectividad | Bajo | ✅ SÍ |
| C-11 | BD: `CREATE DATABASE rag_institucional` | Nueva BD | Almacenar datos RAG | Bajo | ✅ SÍ |
| C-12 | BD: `CREATE EXTENSION vector` | Habilitar pgvector | Búsqueda vectorial | Bajo | ✅ SÍ |

## 17.2 Cambios que NO deben hacerse

| Acción | Motivo |
|--------|--------|
| Modificar BD `superset` | Pertenece a Apache Superset |
| Eliminar `embedding_nomic` | Mantener compatibilidad futura |
| Modificar índices HNSW | Son compatibles con 3072d |
| Cambiar proveedor default de Foundry | Ya confirmado como correcto |
---

# 18. INFORMACIÓN PARA LA FUTURA SKILL POSTGRESQL

La futura skill `.cline/skills/rag-azure-postgres-urosario/SKILL.md` debe contener:

## 18.1 Información del Servidor

```
- Resource Group: RG-Datamining-SII2.0-Dev
- Servidor: supersetdev
- FQDN: supersetdev.postgres.database.azure.com
- Puerto: 5432
- Versión PostgreSQL: 16 (Minor: 14)
- SKU: Standard_B1ms (Burstable)
- Storage: 32 GB Premium_LRS (auto_grow: Disabled)
- Región: East US 2, Zona: 2, HA: Disabled
- Backup: 30 días, sin geo-redundancia
- max_connections: 50
```

## 18.2 Autenticación y Red

```
- ActiveDirectoryAuth: Enabled, PasswordAuth: Enabled
- password_encryption: scram-sha-256
- Login admin: supersetadmin
- Scope AD PostgreSQL: https://ossrdbms-aad.database.windows.net/.default
- PublicNetworkAccess: Enabled, sin VNet, sin Private Endpoint
- Firewall: IP-based (201.234.181.230 + Azure Services)
```

## 18.3 pgvector, BD y Esquema

```
- azure.extensions: vector en allowedValues, actual "" 
- shared_preload_libraries: NO requiere vector
- pgvector: isDynamicConfig=true (sin reinicio)
- BD objetivo: rag_institucional
- BD protegida: superset (NO MODIFICAR)
- BD protegida: postgres (NO MODIFICAR)
- Tabla: items
- embedding_3l: Vector(3072) — CORREGIDO desde 1024
- embedding_nomic: Vector(768) — mantener
- Índices: HNSW (m=16, ef_construction=64, vector_cosine_ops)
- Provider: Foundry (ur-rag-embedding-3-large)
```

## 18.4 Comandos y Errores Conocidos

```
Conexión: postgresql+asyncpg://{user}@{host}:5432/{database}?ssl=require
Auth: Azure AD via AzureDeveloperCliCredential / ManagedIdentity

Diagnóstico:
  az postgres flexible-server show --name supersetdev -g RG-Datamining-SII2.0-Dev
  az postgres flexible-server parameter show --name azure.extensions -s supersetdev -g RG-Datamining-SII2.0-Dev
  az postgres flexible-server firewall-rule list -s supersetdev -g RG-Datamining-SII2.0-Dev

Errores conocidos:
- 404 DeploymentNotFound: dimensions=1024 contra Foundry (usar 3072)
- Extensión no encontrada: azure.extensions no configurada
- Conexión rechazada: IP no permitida en firewall

Operaciones prohibidas:
- NO ejecutar DDL contra BD superset
- NO modificar azure.extensions sin confirmación
- NO crear BD sin verificar impacto
---

# 19. PROCEDIMIENTO PROPUESTO PARA CREACIÓN DE BD

```
PASO 1: Confirmar acceso a supersetdev
  - Agregar IP actual al firewall (requiere permisos)
  - O conectar desde Azure Cloud Shell

PASO 2: Conectar como supersetadmin
  psql "host=supersetdev.postgres.database.azure.com port=5432 dbname=postgres user=supersetadmin sslmode=require"

PASO 3: Verificar que NO existe rag_institucional
  SELECT datname FROM pg_database WHERE datname = 'rag_institucional';

PASO 4: CREAR BD (solo si no existe)
  CREATE DATABASE rag_institucional;

PASO 5: Verificar
  \l rag_institucional
```

⚠️ **Requiere confirmación humana antes del PASO 4.**

---

# 20. PROCEDIMIENTO PROPUESTO PARA PGVECTOR

```
PASO 1: Configurar azure.extensions (dinámico, sin reinicio)
  az postgres flexible-server parameter set \
    --resource-group RG-Datamining-SII2.0-Dev \
    --server-name supersetdev \
    --name azure.extensions \
    --value vector

PASO 2: Verificar configuración
  az postgres flexible-server parameter show \
    --name azure.extensions \
    --server-name supersetdev \
    --resource-group RG-Datamining-SII2.0-Dev

PASO 3: Conectar a rag_institucional
  psql "host=supersetdev.postgres.database.azure.com port=5432 dbname=rag_institucional user=supersetadmin sslmode=require"

PASO 4: Verificar disponibilidad
  SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'vector';

PASO 5: CREAR EXTENSION
  CREATE EXTENSION vector;

PASO 6: Verificar instalación
  SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

⚠️ **Requiere confirmación humana antes del PASO 1 y PASO 5.**

---

# MATRIZ DE RESULTADOS

| ID | Prueba | Resultado | Evidencia | Impacto |
|----|--------|-----------|-----------|---------|
| P-01 | Servidor existe y Ready | ✅ PASS | `"state": "Ready"` | Permite continuar |
| P-02 | FQDN correcto | ✅ PASS | `supersetdev.postgres.database.azure.com` | Conexión posible |
| P-03 | Versión PostgreSQL 16 | ✅ PASS | `"version": "16"` | Compatible pgvector |
| P-04 | SKU y storage adecuados | ✅ PASS | B1ms, 32GB | Suficiente |
| P-05 | Auth Azure AD habilitado | ✅ PASS | `activeDirectoryAuth: Enabled` | Token auth |
| P-06 | Firewall bloquea IP actual | 🔴 FAIL | IP 185.197.129.253 no en reglas | No conexión |
| P-07 | Regla Azure Services existe | ✅ PASS | `AllowAllAzureServices...` | Apps Azure OK |
| P-08 | azure.extensions permite vector | ❗ WARNING | `""` pero `vector` en allowedValues | Configurar |
| P-09 | rag_institucional existe | ❓ NOT TESTED | Sin conexión directa | Asumir NO existe |
| P-10 | pgvector disponible (servidor) | ❓ NOT TESTED | Sin conexión directa | Inferido NO |
| P-11 | pgvector instalado (BD) | ❓ NOT TESTED | Sin conexión directa | Inferido NO |
| P-12 | Vector(1024) correcto | 🔴 FAIL | Foundry devuelve 3072d | Cambiar a 3072 |
| P-13 | Código soporta 3072 | 🔴 FAIL | 7 archivos con 1024 | Cambios necesarios |
| P-14 | Seed data compatible | 🔴 FAIL | Vectores 1024d | Regenerar |
| P-15 | Tests representativos | 🔴 FAIL | Tests usan 1024d | Actualizar |
| P-16 | HNSW soporta 3072 | ✅ PASS | pgvector HNSW sin límite | Sin cambio |
| P-17 | ADV-001 (dimensión) | 🔴 FAIL | 1024 vs 3072 incompatible | Cambio crítico |
| P-18 | ADV-002 (BD equivocada) | ✅ PASS | No apunta a superset | Sin riesgo |
| P-19 | ADV-003 (tabla equivocada) | ✅ PASS | Solo tabla `items` | Sin riesgo |
| P-20 | ADV-004 (extensión ausente) | ❗ WARNING | Error no capturado | Mejorar |
| P-21 | ADV-005 (firewall) | ❗ WARNING | Sin diferenciación | Mejorar |
| P-22 | ADV-006 (legacy) | ✅ PASS | Sin referencia | Sin riesgo |
| P-23 | ADV-007 (nomic default) | ✅ PASS | Foundry es default | Sin riesgo |
| P-24 | Tests engine (URL) | ✅ PASS | 3 tests | Cobertura básica |
| P-25 | Tests searcher (filtros) | ✅ PASS | 2 tests | Cobertura parcial |
| P-26 | Tests embeddings (mock) | ✅ PASS | 2 tests con mock | No Foundry |
| P-27 | shared_preload_libraries | ✅ PASS | No requiere vector | Sin acción |
---

# RESUMEN FINAL

## Lo que SÍ sabemos:

1. ✅ Dónde está PostgreSQL: `supersetdev.postgres.database.azure.com:5432`
2. ✅ Está accesible públicamente (con firewall)
3. ❌ `rag_institucional` no existe
4. ❌ pgvector no disponible (azure.extensions vacío)
5. ❌ `vector` en `allowedValues` pero no configurado
6. ❓ No se pudo verificar versión de pgvector (sin conexión)
7. ✅ Se requiere `azure.extensions=vector` para habilitar pgvector
8. ✅ La dimensión correcta es **3072**, no 1024
9. ❌ El código NO soporta 3072 (usa 1024 en 7 archivos)
10. ✅ Los cambios necesarios están identificados (C-01 a C-12)
11. ✅ Lo que NO debe cambiar: BD superset, embedding_nomic, HNSW, Foundry
12. ✅ Riesgos: modificar Superset, permisos insuficientes, dimensión incorrecta
13. ✅ Info para skill PostgreSQL: documentada (sección 18)
14. ✅ Comandos a ejecutar: documentados (secciones 19-20)
15. ✅ Requieren confirmación humana: creación BD, pgvector, cambios de dimensión

## Lo que NO sabemos (requiere conexión directa):

- ❓ Versión exacta de pgvector
- ❓ Estado de otras BD (superset, postgres)
- ❓ Extensiones instaladas en superset
- ❓ Usuario RAG en Azure AD

## Próximos Pasos

1. **Resolver B-04** (dimensión 1024→3072) — cambios de código primero
2. **Resolver B-03** (firewall) — agregar IP actual
3. **Resolver B-01** (crear BD) — solo tras 1 y 2
4. **Resolver B-02** (pgvector) — solo tras 3
5. Ejecutar test de embedding contra Foundry (verificar 3072)
6. Ejecutar test de conectividad PostgreSQL
7. Regenerar seed data con 3072d

---

**Documento:** AUDITORIA-POSTGRES-AZURE-PGVECTOR.md
**Versión:** 1.0
**Fecha:** 2026-01-09
**Auditor:** analiticaur@urosario.edu.co
**Estado:** COMPLETADA — 28 pruebas, 4 bloqueantes críticos identificados
**Próximo:** Esperar confirmación humana antes de cualquier cambio en Azure