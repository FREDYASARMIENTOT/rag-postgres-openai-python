"""
Tests unitarios para modelos_institucionales.py.

Valida:
    1. Creación y estructura de Documento.
    2. Creación y estructura de FragmentoDocumento.
    3. Relación Documento -> FragmentoDocumento.
    4. Vector(1536) en FragmentoDocumento.
    5. Índices HNSW definidos correctamente.
"""

from __future__ import annotations

import pytest

from fastapi_app.modelos_institucionales import (
    Documento,
    FragmentoDocumento,
    indice_hnsw_fragmentos,
    indice_documento_orden,
)


class TestDocumentoModel:
    """Pruebas del modelo Documento."""

    def test_tabla_documentos_tiene_nombre_correcto(self):
        """La tabla debe llamarse 'documentos'."""
        assert Documento.__tablename__ == "documentos"

    def test_documento_tiene_columnas_esperadas(self):
        """Verifica columnas mínimas del modelo."""
        columnas = {c.name for c in Documento.__table__.columns}
        esperadas = {"id", "titulo", "contenido", "fuente", "tipo_documento",
                      "estado", "metadatos", "created_at", "updated_at"}
        assert esperadas.issubset(columnas), f"Faltan: {esperadas - columnas}"

    def test_documento_id_es_primary_key(self):
        """id debe ser PK autoincremental."""
        col_id = Documento.__table__.columns["id"]
        assert col_id.primary_key
        assert col_id.autoincrement is True

    def test_documento_titulo_tiene_indice(self):
        """titulo debe tener índice para búsqueda textual."""
        col_titulo = Documento.__table__.columns["titulo"]
        assert col_titulo.index is True

    def test_documento_tipo_documento_tiene_indice(self):
        """tipo_documento debe tener índice para filtrado."""
        col_tipo = Documento.__table__.columns["tipo_documento"]
        assert col_tipo.index is True

    def test_documento_repr(self):
        """__repr__ debe incluir id y titulo."""
        doc = Documento(id=1, titulo="Test", contenido="X", fuente="F", tipo_documento="G")
        repr_str = repr(doc)
        assert "Documento" in repr_str
        assert "id=1" in repr_str
        assert "Test" in repr_str


class TestFragmentoDocumentoModel:
    """Pruebas del modelo FragmentoDocumento."""

    def test_tabla_fragmentos_tiene_nombre_correcto(self):
        """La tabla debe llamarse 'fragmentos_documento'."""
        assert FragmentoDocumento.__tablename__ == "fragmentos_documento"

    def test_fragmento_tiene_columnas_esperadas(self):
        """Verifica columnas mínimas del modelo."""
        columnas = {c.name for c in FragmentoDocumento.__table__.columns}
        esperadas = {"id", "documento_id", "orden", "contenido", "embedding", "created_at"}
        assert esperadas.issubset(columnas), f"Faltan: {esperadas - columnas}"

    def test_embedding_es_vector_1536(self):
        """embedding debe ser Vector(1536)."""
        col_embedding = FragmentoDocumento.__table__.columns["embedding"]
        assert col_embedding.type is not None
        # Verificar que es tipo Vector comprobando el nombre
        type_str = str(col_embedding.type)
        assert "VECTOR" in type_str.upper() or "Vector" in type_str
        assert "1536" in type_str

    def test_documento_id_es_foreign_key(self):
        """documento_id debe ser FK a documentos.id."""
        col_fk = FragmentoDocumento.__table__.columns["documento_id"]
        # Verificar que tiene foreign keys
        assert len(col_fk.foreign_keys) > 0

    def test_fragmento_embedding_puede_ser_nulo(self):
        """embedding debe ser nullable (pendiente de indexación)."""
        col_embedding = FragmentoDocumento.__table__.columns["embedding"]
        assert col_embedding.nullable is True

    def test_fragmento_repr(self):
        """__repr__ debe incluir id y documento_id."""
        frag = FragmentoDocumento(id=1, documento_id=5, contenido="X")
        repr_str = repr(frag)
        assert "FragmentoDocumento" in repr_str
        assert "id=1" in repr_str
        assert "documento_id=5" in repr_str


class TestIndicesVectoriales:
    """Pruebas de los índices HNSW."""

    def test_indice_hnsw_existe(self):
        """Debe existir el índice HNSW para búsqueda por similitud."""
        assert indice_hnsw_fragmentos is not None
        assert "hnsw" in str(indice_hnsw_fragmentos).lower()

    def test_indice_hnsw_usa_vector_cosine_ops(self):
        """El índice debe usar vector_cosine_ops."""
        ops = indice_hnsw_fragmentos.kwargs.get("postgresql_ops", {})
        assert "embedding" in ops
        assert "vector_cosine_ops" in ops["embedding"]

    def test_indice_documento_orden_existe(self):
        """Debe existir el índice compuesto documento_id + orden."""
        assert indice_documento_orden is not None


class TestRelacionDocumentoFragmento:
    """Pruebas de la relación entre Documento y FragmentoDocumento."""

    def test_documento_tiene_relacion_fragmentos(self):
        """Documento debe tener atributo 'fragmentos' como relación."""
        assert hasattr(Documento, "fragmentos")

    def test_fragmento_tiene_relacion_documento(self):
        """FragmentoDocumento debe tener atributo 'documento' como relación."""
        assert hasattr(FragmentoDocumento, "documento")