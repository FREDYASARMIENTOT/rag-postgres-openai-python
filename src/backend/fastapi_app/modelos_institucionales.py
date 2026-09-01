"""
Modelo de datos para el RAG Institucional — Universidad del Rosario.

Propósito:
    Define las tablas `documentos` y `fragmentos_documento` que almacenan
    el conocimiento institucional indexado para búsqueda semántica.

Contexto arquitectónico:
    Este modelo es EXCLUSIVO del RAG Institucional. No interfiere con la
    tabla `items` del RAG de productos existente.

    La separación es deliberada:
    - `items`: RAG de productos (Vector 1024 / 768)
    - `documentos` + `fragmentos_documento`: RAG Institucional (Vector 1536)

    ARQUITECTURA:
        supersetdev (PostgreSQL Flexible Server)
          ├── superset              <- BD de Superset (INTOCABLE)
          └── rag_institucional     <- BD del RAG
                ├── documentos              <- Metadatos de documentos
                └── fragmentos_documento    <- Fragmentos con embeddings

¿Por qué dos tablas?
    documentos (1) ──── (N) fragmentos_documento
    Un documento grande (ej: reglamento académico) se fragmenta para
    mejorar la precisión del retrieval. Cada fragmento tiene su embedding.

    1. Trazabilidad: cada fragmento sabe a qué documento pertenece.
    2. Retrieval preciso: se busca sobre fragmentos, no documentos completos.
    3. Fuente preservada: el agente recupera el documento original.
    4. Escalabilidad: documentos grandes no generan vectores desbalanceados.

Embeddings:
    Columna `embedding` en fragmentos_documento: Vector(1536).
    Generado por text-embedding-3-small.

Retrieval:
    1. Consulta en lenguaje natural → embedding (1536d).
    2. Búsqueda de similitud coseno sobre fragmentos_documento.
    3. Fragmentos relevantes + documento asociado (título, fuente, score).

Dependencias:
    - pgvector (extensión PostgreSQL)
    - SQLAlchemy 2.0+
    - fastapi_app.postgres_models.Base

Seguridad:
    - Embeddings no expuestos en respuestas por defecto.
    - metadata almacena JSON serializado (no permite ejecución).
    - Consultas SQL con SQLAlchemy ORM (no raw SQL).

Restricciones:
    - No usar para RAG de productos (usar `items`).
    - Vector(1536) debe coincidir con RAG_EMBEDDING_DIMENSIONS.
    - Requiere CREATE EXTENSION vector.
"""

from __future__ import annotations

import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_app.postgres_models import Base


# =============================================================================
# TABLA: documentos
# =============================================================================
# Almacena metadatos y contenido completo de cada documento indexado.
# - id: PK autoincremental.
# - titulo: Nombre del documento (visible para el agente).
# - contenido: Texto completo (para recuperación posterior).
# - fuente: Origen institucional (URL, dependencia, referencia).
# - tipo_documento: Clasificación (reglamento, resolucion, facultad).
# - fecha_publicacion: Fecha oficial del documento fuente.
# - fecha_actualizacion: Última actualización del documento fuente.
# - estado: activo, archivado, pendiente, error.
# - metadata: JSON con metadatos extendidos.
# - created_at/updated_at: Timestamps del sistema.
# =============================================================================


class Documento(Base):
    """
    Documento indexado en el RAG Institucional.

    Cada fila contiene un documento completo con metadatos.
    El contenido textual completo se almacena aquí; los fragmentos
    con embeddings se almacenan en fragmentos_documento.

    Relaciones:
        1 ──── N fragmentos_documento
    """

    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Identificador único del documento."""

    titulo: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    """Título del documento. Indexado para búsqueda textual."""

    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    """Contenido completo del documento en texto plano."""

    fuente: Mapped[str] = mapped_column(String(1000), nullable=False)
    """Origen institucional: URL, dependencia, o referencia documental."""

    tipo_documento: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    """Clasificación: facultad, reglamento, resolucion, etc."""

    fecha_publicacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    """Fecha oficial de publicación del documento fuente."""

    fecha_actualizacion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    """Fecha de última actualización del documento fuente."""

    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="activo")
    """Estado en el sistema: activo, archivado, pendiente, error."""

    metadatos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    """Metadatos extendidos en JSON: categorias, tags, etc."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    """Timestamp de ingesta al sistema. Asignado automáticamente."""

    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    """Timestamp de última modificación. Actualizado automáticamente."""

    fragmentos: Mapped[list["FragmentoDocumento"]] = relationship(
        "FragmentoDocumento",
        back_populates="documento",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    """Fragmentos del documento. Eliminación en cascada."""

    def __repr__(self) -> str:
        return f"<Documento id={self.id} titulo='{self.titulo[:50]}' tipo={self.tipo_documento}>"


# =============================================================================
# TABLA: fragmentos_documento
# =============================================================================
# Almacena fragmentos de documentos con vectores de embedding.
# Cada fragmento es una porción semánticamente coherente de un documento.
#
# - id: PK autoincremental.
# - documento_id: FK al documento padre (trazabilidad de fuente).
# - orden: Posición del fragmento dentro del documento.
# - contenido: Texto del fragmento (para respuesta del agente).
# - embedding: Vector de 1536 dimensiones (text-embedding-3-small).
# - metadata: JSON con información específica del fragmento.
# - created_at: Timestamp de creación.
# =============================================================================


class FragmentoDocumento(Base):
    """
    Fragmento de documento con embedding vectorial.

    Cada fila contiene una porción semántica de un documento y su
    representación vectorial (text-embedding-3-small, 1536d).

    La búsqueda semántica se realiza sobre el embedding usando
    distancia coseno (<=>). Los resultados incluyen datos del
    documento padre (título, fuente, tipo).

    Relaciones:
        N ──── 1 documentos. Cada fragmento pertenece a un documento.
    """

    __tablename__ = "fragmentos_documento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Identificador único del fragmento."""

    documento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """
    ID del documento padre.
    FK con ondelete=CASCADE: eliminar fragmento si se elimina el documento.
    """

    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Posición del fragmento dentro del documento."""

    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    """
    Texto del fragmento. Es la parte que se devuelve al agente como contexto.
    """

    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536), nullable=True)
    """
    Vector de embedding (1536 dimensiones). Generado por text-embedding-3-small.
    Puede ser NULL si el fragmento está pendiente de indexación.
    text-embedding-3-small genera vectores de hasta 1536 dimensiones.
    """

    metadatos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    """
    Metadatos del fragmento en JSON.
    Ej: {"seccion": "facultades", "palabras_clave": ["medicina"]}
    """

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    """Timestamp de creación del fragmento."""

    documento: Mapped["Documento"] = relationship(
        "Documento",
        back_populates="fragmentos",
    )
    """Referencia al documento padre (lazy loading)."""

    def __repr__(self) -> str:
        return (
            f"<FragmentoDocumento id={self.id} "
            f"documento_id={self.documento_id}>"
        )


# =============================================================================
# ÍNDICES VECTORIALES HNSW
# =============================================================================
# HNSW: búsqueda aproximada de vecinos más cercanos.
# Ventajas sobre IVFFlat: mayor velocidad, construcción incremental.
# Desventaja: mayor consumo de memoria.
#
# Parámetros:
#   m=16: Conexiones bidireccionales por nodo (12-64).
#   ef_construction=64: Tamaño de lista dinámica (64-512).
# Operador: vector_cosine_ops (distancia coseno).
# Requisito: pgvector 0.5.0+
# =============================================================================

indice_hnsw_fragmentos = Index(
    f"hnsw_cosine_fragmentos_documento_embedding",
    FragmentoDocumento.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
"""
Índice HNSW para búsqueda por similitud coseno.
Acelera: ORDER BY embedding <=> :query_vector LIMIT :top
Sin él: escaneo secuencial O(n).
"""

indice_documento_orden = Index(
    "ix_fragmentos_documento_documento_orden",
    FragmentoDocumento.documento_id,
    FragmentoDocumento.orden,
)
"""
Índice compuesto para recuperar fragmentos ordenados de un documento.
Útil para obtener_documento_rag.
"""