"""
Modelos legacy — public.documentos y public.fragmentos_documento.
NO MODIFICAR hasta aprobacion de migracion completa.
Mantenidos para compatibilidad durante Fase F.
"""

from __future__ import annotations

import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_app.postgres_models import Base


class DocumentoLegacy(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fuente: Mapped[str] = mapped_column(String(300), default="Sin fuente")
    tipo_documento: Mapped[str] = mapped_column(String(100), default="general")
    estado: Mapped[str] = mapped_column(String(30), default="activo")
    metadatos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_publicacion: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_actualizacion: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    fragmentos: Mapped[list["FragmentoDocumentoLegacy"]] = relationship(
        "FragmentoDocumentoLegacy", back_populates="documento",
        cascade="all, delete-orphan",
    )


class FragmentoDocumentoLegacy(Base):
    __tablename__ = "fragmentos_documento"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    documento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(3072), nullable=True)
    metadatos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    documento: Mapped["DocumentoLegacy"] = relationship(
        "DocumentoLegacy", back_populates="fragmentos",
    )