"""
Modelos del schema rag — Clasificacion (documentos_temas, fragmentos)
FASE F: Universidad del Rosario
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fastapi_app.modelos_rag_documentos import Documento
    from fastapi_app.modelos_rag_catalogo import Tema

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_app.postgres_models import Base


class DocumentoTema(Base):
    __tablename__ = "documentos_temas"
    __table_args__ = (
        UniqueConstraint("id_documento", "id_tema", name="uq_documento_tema"),
        {"schema": "rag"},
    )

    id_documento_tema: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_documento: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="RESTRICT"), nullable=False
    )
    id_tema: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.temas.id_tema", ondelete="RESTRICT"), nullable=False
    )
    es_tema_principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confianza_clasificacion: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    clasificacion_confirmada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usuario_confirmacion: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_confirmacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_confirmacion: Mapped[Optional[datetime.time]] = mapped_column(Time)

    documento: Mapped["Documento"] = relationship("Documento", back_populates="documentos_temas")
    tema: Mapped["Tema"] = relationship("Tema", back_populates="documentos_temas")


class FragmentoDocumento(Base):
    __tablename__ = "fragmentos_documento"
    __table_args__ = (
        CheckConstraint("numero_orden >= 1", name="ck_numero_orden"),
        {"schema": "rag"},
    )

    id_fragmento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_documento: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="RESTRICT"), nullable=False
    )
    numero_orden: Mapped[int] = mapped_column(Integer, nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad_caracteres: Mapped[Optional[int]] = mapped_column(Integer)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(3072), nullable=True)
    fecha_creacion: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_creacion: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    fecha_actualizacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_actualizacion: Mapped[Optional[datetime.time]] = mapped_column(Time)

    documento: Mapped["Documento"] = relationship("Documento", back_populates="fragmentos")