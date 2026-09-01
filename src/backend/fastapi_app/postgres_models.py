from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# =============================================================================
# MODELO DE DATOS PARA EL RAG INSTITUCIONAL
# =============================================================================
# Este archivo define el modelo SQLAlchemy para la tabla `items`,
# que almacena tanto los datos de los documentos como sus vectores de embedding.
#
# ARQUITECTURA OBJETIVO:
#   supersetdev (PostgreSQL Flexible Server, East US 2, PG16)
#     ├── superset      <- BD existente de Apache Superset (INTOCABLE)
#     └── rag_institucional  <- BD del RAG (CREAR)
#           └── items   <- Tabla con datos + vectores
#
# DEPENDENCIA: pgvector
#   La extensión `vector` debe estar habilitada en PostgreSQL antes
#   de que esta tabla pueda ser creada o consultada.
#   Estado actual de supersetdev: azure.extensions = "" (NO habilitado).
#   Ver docs/ARCHITECTURA-RAG.md para procedimiento de habilitación.
# =============================================================================


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos SQLAlchemy del proyecto.

    Todos los modelos de base de datos deben heredar de esta clase
    para garantizar la consistencia del registro declarativo.
    """
    pass


class Item(Base):
    """Modelo principal que representa un documento indexado en el RAG Institucional.

    Cada fila contiene:
    - Metadatos del documento (type, brand, name, description, price).
    - Vectores de embedding para búsqueda por similitud semántica.

    Columnas vectoriales:
    - `embedding_3l`: Vector de 1024 dimensiones para text-embedding-3-large.
    - `embedding_nomic`: Vector de 768 dimensiones para nomic-embed-text.

    Nota: Ambas columnas son opcionales (nullable=True). Solo se puebla
    la columna correspondiente al modelo de embeddings configurado
    (definido por AZURE_OPENAI_EMBEDDING_COLUMN en la configuración).

    Restricciones:
    - Requiere la extensión pgvector habilitada en PostgreSQL.
    - Los índices HNSW se definen abajo (fuera de la clase).
    """
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column()
    brand: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()
    # =========================================================================
    # Columnas de embedding (vectores)
    # =========================================================================
    # Solo una de estas dos columnas será utilizada en tiempo de ejecución,
    # dependiendo del valor de AZURE_OPENAI_EMBEDDING_COLUMN en la configuración.
    # La otra columna permanecerá NULL en todas las filas.
    # =========================================================================
    embedding_3l: Mapped[Vector] = mapped_column(Vector(1024), nullable=True)
    """Vector de 1024 dimensiones para text-embedding-3-large (Azure OpenAI)."""

    embedding_nomic: Mapped[Vector] = mapped_column(Vector(768), nullable=True)
    """Vector de 768 dimensiones para nomic-embed-text (Ollama local)."""

    def to_dict(self, include_embedding: bool = False):
        """
        Convierte el modelo a diccionario, excluyendo vectores por defecto.

        Args:
            include_embedding: Si True, incluye las columnas vectoriales
                              en el resultado. Por defecto False para evitar
                              exponer vectores grandes en respuestas API.

        Returns:
            Diccionario con columnas del modelo.

        Seguridad:
            Por defecto no se incluyen embeddings en la respuesta para
            evitar exposición innecesaria de representaciones vectoriales.
        """
        model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if include_embedding:
            model_dict["embedding_3l"] = model_dict.get("embedding_3l", [])
            model_dict["embedding_nomic"] = model_dict.get("embedding_nomic", [])
        else:
            del model_dict["embedding_3l"]
            del model_dict["embedding_nomic"]
        return model_dict

    def to_str_for_rag(self):
        """
        Representación textual del ítem para incluir en el contexto del LLM.

        Este formato es el que recibe el modelo de lenguaje como parte
        del prompt de generación de respuesta (contexto RAG).
        """
        return f"Name:{self.name} Description:{self.description} Price:{self.price} Brand:{self.brand} Type:{self.type}"

    def to_str_for_embedding(self):
        """
        Representación textual del ítem para generar su embedding.

        NOTA: Este método se usa para crear embeddings de los documentos
        durante la indexación. Incluye solo los campos que contribuyen
        a la representación semántica del documento.
        """
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


# =============================================================================
# ÍNDICES VECTORIALES HNSW
# =============================================================================
# Se definen índices HNSW (Hierarchical Navigable Small World) para cada
# columna vectorial. HNSW es un algoritmo de indexación aproximada que
# ofrece buena precisión con latencia de búsqueda baja.
#
# Operador: vector_cosine_ops (distancia coseno)
#   Funciona tanto para embeddings normalizados como no normalizados.
#   Si los embeddings están normalizados (unitarios), puede reemplazarse
#   por inner product (vector_ip_ops) para mejor rendimiento.
#
# Parámetros HNSW:
#   m = 16: Número de conexiones bidireccionales por nodo.
#           Valores típicos: 12-64. Mayor valor = más precisión, más memoria.
#   ef_construction = 64: Tamaño de la lista de candidatos durante construcción.
#           Valores típicos: 64-512. Mayor valor = mejor recall, más tiempo de
#           construcción.
# =============================================================================

table_name = Item.__tablename__

index_3l = Index(
    f"hnsw_index_for_cosine_{table_name}_embedding_3l",
    Item.embedding_3l,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding_3l": "vector_cosine_ops"},
)

index_nomic = Index(
    f"hnsw_index_for_cosine_{table_name}_embedding_nomic",
    Item.embedding_nomic,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding_nomic": "vector_cosine_ops"},
)
