"""
Configuración del RAG Institucional — Universidad del Rosario.

Propósito:
    Centraliza toda la configuración específica del RAG Institucional,
    separándola de la configuración del RAG de productos existente.

Contexto arquitectónico:
    El RAG Institucional coexiste con el RAG de productos (items).
    Ambos comparten PostgreSQL, pero usan tablas, modelos de embedding
    y configuraciones independientes.

    RAG Productos: text-embedding-3-large, 1024d, columna embedding_3l
    RAG Institucional: text-embedding-3-large, 3072d, columna embedding propia

Dependencias:
    - Variables de entorno definidas en .env.sample (RAG_EMBEDDING_*)
    - Ninguna dependencia de infraestructura externa

Seguridad:
    - NO expone contraseñas, API keys ni tokens
    - Los valores secretos deben venir de .env (excluido de Git) o Azure Key Vault
    - En producción, usar Managed Identity en lugar de claves

Restricciones:
    - Las dimensiones de embedding deben coincidir con el modelo de datos
      (Vector(3072) en fragmentos_documento.embedding)
    - Cambiar las dimensiones requiere migración de base de datos
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("ragapp")


# =============================================================================
# CONSTANTES DEL MODELO DE DATOS
# =============================================================================
# Estas constantes reflejan la estructura física de las tablas PostgreSQL.
# NO deben cambiar sin migración de base de datos.
# =============================================================================

DIMENSION_EMBEDDING_INSTITUCIONAL: int = 3072
"""Dimensión del vector de embedding en la tabla fragmentos_documento.

text-embedding-3-large genera 3072 dimensiones completas.
Foundry no soporta el parámetro `dimensions`, por lo que se usa la
dimensión completa del modelo (3072). Esta constante debe coincidir
con Vector(3072) en modelos_institucionales.py.
"""

NOMBRE_COLUMNA_EMBEDDING: str = "embedding"
"""Nombre de la columna vectorial en la tabla fragmentos_documento."""

TABLA_DOCUMENTOS: str = "documentos"
"""Nombre de la tabla de documentos institucionales."""

TABLA_FRAGMENTOS: str = "fragmentos_documento"
"""Nombre de la tabla de fragmentos con embeddings."""


# =============================================================================
# CONFIGURACIÓN DEL RAG INSTITUCIONAL
# =============================================================================


@dataclass
class ConfiguracionRAGInstitucional:
    """Configuración del RAG Institucional — constantes de modelo de datos y chunking.

    Esta clase se mantiene para uso del FragmentadorDocumentos y como
    referencia de constantes físicas de base de datos. La configuración
    de modelos (LLM, embeddings) se centraliza en FastAPIAppContext.

    Args:
        tamano_fragmento_maximo: Máximo de caracteres por fragmento.
        solapamiento_fragmentos: Solapamiento entre fragmentos.

    Attributes del modelo de datos (constantes):
        embed_dimensions: 1536 (text-embedding-3-small).
        embedding_column: Nombre de columna vectorial.
        tabla_documentos: Nombre de tabla documentos.
        tabla_fragmentos: Nombre de tabla fragmentos.
    """

    # Chunking
    tamano_fragmento_maximo: int = 1000
    """Máximo de caracteres por fragmento de documento."""
    solapamiento_fragmentos: int = 100
    """Solapamiento entre fragmentos consecutivos en caracteres."""

    # Constantes del modelo de datos (no configurables)
    embed_dimensions: int = DIMENSION_EMBEDDING_INSTITUCIONAL
    embedding_column: str = NOMBRE_COLUMNA_EMBEDDING
    tabla_documentos: str = TABLA_DOCUMENTOS
    tabla_fragmentos: str = TABLA_FRAGMENTOS


def cargar_configuracion_institucional() -> ConfiguracionRAGInstitucional:
    """Carga la configuración del RAG Institucional desde variables de entorno.

    Lee exclusivamente las variables de chunking: RAG_CHUNK_SIZE y
    RAG_CHUNK_OVERLAP. El resto de la configuración (modelos, deployments)
    se obtiene desde FastAPIAppContext via common_parameters().

    Returns:
        ConfiguracionRAGInstitucional con valores del entorno o defaults.
    """
    return ConfiguracionRAGInstitucional(
        tamano_fragmento_maximo=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
        solapamiento_fragmentos=int(os.getenv("RAG_CHUNK_OVERLAP", "100")),
    )