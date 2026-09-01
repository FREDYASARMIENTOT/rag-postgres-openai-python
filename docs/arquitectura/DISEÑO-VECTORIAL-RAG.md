# Diseño Vectorial del RAG — Embeddings y pgvector

**Documento:** DISEÑO-VECTORIAL-RAG.md  
**Versión:** 1.0 — Fase Foundry  
**Fecha:** 2026-01-09  
**Status:** ✅ DOCUMENTADO — Pendiente de validación

---

## 1. Objetivo

Documentar el diseño de la capa vectorial del RAG Institucional:

- Modelos de embeddings soportados.
- Dimensiones y configuración.
- Almacenamiento en pgvector.
- Contrato de ProveedorEmbeddings.

---

## 2. Modelos de Embeddings Soportados

### 2.1 text-embedding-3-large (SELECCIONADO)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Foundry (Modelo-IA-UR) |
| Dimensiones | 256, 512, 1024, 3072 (configurable vía `dimensions`) |
| Dimensión elegida | **1024** |
| Costo | Medio ($0.13/1K tokens) |
| Multilingüe | ✅ Sí |
| Deployment | `ur-rag-embedding-3-large` |
| Estado | ✅ CREADO por `deploy-foundry-rag-institucional.ps1` |

### 2.2 text-embedding-3-small (Alternativa)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI / Foundry |
| Dimensiones | 512, 256, 1536 (configurable vía `dimensions`) |
| Costo | Bajo ($0.02/1K tokens) |
| Multilingüe | ✅ Sí |
| Uso | Si el benchmark revela que 1024d es excesivo |

### 2.3 text-embedding-ada-002 (Legacy)

| Atributo | Valor |
|----------|-------|
| Proveedor | OpenAI / Azure OpenAI |
| Dimensiones | 1536 (fijas, no configurables) |
| Costo | Medio |
| Recomendación | ❌ No recomendado (deprecado) |

### 2.4 nomic-embed-text (Open-Source)

| Atributo | Valor |
|----------|-------|
| Proveedor | Nomic / self-hosted |
| Dimensiones | 768 (fijas) |
| Costo | 0 (self-hosted) |
| Recomendación | Alternativa offline |

---

## 3. Decisión de Dimensiones

| Modelo | Dimensión | Razón |
|--------|-----------|-------|
| text-embedding-3-large (SELECCIONADO) | **1024** | Balance calidad/rendimiento (ver DECISION-EMBEDDINGS.md) |
| text-embedding-3-small (Alternativa) | 1536 | Dimensión completa del modelo |

**La dimensión es CONFIGURABLE** via variable de entorno:

```bash
# Para Foundry (default actual)
FOUNDRY_EMBEDDING_DIMENSIONS=1024

# Para Azure OpenAI (legacy)
AZURE_OPENAI_EMBED_DIMENSIONS=1024
```

⚠️ La dimensión definitiva debe validarse con el corpus institucional real
antes de fijarla. Ver `docs/decisiones/DECISION-EMBEDDINGS.md`.

---

## 4. Contrato de Embeddings

```python
class ProveedorEmbeddings(ABC):
    @property
    def cliente(self) -> AsyncOpenAI:
        """Cliente OpenAI asíncrono."""
    @property
    def modelo(self) -> str:
        """Nombre del modelo (ej: text-embedding-3-large)."""
    @property
    def deployment(self) -> Optional[str]:
        """Nombre del deployment o None."""
    @property
    def dimensiones(self) -> Optional[int]:
        """Dimensiones del vector o None si no soporta."""
```

### 4.1 Modelos que Soportan `dimensions`

```python
MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES = frozenset({
    "text-embedding-3-small",
    "text-embedding-3-large",
})
```

---

## 5. Almacenamiento en pgvector

### 5.1 Columnas Vectoriales

| Columna | Dimensión | Modelo |
|---------|-----------|--------|
| `embedding_3l` | 1024 (configurable) | text-embedding-3-large (SELECCIONADO) |
| `embedding_nomic` | 768 | nomic-embed-text |

### 5.2 Dependencia entre Dimensión y Performance

| Dimensión | Tamaño/vector | Performance relativa |
|-----------|--------------|---------------------|
| 768 | 3 KB | Referencia |
| 1024 | 4 KB | ~10% más lento |
| 1536 | 6 KB | ~25% más lento |
| 3072 | 12 KB | ~60% más lento |

### 5.3 Índice Recomendado

```sql
CREATE INDEX IF NOT EXISTS idx_items_embedding_3l_hnsw
ON items USING hnsw (embedding_3l vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

---

## 6. Flujo de Embedding

```python
texto → compute_text_embedding(
    texto_consulta,
    cliente_openai,         # del ProveedorEmbeddings
    modelo_embedding,       # del ProveedorEmbeddings
    deployment_embedding,   # del ProveedorEmbeddings
    dimensiones_embedding,  # del ProveedorEmbeddings
) → list[float] (vector)
```

---

## 7. Estado de Implementación

1. ✅ Deployment `ur-rag-embedding-3-large` creado — Succeeded (2026-01-09).
2. ✅ Endpoint Foundry confirmado: `https://modelo-ia-ur.cognitiveservices.azure.com/`
3. ⏳ Validar dimensión 1024 vs alternativas con corpus real (pendiente).
4. ⏳ Ejecutar benchmark de recall@10 con queries típicas (pendiente).
5. ⏳ Medir latencia real en supersetdev con pgvector (pendiente).

---

## 8. Referencias

- [Decisión de Embeddings](../decisiones/DECISION-EMBEDDINGS.md)
- [Integración Foundry](FOUNDRY-INTEGRATION.md)
- [Arquitectura del RAG](ARCHITECTURA-RAG.md)
- Código: `src/backend/fastapi_app/embeddings.py`
- Código: `src/backend/fastapi_app/proveedores.py`

---

**Documento:** DISEÑO-VECTORIAL-RAG.md  
**Versión:** 1.0 | **Fecha:** 2026-01-09 | **Status:** ✅ DOCUMENTADO